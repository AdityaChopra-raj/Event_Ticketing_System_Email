import streamlit as st
from PIL import Image
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
# IMPORT FIX: Centralized Blockchain and helpers
from blockchain import Blockchain, get_ticket_status
from events_data import events 

# ------------------------ CONFIGURATION & SECRETS ------------------------
EMAIL_ADDRESS = st.secrets["email"]["address"]
EMAIL_PASSWORD = st.secrets["email"]["password"]

def send_email(to_email, subject, body):
    """Sends confirmation emails."""
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
        st.error(f"Error sending email. Check secrets.toml and App Password. Error: {e}")


# ------------------------ APP STATE & INITIALIZATION ------------------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
# The selected event will now be driven by st.query_params
# if "event_selected" not in st.session_state:
#     st.session_state.event_selected = None
if "mode" not in st.session_state:
    st.session_state.mode = None
# This cache stores the current ticket status calculated from the blockchain, including customer data.
if "purchased_tickets_cache" not in st.session_state:
    st.session_state.purchased_tickets_cache = {}


st.set_page_config(page_title="Event Ticket Portal", layout="wide")

# Get selected event from query params (URL)
event_selected = st.query_params.get("event")
if event_selected and event_selected not in events:
    # Handle bad URL param by resetting
    st.query_params.clear()
    event_selected = None


# ------------------------ NETFLIX-THEME STYLING ------------------------
st.markdown("""
<style>
/* Base Dark Theme & Font */
.stApp {
    background-color: #141414; /* Deep charcoal background */
    color: white;
    font-family: 'Inter', sans-serif;
}

/* Page Header (Netflix Red) */
h1 {
    /* Title size doubled and font changed to look like a logo */
    text-align: center;
    color: #E50914; /* Netflix Red */
    font-size: 6em; /* Doubled from 3em */
    font-weight: 900;
    letter-spacing: 2px;
    margin-bottom: 20px;
    font-family: 'Avenir', 'Arial Black', sans-serif; /* Logo-style font */
}

/* ----------------------- CLICKABLE CARD STYLES ----------------------- */

/* Visual content container for image */
.event-image-container {
    padding: 10px;
    position: relative;
    z-index: 5; 
    /* FIX: Enforce 2:3 aspect ratio for visual consistency */
    aspect-ratio: 2 / 3; 
    overflow: hidden; 
}

/* Image styling inside the container */
.event-image-container img {
    border-radius: 4px 4px 0 0; /* Match Netflix style */
    /* FIX: Ensure image covers the fixed container size, cropping if necessary */
    width: 100%;
    height: 100%;
    object-fit: cover; 
}


/* Event Title Card - Visual content container */
.event-card {
    border-radius: 8px;
    background: #222; /* Darker card background */
    padding: 15px 5px; 
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    overflow: hidden;
    text-align: center; 
    transition: transform 0.3s ease-in-out, box-shadow 0.3s;
}

/* Link/Title styling for the clickable text */
.event-card a {
    text-decoration: none !important; /* Remove link underline */
    color: white !important; /* White text for contrast */
    font-weight: 700;
    display: block; /* Make the entire div area clickable via the link inside */
}

/* Netflix Red Glow and Zoom on Hover - Applied to the visual element */
.event-card:hover {
    transform: scale(1.05); /* Smooth zoom effect */
    box-shadow: 0 8px 16px rgba(229, 9, 20, 0.6); /* Strong red glow on hover */
    z-index: 6; /* Bring hovered card slightly forward */
    background: #333; /* Slightly lighter background on hover */
}


/* --- Detail View Styles (unchanged) --- */
.detail-container {
    display: flex;
    gap: 30px;
    padding: 20px;
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
}
.event-image-card:hover {
    transform: scale(1.02);
}

.event-description-box {
    padding: 10px;
    color: #ccc;
    width: 100%; 
}
.event-description-box h2 {
    color: #E50914; 
    margin-top: 0;
    margin-bottom: 10px;
    font-size: 2.5em;
}
.event-description-box p {
    font-size: 1.1em;
    line-height: 1.6;
    margin-bottom: 20px;
    color: white;
}
.event-description-box .detail-item strong {
    color: #E50914; 
}

.event-stats {
    background-color: #333;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 20px;
    text-align: center;
    border-left: 5px solid #E50914;
    transition: all 0.3s;
}
.event-stats div {
    font-size: 1.1em;
    font-weight: 600;
    color: #fff;
    margin: 5px 0;
}

/* Standard Streamlit Button Styling (Red with black thin border) */
div.stButton > button {
    background-color: #E50914; /* Netflix Red */
    color: white;
    border: 1px solid black; /* Black thin border */
    padding: 10px 20px;
    font-size: 1em;
    border-radius: 6px;
    margin-top: 10px;
    cursor: pointer;
    transition: background-color 0.2s, transform 0.2s, box-shadow 0.2s;
    font-weight: bold;
}
div.stButton > button:hover {
    background-color: #f6121d; /* Slightly lighter red on hover */
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(229, 9, 20, 0.6); /* Reduced shadow depth */
}

.footer {position:fixed;bottom:10px;left:20px;font-size:16px;color:#E50914;}
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
    The Event Name text is now the clickable element via a markdown link.
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
                # We use use_container_width=True to make Streamlit render the image component 
                # inside the column, and the CSS forces the aspect ratio and crop.
                st.image(img, use_container_width=True)
            except FileNotFoundError:
                 # If the image is missing, use a placeholder that also respects the 2:3 aspect ratio
                 st.image("https://placehold.co/300x450/E50914/FFFFFF?text=Image+Missing", use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True) 
            
            # 2. Clickable Title Card (The bottom part of the card, with hover effect)
            # The title is wrapped in an <a> tag using markdown, pointing to the nav_url
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
            # Changed use_column_width=True to use_container_width=True
            st.image(img, use_container_width=True)
        except FileNotFoundError:
            # Changed use_column_width=True to use_container_width=True
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
        # Using create_block as per the original structure, though the helper file uses mine_block
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

# ------------------------ PAGE FLOW ------------------------
if event_selected is None:
    show_events()
else:
    show_event_actions(event_selected)

# ------------------------ DEVELOPER FOOTER ------------------------
blocks_count, purchase_count, check_in_count = get_blockchain_stats()
footer_text = f"Blocks Created:{blocks_count}-Purchase:{purchase_count} ; Check In:{check_in_count}"

st.markdown(f"<div class='footer'>{footer_text} | Dev only (to check all blocks)</div>", unsafe_allow_html=True)
