import streamlit as st
from PIL import Image
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import json # Used by imported blockchain

# IMPORT FIX: Centralize Blockchain and helpers
from blockchain import Blockchain, get_ticket_status
from events_data import events 

# ------------------------ EMAIL FUNCTION ------------------------
# NOTE: This uses the correct secrets from secrets.toml
EMAIL_ADDRESS = st.secrets["email"]["address"]
EMAIL_PASSWORD = st.secrets["email"]["password"]

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        st.error(f"Error sending email: Check secrets.toml, App Password, and internet connection. ({e})")


# ------------------------ APP STATE ------------------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()

# FIX: Cache for ticket details, populated by reading the chain
if "purchased_tickets_cache" not in st.session_state:
    st.session_state.purchased_tickets_cache = {}

if "event_selected" not in st.session_state:
    st.session_state.event_selected = None
if "mode" not in st.session_state:
    st.session_state.mode = None

# FIX: Removed redundant local EVENTS dict and Blockchain class


st.set_page_config(page_title="Event Ticket Portal", layout="wide")

# ------------------------ STYLING ------------------------
st.markdown("""
<style>
body {background-color:#141414;color:white;}
.event-card {border-radius:15px;padding:20px;margin:10px;background:#222;text-align:center;}
.event-button button {background:#E50914;color:white;border:none;padding:12px 25px;
                      font-size:18px;border-radius:8px;margin-top:15px;cursor:pointer;}
.event-button button:hover {background:#f6121d;}
.footer {position:fixed;bottom:10px;left:20px;font-size:16px;color:#E50914;}
.event-stats {
    background-color: #333;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 15px;
    text-align: center;
}
.event-stats div {
    font-size: 1.1em;
    font-weight: bold;
    color: #fff;
    margin: 5px 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;color:#E50914;'>Event Ticket Portal</h1>", unsafe_allow_html=True)


# ------------------------ HELPER FUNCTIONS ------------------------
def capacity_info(event_name):
    # FIX: Use get_ticket_status to read blockchain
    _, scanned, remaining, _, purchased_tickets_cache = get_ticket_status(st.session_state.blockchain, event_name)
    st.session_state.purchased_tickets_cache = purchased_tickets_cache # Update cache
    return remaining, scanned

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

# ------------------------ UI FUNCTIONS ------------------------
def show_events():
    st.session_state.mode = None
    # FIX: Use imported 'events' data
    cols = st.columns(len(events))
    for idx, (ename, edata) in enumerate(events.items()):
        with cols[idx]:
            try:
                img = Image.open(edata["image"])
                st.image(img, use_column_width=True)
            except FileNotFoundError:
                 st.warning(f"Image not found for {ename}. Check the 'images/' folder.")
                 st.image("https://via.placeholder.com/300x200?text=Image+Missing")
            
            st.markdown(f"<div class='event-card'><h3 style='color:white'>{ename}</h3></div>", unsafe_allow_html=True)
            if st.button(f"Select {ename}", key=f"select_{ename}"):
                st.session_state.event_selected = ename
                st.experimental_rerun()


def show_event_actions(event_name):
    st.markdown(f"<h2 style='text-align:center;color:#E50914;'>{event_name}</h2>", unsafe_allow_html=True)
    remaining, scanned = capacity_info(event_name)
    
    # Matches PDF Design: Available Tickets and No. of guests in venue
    st.markdown(f"""
    <div class='event-stats'>
        <div>Available Tickets: {remaining}</div>
        <div>No. of guests in venue: {scanned}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.mode is None:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Buy Ticket"):
                st.session_state.mode = "buy"
        with c2:
            if st.button("Check-In"): # Matches PDF Design: Checkin
                st.session_state.mode = "verify"
        if st.button("⬅ Back"):
            st.session_state.event_selected = None
            st.experimental_rerun()
    else:
        if st.button("⬅ Back to Actions"):
            st.session_state.mode = None
        if st.session_state.mode == "buy":
            buy_tickets(event_name, remaining)
        elif st.session_state.mode == "verify":
            verify_tickets(event_name)


def buy_tickets(event_name, remaining):
    st.subheader("Enter Your Details to Buy Ticket")
    # Matches PDF Design inputs: Name, Email, Phone Number, No. of Tickets
    name = st.text_input("Name", key="buy_name")
    email = st.text_input("Email", key="buy_email")
    phone_number = st.text_input("Phone Number", key="buy_phone") # ADDED PHONE NUMBER
    qty = st.number_input("No. of Tickets (max 10)", min_value=1, max_value=10, value=1, key="buy_qty")
    
    if st.button("Confirm Purchase", key="confirm_purchase"):
        if qty > remaining:
            st.error("Not enough remaining capacity")
            return
            
        ticket_id = str(uuid.uuid4())[:8].upper()
        
        # 1. Add PURCHASE transaction to the blockchain
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
        
        st.success(f"Purchase Confirmed! Ticket ID: {ticket_id}")
        
        # 3. Send email confirmation
        body = (f"Hello {name},\n\nYou purchased {qty} ticket(s) for {event_name}.\n"
                f"Ticket ID: {ticket_id}\n\nPresent this ID at the venue for verification.")
        send_email(email, f"{event_name} Ticket Confirmation", body)


def verify_tickets(event_name):
    st.subheader("Check-In")
    # Matches PDF Design inputs: Ticket ID and No. of People Entering
    ticket_id = st.text_input("Enter Ticket ID", key="verify_id").upper()
    num_entering = st.number_input("No. of People Entering", min_value=1, value=1, key="verify_num")
    
    if st.button("Verify", key="verify_btn"):
        # 1. Fetch current status by reading the blockchain
        _, _, _, ticket_details, purchased_tickets_cache = get_ticket_status(st.session_state.blockchain, event_name)
        t_status = ticket_details.get(ticket_id)
        t_info = purchased_tickets_cache.get(ticket_id) 

        if not t_status or t_info["event"] != event_name:
            st.error("❌ Invalid Ticket ID for this event.")
            return

        remaining_to_use = t_status["qty"] - t_status["scanned"]
        
        if remaining_to_use <= 0:
            st.error("❌ Ticket has already been fully used.")
            return
            
        if num_entering > remaining_to_use:
            st.error(f"❌ Only {remaining_to_use} tickets remain for this Ticket ID (Used: {t_status['scanned']}/{t_status['qty']}).")
            return
            
        # 2. Add VERIFY transaction to the blockchain (CRITICAL FIX: IMMUTABILITY)
        st.session_state.blockchain.add_transaction({
            "type": "VERIFY", 
            "ticket_id": ticket_id, 
            "event": event_name, 
            "num_entering": num_entering,
            "timestamp": time.time()
        })
        
        # 3. Mine a new block
        st.session_state.blockchain.create_block(st.session_state.blockchain.last_block["hash"])
        
        # 4. Success feedback and email
        new_remaining = remaining_to_use - num_entering
        st.success(f"✅ Verified {num_entering} guest(s). Remaining: {new_remaining}")
        
        body = (f"Hello {t_info['name']},\n\n{num_entering} guest(s) used your Ticket ID {ticket_id} for {event_name}.\n"
                f"Remaining tickets: {new_remaining}")
        send_email(t_info["email"], f"{event_name} Ticket Verification Update", body)


# ------------------------ PAGE FLOW ------------------------
if st.session_state.event_selected is None:
    show_events()
else:
    show_event_actions(st.session_state.event_selected)

# ------------------------ BLOCKCHAIN COUNTER (PDF Design Footer) ------------------------
blocks_count, purchase_count, check_in_count = get_blockchain_stats()
footer_text = f"Blocks Created:{blocks_count}-Purchase:{purchase_count} ; Check In:{check_in_count}"

st.markdown(f"<div class='footer'>{footer_text} | Dev only (to check all blocks)</div>", unsafe_allow_html=True)
