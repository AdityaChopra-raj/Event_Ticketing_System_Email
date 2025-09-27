import streamlit as st
from PIL import Image
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import pandas as pd
# IMPORT FIX: Centralized Blockchain and helpers
from blockchain import Blockchain, get_ticket_status
from events_data import events 

# ------------------------ CONFIGURATION & SECRETS ------------------------
# FALLBACK: Use try/except for st.secrets to allow local execution without TOML file
try:
    EMAIL_ADDRESS = st.secrets["email"]["address"]
    EMAIL_PASSWORD = st.secrets["email"]["password"]
    EMAIL_SECRET_LOADED = True
except KeyError:
    # Set safe, non-functional placeholders if secrets.toml is missing or misconfigured
    EMAIL_ADDRESS = "placeholder@example.com"
    EMAIL_PASSWORD = "app_password_placeholder"
    EMAIL_SECRET_LOADED = False
    
    # Updated: Specific warning about the required TOML structure/keys
    st.error("""
        ⚠️ **EMAIL FUNCTIONALITY DISABLED** (Required secrets are missing or keys are incorrect)
        
        The app failed to load the `[email]` secrets. Please verify that your 
        `.streamlit/secrets.toml` file has the following *exact* structure:
        
        ```toml
        [email]
        address = "your_sending_email@gmail.com"
        password = "your_generated_app_password" 
        ```
        
        Ensure you are using a Gmail **App Password** for security.
    """, icon="🚫")


def send_email(to_email, subject, body):
    """Sends confirmation emails."""
    
    # Do not attempt to send if secrets failed to load
    if not EMAIL_SECRET_LOADED:
        st.info(f"Email skipped: Confirmation for '{to_email}' not sent (Secrets not configured).")
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Use secure SMTP connection on port 465
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        st.toast("Email sent successfully!", icon='📧')
    except Exception as e:
        # Display a more helpful error message for email delivery issues
        st.error(f"Error sending email: Check network connection or ensure the App Password is correct and enabled. Error: {e}")


# ------------------------ APP STATE & INITIALIZATION ------------------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
if "mode" not in st.session_state:
    st.session_state.mode = None
# This cache stores the current ticket status calculated from the blockchain, including customer data.
if "purchased_tickets_cache" not in st.session_state:
    st.session_state.purchased_tickets_cache = {}


st.set_page_config(page_title="Event Ticket Portal", layout="wide")

# Get selected event or admin view from query params (URL)
event_selected = st.query_params.get("event")
admin_view = st.query_params.get("view") == "admin" # Admin view check

if event_selected and event_selected not in events:
    # Handle bad URL param by resetting
    st.query_params.clear()
    event_selected = None


# ------------------------ NETFLIX-THEME STYLING (Spacing Fixes Applied) ------------------------
st.markdown("""
<style>
/* Base Dark Theme & Font */
.stApp {
    background-color: #141414; /* Deep charcoal background */
    color: white;
    font-family: 'Inter', sans-serif;
}

/* ----------------------- FIX: ELIMINATE EMPTY SPACE AT TOP ----------------------- */
/* Target the main container and content wrapper to remove Streamlit's default padding */
.stApp {
    padding-top: 0px !important;
    margin-top: 0px !important;
}

/* Targets the main content block, which usually has a huge padding-top by default */
.block-container, header {
    padding-top: 0px !important;
    margin-top: 0px !important;
}

/* --------------------------------------------------------------------------------- */

/* *** SPACING FIX: AGGRESSIVE OVERRIDE *** */
h1 {
    text-align: center;
    color: #E50914; /* Netflix Red */
    font-size: 3em; 
    font-weight: 900;
    letter-spacing: 2px;
    margin-top: 5px !important;       /* Adjusted to 5px to give a slight margin from the absolute top */
    margin-bottom: -5px !important; 
    font-family: 'Avenir', 'Arial Black', sans-serif; 
}

/* ----------------------- CARD STYLES (UI/UX FOCUS) ----------------------- */

/* Visual content container for image in the main grid */
.event-image-container {
    padding: 10px; 
    position: relative;
    z-index: 5; 
    /* Softly enforce the 2:3 ratio */
    aspect-ratio: 2 / 3; 
    overflow: hidden; 
    /* Set a maximum width for consistency on large screens */
    max-width: 250px; 
    margin-left: auto; /* Center the image container within the column */
    margin-right: auto;
}

/* Image styling inside the container */
.event-image-container img {
    border-radius: 4px 4px 0 0; /* Match Netflix style */
    width: 100%;
    height: 100%;
    object-fit: cover; 
}


/* Event Title Card - Visual content container */
.event-card {
    border-radius: 8px;
    background: #222; 
    padding: 15px 5px; 
    margin-bottom: 30px; 
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    overflow: hidden;
    text-align: center; 
    transition: transform 0.3s ease-in-out, box-shadow 0.3s;
}

/* Link/Title styling */
.event-card a {
    text-decoration: none !important; 
    color: white !important; 
    font-weight: 700;
    display: block; 
}

/* Netflix Red Glow and Zoom on Hover */
.event-card:hover {
    transform: scale(1.05); 
    box-shadow: 0 8px 16px rgba(229, 9, 20, 0.6); 
    z-index: 6; 
    background: #333; 
}


/* --- Detail View Styles --- */
.detail-container {
    display: flex;
    gap: 30px;
    padding: 30px; 
    margin-bottom: 40px; 
    background-color: #1a1a1a; 
    border-radius: 10px;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.7);
}

.event-image-card {
    position: relative;
    border-radius: 8px;
    overflow: hidden;
    max-width: 300px; 
    height: auto;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.6);
    transition: transform 0.3s;
    /* Softly enforcing aspect ratio */
    aspect-ratio: 2 / 3;
}
.event-image-card img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.event-description-box {
    padding: 10px;
    color: #ccc;
    width: 100%; 
}
.event-description-box h2 {
    color: #E50914; 
    margin-top: 0;
    margin-bottom: 15px; 
    font-size: 2.5em;
}
.event-description-box p {
    font-size: 1.1em;
    line-height: 1.6;
    margin-bottom: 30px; 
    color: white;
}
.event-description-box .detail-item strong {
    color: #E50914; 
}

.event-stats {
    background-color: #333;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 30px; 
    text-align: center;
    border-left: 5px solid #E50914;
    transition: all 0.3s;
}

/* Standard Streamlit Button Styling (Red with black thin border) */
div.stButton > button {
    background-color: #E50914; 
    color: white;
    border: 1px solid black; 
    padding: 10px 20px;
    font-size: 1em;
    border-radius: 6px;
    margin-top: 15px; 
    cursor: pointer;
    transition: background-color 0.2s, transform 0.2s, box-shadow 0.2s;
    font-weight: bold;
}
div.stButton > button:hover {
    background-color: #f6121d; 
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(229, 9, 20, 0.6); 
}

.footer {position:fixed;bottom:10px;left:20px;font-size:16px;color:#E50914;}

/* NEW: Floating Button Styles */
.audit-button-container {
    position: fixed;
    bottom: 20px; /* Adjust vertical position */
    right: 20px; /* Adjust horizontal position */
    z-index: 1000; /* Ensure it floats above other content */
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5); /* Shadow for better visibility */
    border-radius: 8px;
    overflow: hidden; /* Contains the button shadow */
}

/* Target the Streamlit button element within the container */
.audit-button-container .stButton > button {
    background-color: #E50914 !important; /* Netflix Red */
    color: white !important;
    padding: 12px 20px !important;
    font-size: 1.1em !important;
    font-weight: bold !important;
    border: none !important;
    box-shadow: none !important;
    transition: background-color 0.2s, transform 0.2s;
}
.audit-button-container .stButton > button:hover {
    background-color: #f6121d !important;
    transform: translateY(-1px) !important;
}

</style>
""", unsafe_allow_html=True)

st.markdown("<h1>Event Ticket Portal</h1>", unsafe_allow_html=True)

# ------------------------ HELPER FUNCTIONS ------------------------
def capacity_info(event_name):
    """Fetches real-time status by reading the blockchain."""
    total_purchased, scanned, remaining, _, purchased_tickets_cache = get_ticket_status(st.session_state.blockchain, event_name)
    st.session_state.purchased_tickets_cache = purchased_tickets_cache 
    return remaining, scanned, total_purchased

def get_blockchain_stats():
    """Calculates counts for the PDF design footer."""
    blocks_count = len(st.session_state.blockchain.chain)
    purchase_count = 0
    check_in_count = 0
    for block in st.session_state.blockchain.chain:
        for txn in block["transactions"]:
            if txn.get("type") == "PURCHASE":
                purchase_count += 1
            elif txn.get("type") == "VERIFY":
                check_in_count += 1
    return blocks_count, purchase_count, check_in_count

# ------------------------ UI SCREENS ------------------------

def show_events():
    """
    Renders the main event selection screen.
    """
    st.session_state.mode = None
    
    # Use fluid columns for responsiveness
    cols = st.columns(len(events)) 
    for idx, (ename, edata) in enumerate(events.items()):
        # Create the navigation URL string for this event card
        nav_url = f'?event={ename}'
        
        with cols[idx]:
            # 1. Image Container (The top part of the card)
            st.markdown("<div class='event-image-container'>", unsafe_allow_html=True) 
            
            try:
                img = Image.open(edata["image"])
                # st.image renders the image component, which is then constrained by the CSS 
                st.image(img, use_container_width=True)
            except FileNotFoundError:
                 # Placeholder ensures missing images still respect the 2:3 ratio
                 st.image("https://placehold.co/300x450/E50914/FFFFFF?text=Image+Missing", use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True) 
            
            # 2. Clickable Title Card (The bottom part of the card, with hover effect)
            st.markdown(f"""
            <div class='event-card'>
                <a href="{nav_url}">
                    <h3 style='color:inherit; margin:0;'>{ename}</h3>
                </a>
            </div>
            """, unsafe_allow_html=True) 


def show_event_actions(event_name):
    """
    Renders event details, actions (Buy/Check-In), and statistics in a two-column (Netflix-style) layout.
    """
    
    # Get event data and status
    edata = events[event_name]
    remaining, scanned, _ = capacity_info(event_name)

    # Use columns for Netflix layout: Image on Left, Details/Actions on Right
    st.markdown("<div class='detail-container'>", unsafe_allow_html=True)
    
    # Set column widths: 1 for image, 2.5 for details
    col_image, col_details = st.columns([1, 2.5]) 

    with col_image:
        # Image Card (Left Side)
        st.markdown("<div class='event-image-card'>", unsafe_allow_html=True)
        try:
            img = Image.open(edata["image"])
            # use_container_width=True combined with the .event-image-card CSS ensures 2:3 ratio
            st.image(img, use_container_width=True)
        except FileNotFoundError:
            # Placeholder for detail view
            st.image("https://placehold.co/300x450/E50914/FFFFFF?text=Image+Missing", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_details:
        # Details and Actions (Right Side - Description/Stats/Buttons)
        st.markdown(f"<div class='event-description-box'>", unsafe_allow_html=True)
        st.markdown(f"<h2>{event_name}</h2>", unsafe_allow_html=True)
        
        # Display Time and Location
        st.markdown(f"<div class='detail-item'><strong>Time:</strong> {edata.get('time', 'N/A')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='detail-item'><strong>Location:</strong> {edata.get('location', 'N/A')}</div>", unsafe_allow_html=True)
        
        # Display Description
        st.markdown(f"<p>{edata['description']}</p>", unsafe_allow_html=True)
        
        # Display statistics
        st.markdown(f"""
        <div class='event-stats'>
            <div>Available Tickets: {remaining}</div>
            <div>No. of guests in venue: {scanned}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.mode is None:
            c1, c2, c3 = st.columns(3)
            with c1:
                # Back button now clears the event query param
                if st.button("⬅ Back to Events"):
                    st.query_params.clear()
                    st.rerun() 
            with c2:
                if st.button("Buy Ticket", key="action_buy"):
                    st.session_state.mode = "buy"
            with c3:
                if st.button("Check-In", key="action_verify"): 
                    st.session_state.mode = "verify"
        else:
            if st.button("⬅ Back to Actions"):
                st.session_state.mode = None
                st.rerun() 
            
            # Conditionally render Buy or Verify forms
            if st.session_state.mode == "buy":
                buy_tickets(event_name, remaining)
            elif st.session_state.mode == "verify":
                verify_tickets(event_name)
        
        st.markdown("</div>", unsafe_allow_html=True) # Close event-description-box
    
    st.markdown("</div>", unsafe_allow_html=True) # Close detail-container


def buy_tickets(event_name, remaining):
    """Renders the purchase form and adds an immutable PURCHASE transaction (Page 3 of PDF)."""
    st.subheader("Enter Your Details to Buy Ticket")
    
    # Matches PDF Design inputs: Name, Email, Phone Number, No. of Tickets
    with st.form(key='purchase_form'):
        name = st.text_input("Name", key="buy_name")
        email = st.text_input("Email", key="buy_email")
        phone_number = st.text_input("Phone Number", key="buy_phone") 
        qty = st.number_input("No. of Tickets (max 10)", min_value=1, max_value=10, value=1, key="buy_qty")
        
        submitted = st.form_submit_button("Confirm Purchase")

    if submitted:
        if not name or not email or not phone_number:
            st.error("Please fill in all details.")
            return

        if qty > remaining:
            st.error("Not enough remaining capacity")
            return
            
        ticket_id = str(uuid.uuid4())[:8].upper()
        
        # 1. Add immutable PURCHASE transaction to the ledger
        st.session_state.blockchain.add_transaction({
            "type": "PURCHASE", 
            "ticket_id": ticket_id, 
            "event": event_name, 
            "quantity": qty, 
            "holder": name,
            "email": email,
            "phone_number": phone_number,
            "timestamp": time.time()
        })
        
        # 2. Mine a new block
        st.session_state.blockchain.create_block(st.session_state.blockchain.last_block["hash"]) 
        
        st.success(f"Purchase Confirmed! Your Ticket ID is: **{ticket_id}**. Check your email.")
        
        # 3. Send email confirmation
        body = (f"Hello {name},\n\nYour purchase for {event_name} has been confirmed.\n"
                f"Total Tickets Purchased: {qty}\n"
                f"Your Ticket ID: {ticket_id}\n\n"
                f"Present this ID at the venue for check-in.\n\n"
                f"--- Confirmation Sent from Event Portal ---")
                
        send_email(email, f"{event_name} Ticket Confirmation", body)
        st.rerun() # Refresh to show new capacity


def verify_tickets(event_name):
    """Handles the in-app ticket verification (Check-In) logic."""
    st.subheader("Gate Attendant: Process Check-In")

    # Fetch the latest status for verification checks
    _, _, _, ticket_details, purchased_tickets_cache = get_ticket_status(st.session_state.blockchain, event_name)

    # Verification Form
    ticket_id = st.text_input("Enter Ticket ID").upper()
    email_input = st.text_input("Enter Customer Email", help="Required for double-checking customer identity.")
    num_entering = st.number_input("No. of People Entering", min_value=1, value=1, key="verify_num", help="How many people are entering using this ID?")

    if st.button("Process Check-In"):
        if not ticket_id or not email_input:
            st.warning("Please enter both Ticket ID and Customer Email.")
            return

        # 1. Get status and purchase info
        t_status = ticket_details.get(ticket_id)
        t_purchase_info = purchased_tickets_cache.get(ticket_id)
        
        # 2. Basic Validation
        if not t_status or not t_purchase_info:
            st.error("❌ Invalid Ticket ID for this event or ticket was not found.")
            return

        # 3. Email Security Check (using strip and lower for robustness)
        if t_purchase_info['email'].lower() != email_input.strip().lower(): 
            st.error("❌ Email address does not match the purchasing customer on record for this Ticket ID.")
            return

        # 4. Usage Validation
        total_tickets = t_status["qty"]
        scanned_tickets = t_status["scanned"]
        remaining_to_use = total_tickets - scanned_tickets
        
        if remaining_to_use <= 0:
            st.error("❌ Ticket has already been fully used.")
            return
            
        if num_entering > remaining_to_use:
            st.error(f"❌ Cannot check in {num_entering} guests. Only {remaining_to_use} tickets remain for this Ticket ID (Used: {scanned_tickets}/{total_tickets}).")
            return
            
        # 5. Process Check-in (Add VERIFY transaction and mine block)
        st.session_state.blockchain.add_transaction({
            "type": "VERIFY", 
            "ticket_id": ticket_id, 
            "event": event_name, 
            "num_entering": num_entering,
            "verifier": "Main Portal Check-In", 
            "timestamp": time.time()
        })
        st.session_state.blockchain.create_block(st.session_state.blockchain.last_block["hash"])
        
        # 6. Recalculate status and display success
        _, _, _, new_ticket_details, _ = get_ticket_status(st.session_state.blockchain, event_name)
        new_scanned_tickets = new_ticket_details[ticket_id]["scanned"]
        new_remaining = total_tickets - new_scanned_tickets
        
        st.balloons()
        st.success(f"✅ VERIFIED {num_entering} GUEST(S) for {t_purchase_info['name']}. Remaining: **{new_remaining}**")

        # 7. Send confirmation email
        email_body = (
            f"Hello {t_purchase_info['name']},\n\n"
            f"A check-in was successfully processed for your **{event_name}** ticket.\n\n"
            f"**Ticket ID:** {ticket_id}\n"
            f"**Guests Checked In Now:** {num_entering}\n"
            f"**Total Used Tickets:** {new_scanned_tickets} / {total_tickets}\n"
            f"**Tickets Remaining:** {new_remaining}\n\n"
            f"--- Check-In Confirmation from Event Portal ---"
        )
        send_email(
            t_purchase_info['email'], 
            f"Check-In Update: {event_name} - {num_entering} Guests Entered", 
            email_body
        )
        
        # 8. Refresh the app state to clear fields and update stats
        st.rerun()


def show_admin_audit():
    """
    Renders a detailed view of the entire blockchain ledger for auditing, 
    including a downloadable CSV of all transactions.
    
    FIXED: Now explicitly joins customer purchase data to VERIFY transactions for a complete view.
    """
    st.subheader("🔒 Blockchain Audit Ledger")
    st.markdown("---")

    blockchain_data = st.session_state.blockchain.chain
    all_txns_for_display = []
    
    # Back button to return to the main event list
    if st.button("⬅ Back to Events Dashboard"):
        st.query_params.clear()
        st.rerun()

    if not blockchain_data:
        st.info("The blockchain is currently empty (only the genesis block exists).")
        return
        
    # NEW: 1. Generate the customer purchase information map once (ticket_id -> customer details)
    # We use the helper function to calculate the full customer map across ALL blocks/events
    _, _, _, _, customer_info_map = get_ticket_status(st.session_state.blockchain, None)


    # ------------------ 2. Gather ALL Transactions for Report and Display ------------------
    for block in blockchain_data:
        block_index = block['index']
        block_hash = block['hash'] # The unique hash of this block (The Ledger Proof)
        block_prev_hash = block['previous_hash']
        
        for txn in block["transactions"]:
            txn_type = txn.get("type", "N/A")
            ticket_id = txn.get("ticket_id", "N/A")
            
            # Initialize common fields
            txn_data = {
                "Block Index": block_index,
                "Transaction Type": txn_type,
                "Time (Readable)": time.ctime(txn.get("timestamp", 0)),
                "Event Name": txn.get("event", "N/A"),
                "Ticket ID": ticket_id,
                "Quantity/Guests": 0, 
                "Customer Name": "N/A", 
                "Customer Email": "N/A", 
                "Phone Number": "N/A", 
                "Verifier": "N/A", 
                "Block Hash (Ledger Proof)": block_hash, 
                "Previous Block Hash": block_prev_hash,
                "Timestamp (Unix)": txn.get("timestamp", 0) 
            }

            if txn_type == "PURCHASE":
                # For a PURCHASE transaction, all customer data is directly on the transaction
                txn_data["Quantity/Guests"] = txn.get("quantity", 0)
                txn_data["Customer Name"] = txn.get("holder", "N/A")
                txn_data["Customer Email"] = txn.get("email", "N/A")
                txn_data["Phone Number"] = txn.get("phone_number", "N/A")

            elif txn_type == "VERIFY":
                # For a VERIFY transaction, pull check-in details and ENRICH with customer map
                txn_data["Quantity/Guests"] = txn.get("num_entering", 0)
                txn_data["Verifier"] = txn.get("verifier", "N/A")
                
                # Enrichment step: Look up customer details using the ticket_id
                customer_details = customer_info_map.get(ticket_id)
                if customer_details:
                    txn_data["Customer Name"] = customer_details.get("name", "N/A")
                    txn_data["Customer Email"] = customer_details.get("email", "N/A")
                    txn_data["Phone Number"] = customer_details.get("phone_number", "N/A")
                # Note: The original quantity is part of the customer_info_map, 
                # but we prefer to show the purchase quantity only on the PURCHASE row,
                # and the guests checked in (num_entering) on the VERIFY row.

            all_txns_for_display.append(txn_data)

    df_all_txns = pd.DataFrame(all_txns_for_display)
    
    # ------------------ 3. Download Button ------------------
    if not df_all_txns.empty:
        # Sort data by timestamp before export for logical flow
        df_all_txns = df_all_txns.sort_values(by="Timestamp (Unix)", ascending=True) 
        
        csv = df_all_txns.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download All Transactions Data (CSV)",
            data=csv,
            file_name='blockchain_event_audit.csv',
            mime='text/csv',
            help="Download a CSV file containing every transaction recorded on the blockchain, including the block hash proof and customer details."
        )

    st.markdown("### All Recorded Transactions (Audit Table)")
    
    if df_all_txns.empty:
         st.info("No purchase or check-in transactions have been recorded yet.")
    else:
        # Display the full, clean DataFrame 
        st.dataframe(
            df_all_txns.drop(columns=["Timestamp (Unix)", "Previous Block Hash"]), 
            use_container_width=True,
            # Set the order for comprehensive and logical display
            column_order=[
                "Block Index", 
                "Transaction Type", 
                "Time (Readable)", 
                "Ticket ID", 
                "Event Name", 
                "Customer Name", 
                "Customer Email", 
                "Phone Number", 
                "Quantity/Guests", 
                "Verifier",
                "Block Hash (Ledger Proof)" 
            ]
        )

    st.markdown("---")
    st.markdown("### Block-by-Block Detail")
    
    # ------------------ 4. Block-by-Block Detailed View ------------------
    # Iterate through blocks in reverse order (most recent first)
    for i, block in enumerate(reversed(blockchain_data)):
        # Calculate the display index 
        block_index = len(blockchain_data) - 1 - i
        
        with st.expander(f"Block #{block_index} (Index: {block['index']}) - {len(block['transactions'])} Transactions", expanded=(i == 0)):
            
            # Display core block metadata
            st.markdown(f"**Timestamp:** `{time.ctime(block['timestamp'])}`")
            st.code(f"Hash: {block['hash']}", language='text')
            st.code(f"Previous Hash: {block['previous_hash']}", language='text')
            
            st.markdown("#### Transactions Contained in this Block:")
            
            if block["transactions"]:
                # Format transactions for display in a pandas DataFrame
                txns_for_display = []
                for txn in block["transactions"]:
                    txn_data = {
                        "Type": txn.get("type", "N/A"),
                        "Event": txn.get("event", "N/A"),
                        "ID": txn.get("ticket_id", "N/A"),
                        "Qty/Guests": txn.get("quantity", txn.get("num_entering", 1)),
                        "Holder/Verifier": txn.get("holder", txn.get("verifier", "N/A")),
                        "Email": txn.get("email", "N/A"),
                        "Time": time.ctime(txn.get("timestamp", 0))
                    }
                    txns_for_display.append(txn_data)
                
                st.dataframe(pd.DataFrame(txns_for_display), use_container_width=True)
            else:
                st.info("No transactions in this block.")

# ------------------------ PAGE FLOW ------------------------
if admin_view:
    show_admin_audit()
elif event_selected is None:
    show_events()
else:
    show_event_actions(event_selected)

# ------------------------ DEVELOPER FOOTER & FLOATING BUTTON ------------------------

# 1. Developer Footer (bottom left)
blocks_count, purchase_count, check_in_count = get_blockchain_stats()
footer_text = f"Blocks Created:{blocks_count} | Purchase Txns:{purchase_count} | Check In Txns:{check_in_count}"

# Link in the footer to the audit view
audit_link_footer = f"<a href='?view=admin' style='color:#E50914; text-decoration:none; font-weight:bold;'>View Audit Ledger</a>"
st.markdown(f"<div class='footer'>{footer_text} | {audit_link_footer}</div>", unsafe_allow_html=True)


# 2. Floating Audit Button (bottom right)
if not admin_view: # Only show the button if we are NOT already on the admin page
    # Embed the Streamlit button in a custom HTML container for fixed positioning
    st.markdown(
        f"""
        <div class='audit-button-container'>
            <a href='?view=admin'>
                <button>
                    Blockchain Audit
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
