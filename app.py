import streamlit as st
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import pandas as pd
import random # Placeholder import is now replaced by blockchain methods

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

    # Warning ensures the user knows email won't work without configuration
    st.info("""
        ⚠️ **Email Functionality Note:** Email sending is disabled because the required 
        `[email]` secrets were not found. Please configure `.streamlit/secrets.toml`
        to enable confirmation emails.
    """, icon="🚫")


def send_email(to_email, subject, body):
    """Sends confirmation emails."""

    if not EMAIL_SECRET_LOADED:
        st.info(f"Email skipped: Confirmation for '{to_email}' not sent (Secrets not configured).")
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        st.toast("Email sent successfully!", icon='📧')
    except Exception as e:
        # Display helpful error for email delivery issues
        st.error(f"Error sending email: Check your App Password or email settings. Error: {e}")


# ------------------------ APP STATE & INITIALIZATION ------------------------

if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
if "mode" not in st.session_state:
    st.session_state.mode = None
if "purchased_tickets_cache" not in st.session_state:
    st.session_state.purchased_tickets_cache = {}

# CRITICAL: Use layout="wide" to maximize horizontal space

st.set_page_config(page_title="Event Ticket Portal", layout="wide")

# Get selected event or admin view from query params (URL)

event_selected = st.query_params.get("event")
admin_view = st.query_params.get("view") == "admin" # Admin view check

if event_selected and event_selected not in events:
    # Handle bad URL param by resetting
    st.query_params.clear()
    event_selected = None

# ------------------------ NETFLIX-THEME STYLING (Integrated Canvas Design) ------------------------

st.markdown("""

<style>
/* --------------------------------------------------------------------------------- */
/* ---- 1. COLOR PALETTE & BASE STYLES (Based on Canvas Section 1) ---- */
/* --------------------------------------------------------------------------------- */
.stApp {
    background-color: #141414; /* Background (Primary): Deep Charcoal */
    color: white; /* Foreground (Text): Pure White */
    font-family: 'Inter', sans-serif; /* Font Family: sans-serif */
    padding: 0 !important;
    margin: 0 !important;
}

/* Fix Streamlit Header & Content Padding */
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 2rem !important; /* Added bottom padding for footer space */
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}
.stApp > header {
    background-color: #141414 !important;
    padding: 0 !important;
    margin: 0 !important;
    height: 0 !important;
}

/* --------------------------------------------------------------------------------- */
/* ---- 2. TYPOGRAPHY (Based on Canvas Section 2) ---- */
/* --------------------------------------------------------------------------------- */
h1 {
    /* Main Title/Heading (H1) */
    text-align: center;
    color: #E50914; /* Accent Color: Netflix Red */
    font-size: 3.5em; /* Slightly larger */
    font-weight: 900; /* Bold */
    letter-spacing: 2px;
    margin-top: 5px !important;

    margin-bottom: 20px !important; /* Added margin here for spacing from top content */
    padding: 0 !important;
    font-family: 'Avenir', 'Arial Black', sans-serif;
}

/* Body Text (Modified Streamlit Text/Paragraphs) */
p, .stText, .detail-item {
    color: #CCCCCC; /* Body Text: Light Gray */
    font-size: 1.1em;
    line-height: 1.6; /* Generous line-height */
}

/* --------------------------------------------------------------------------------- */
/* ---- 4. INTERACTIVE ELEMENTS (Cards & Buttons) (Based on Canvas Section 4) ---- */
/* --------------------------------------------------------------------------------- */

/* Card Image Container (Ensures 2:3 aspect ratio) */
.event-image-container {
    position: relative;
    z-index: 5;
    aspect-ratio: 2 / 3; /* Structure: 2:3 aspect ratio */
    overflow: hidden;
    max-width: 250px;
    margin-left: auto;
    margin-right: auto;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}
.event-image-container img {
    border-radius: 4px; /* Image corners inside the card */
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* Content Cards (Event Cards) */
.event-card {
    border-radius: 10px; /* Subtly rounded corners */
    background: #222222; /* Secondary Background: Dark Gray */
    padding: 10px 5px 0px 5px; /* Adjust padding for better look */
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    overflow: hidden;
    text-align: center;
    /* Transition smoothly */
    transition: transform 0.3s ease-in-out, box-shadow 0.3s, background-color 0.3s;
}

/* Card Hover Interaction (Crucial) */
.event-card:hover {
    transform: scale(1.05); /* Slightly scale up (scale-105) */
    /* Prominent box-shadow glow in Accent Color */
    box-shadow: 0 8px 20px rgba(229, 9, 20, 0.9);
    z-index: 6;
    background: #333333; /* Slightly lighter on hover */
    cursor: pointer;
}
/* Ensure the link inside the card doesn't ruin the look */
.event-card a {
    text-decoration: none;
    color: white;
}

/* Primary Buttons (Red with vertical lift/shadow on hover) */
div.stButton > button {
    background-color: #E50914; /* Accent Color: Netflix Red */
    color: white; /* Text: White, bold */
    border: none;
    padding: 10px 20px; /* Slightly larger padding */
    font-size: 1em;
    border-radius: 6px;
    margin-top: 15px; /* Added margin */
    cursor: pointer;
    transition: background-color 0.2s, transform 0.2s, box-shadow 0.2s;
    font-weight: bold;
    min-width: 150px; /* Ensure buttons are wide enough */
}
div.stButton > button:hover {
    background-color: #f6121d; /* Slightly darken/brighter red */
    transform: translateY(-2px); /* Subtle vertical lift (translate-y-[-1px]) */
    box-shadow: 0 6px 10px rgba(229, 9, 20, 0.7); /* Small shadow */
}

/* --- Detail View Styles --- */
.detail-container {
    display: flex;
    gap: 30px; /* Increased gap */
    padding: 20px;
    margin-top: 30px;
    margin-bottom: 20px;
    background-color: #1a1a1a;
    border-radius: 10px;
    box-shadow: 0 0 25px rgba(0, 0, 0, 0.8);
}
.event-description-box h2 {
    color: white; /* Title inside detail box */
    margin-top: 0;
    margin-bottom: 10px;
    font-size: 2.5em;
    text-align: left; /* Must be left-aligned in detail view */
}
.event-description-box .detail-item strong {
    color: #E50914;
}

/* --------------------------------------------------------------------------------- */
/* ---- 5. CONTAINERS & STATUS BARS (Based on Canvas Section 5) ---- */
/* --------------------------------------------------------------------------------- */

/* Info/Status Boxes (Event Stats) */
.event-stats {
    background-color: #222222; /* Dark background */
    padding: 15px;
    border-radius: 8px;
    margin-top: 20px;
    margin-bottom: 20px;
    text-align: center;
    /* Thick, vertical Accent Color stripe on the left edge */
    border-left: 8px solid #E50914;
    transition: all 0.3s;
    line-height: 2;
    font-weight: bold;
}

/* Floating Audit Button Positioning (bottom right) */
.audit-button-container {
    position: fixed;
    bottom: 20px; /* Space from bottom */
    right: 20px; /* Space from right */
    z-index: 1000;
}
.audit-button-container a {
    text-decoration: none;
}
/* Apply primary button style to the floating button */
.audit-button-container button {
    background-color: #E50914 !important; /* Netflix Red */
    color: white !important;
    padding: 12px 24px !important;
    font-size: 1.1em !important;
    font-weight: bold !important;
    border: none !important;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5); /* Add shadow for lift */
    border-radius: 6px;
    cursor: pointer;
    transition: background-color 0.2s, transform 0.2s, box-shadow 0.2s;
}
div.stButton > button:hover {
    background-color: #f6121d; /* Slightly darken/brighter red */
    transform: translateY(-2px); /* Subtle vertical lift (translate-y-[-1px]) */
    box-shadow: 0 6px 10px rgba(229, 9, 20, 0.7); /* Small shadow */
}


/* Footer Link Color */
.footer a {
    color: #E50914 !important;
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

    # Use fluid columns for responsiveness (Canvas Section 3: Grid System)
    # Use st.columns based on event count, max 5 wide
    num_events = len(events)
    cols = st.columns(min(num_events, 5))

    # Ensure we cycle through the columns correctly if more than 5 events were added
    event_list = list(events.items())

    for idx, (ename, edata) in enumerate(event_list):
        # Determine which column to place the content in
        col_index = idx % len(cols)

        with cols[col_index]:
            # Create the navigation URL string for this event card
            nav_url = f'?event={ename}'

            # 1. Clickable Title Card (Content Card: Secondary Background, Hover Interaction)
            st.markdown(f"""
            <a href="{nav_url}" style="text-decoration:none;">
            <div class='event-card'>
                <div class='event-image-container'>
            """, unsafe_allow_html=True)

            # Use st.image with the URL defined in events_data.py
            image_url = edata.get("image", "https://placehold.co/300x450/E50914/FFFFFF?text=Image+Missing")
            st.image(image_url, use_container_width=True)

            st.markdown(f"""
                </div>
                <h3 style='color:white; margin:10px 0 15px 0;'>{ename}</h3>
            </div>
            </a>
            """, unsafe_allow_html=True)


def show_event_actions(event_name):
    """
    Renders event details, actions (Buy/Check-In), and statistics in a two-column (Netflix-style) layout.
    """

    # Get event data and status
    edata = events[event_name]
    remaining, scanned, _ = capacity_info(event_name)

    # Use markdown for the detail container to apply custom CSS
    st.markdown("<div class='detail-container'>", unsafe_allow_html=True)

    # Set column widths: 1 for image, 2.5 for details
    col_image, col_details = st.columns([1, 2.5])

    with col_image:
        # Image Card (Left Side)
        st.markdown("<div class='event-image-card' style='max-width:300px;'>", unsafe_allow_html=True)
        # Use st.image with the URL defined in events_data.py
        image_url = edata.get("image", "https://placehold.co/300x450/E50914/FFFFFF?text=Image+Missing")
        st.image(image_url, use_container_width=True)
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

        # Display statistics (Canvas Section 5: Info/Status Boxes)
        st.markdown(f"""
        <div class='event-stats'>
            <div style='font-size:1.2em;'>Available Tickets: <span style='color:#E50914;'>{remaining}</span></div>
            <div style='font-size:1.2em;'>Guests Checked In: <span style='color:white;'>{scanned}</span></div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.mode is None:
            c1, c2, c3 = st.columns(3)
            with c1:
                # Back button
                if st.button("⬅ Back to Events"):
                    st.query_params.clear()
                    st.rerun()
            with c2:
                # Primary Button Style
                if st.button("Buy Ticket", key="action_buy"):
                    st.session_state.mode = "buy"
            with c3:
                # Primary Button Style
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

        # Primary Button Style
        submitted = st.form_submit_button("Confirm Purchase")

    if submitted:
        if not name or not email or not phone_number:
            st.error("Please fill in all details.")
            return

        if qty > remaining:
            st.error("Not enough remaining capacity")
            return

        # --- Proof of Work Calculation ---
        last_proof = st.session_state.blockchain.last_block["proof"]
        # Calculate the Proof of Work
        proof_of_work = st.session_state.blockchain.proof_of_work(last_proof)
        # ---------------------------------
        
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

        # 2. Mine a new block with the calculated proof
        st.session_state.blockchain.create_block(proof=proof_of_work)

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

    # Primary Button Style
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

        # --- Proof of Work Calculation ---
        last_proof = st.session_state.blockchain.last_block["proof"]
        # Calculate the Proof of Work
        proof_of_work = st.session_state.blockchain.proof_of_work(last_proof)
        # ---------------------------------

        # 5. Process Check-in (Add VERIFY transaction and mine block)
        st.session_state.blockchain.add_transaction({
            "type": "VERIFY",
            "ticket_id": ticket_id,
            "event": event_name,
            "num_entering": num_entering,
            "verifier": "Main Portal Check-In",
            "timestamp": time.time()
        })
        # Mine block with the calculated proof
        st.session_state.blockchain.create_block(proof=proof_of_work)

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
    """
    st.subheader("🔒 Blockchain Audit Ledger")
    st.markdown("---")

    blockchain_data = st.session_state.blockchain.chain
    all_txns_for_display = []

    # Primary Button Style
    if st.button("⬅ Back to Events Dashboard"):
        st.query_params.clear()
        st.rerun()

    if not blockchain_data:
        st.info("The blockchain is currently empty (only the genesis block exists).")
        return

    # NEW: 1. Generate the customer purchase information map once (ticket_id -> customer details)
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
            st.markdown(f"**Proof-of-Work:** `{block.get('proof', 'N/A')}`") # Added proof display
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

# The footer div ensures light gray text and the accent link color

st.markdown(f"<div class='footer' style='color: #CCCCCC; font-size: 14px; position: fixed; bottom: 10px; left: 20px;'>{footer_text} | {audit_link_footer}</div>", unsafe_allow_html=True)

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
