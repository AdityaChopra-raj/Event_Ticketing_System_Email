import streamlit as st
from PIL import Image
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import json

# Import the centralized classes and data
from blockchain import Blockchain
from events_data import events

# ------------------------ EMAIL FUNCTION ------------------------
# NOTE: Update your secrets.toml with the actual password before deployment
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
        # Simplified error handling for Streamlit demo
        st.error(f"Error sending email: Check your secrets.toml and internet connection. ({e})")


# ------------------------ APP STATE ------------------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
# The 'purchased_tickets' dict stores basic ticket info for quick lookup (e.g., email for verification updates)
if "purchased_tickets" not in st.session_state:
    st.session_state.purchased_tickets = {} 

if "event_selected" not in st.session_state:
    st.session_state.event_selected = None
if "mode" not in st.session_state:
    st.session_state.mode = None


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
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;color:#E50914;'>Event Ticket Portal</h1>", unsafe_allow_html=True)


# ------------------------ HELPER FUNCTIONS (The CORE FIX) ------------------------
def get_ticket_status(event_name):
    """
    Calculates total purchased, scanned, and remaining capacity by reading the blockchain.
    This is the single source of truth for the app.
    """
    total_capacity = events[event_name]["capacity"]
    total_purchased = 0
    total_scanned = 0
    
    # Store ticket status: ticket_id -> {'qty': x, 'scanned': y}
    ticket_details = {} 

    for block in st.session_state.blockchain.chain:
        for txn in block["transactions"]:
            if txn.get("event") == event_name:
                ticket_id = txn.get("ticket_id")
                if not ticket_id:
                    continue # Skip invalid transactions

                # PURCHASE Transaction
                if txn.get("type") == "PURCHASE":
                    qty = txn["quantity"]
                    total_purchased += qty
                    # Initialize ticket status
                    ticket_details[ticket_id] = {"qty": qty, "scanned": 0}
                    # Update quick lookup table
                    st.session_state.purchased_tickets[ticket_id] = {
                        "event": event_name, "name": txn.get("holder", "N/A"), "qty": qty, "email": txn.get("email", "N/A")
                    }

                # VERIFY Transaction (The new, immutable event)
                elif txn.get("type") == "VERIFY":
                    num_entering = txn.get("num_entering", 0)
                    
                    if ticket_id in ticket_details:
                        ticket_details[ticket_id]["scanned"] += num_entering
                        total_scanned += num_entering
                    # If a VERIFY txn exists for a ticket_id that hasn't PURCHASED, it will be ignored here.

    remaining_capacity = total_capacity - total_purchased
    
    return total_purchased, total_scanned, remaining_capacity, ticket_details

def capacity_info(event_name):
    """Simple wrapper for the UI display."""
    _, scanned, remaining, _ = get_ticket_status(event_name)
    return remaining, scanned


# ------------------------ UI FUNCTIONS ------------------------
def show_events():
    st.session_state.mode = None
    cols = st.columns(len(events))
    for idx, (ename, edata) in enumerate(events.items()):
        with cols[idx]:
            try:
                img = Image.open(edata["image"])
                st.image(img, use_column_width=True)
            except FileNotFoundError:
                 st.warning(f"Image not found for {ename}")
            
            st.markdown(f"<div class='event-card'><h3 style='color:white'>{ename}</h3></div>", unsafe_allow_html=True)
            if st.button(f"Select {ename}", key=f"select_{ename}"):
                st.session_state.event_selected = ename
                st.experimental_rerun()


def show_event_actions(event_name):
    st.markdown(f"<h2 style='text-align:center;color:#E50914;'>{event_name}</h2>", unsafe_allow_html=True)
    remaining, scanned = capacity_info(event_name)
    st.write(f"**Tickets Scanned:** {scanned} | **Remaining Capacity:** {remaining}")
    if st.session_state.mode is None:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Buy Ticket"):
                st.session_state.mode = "buy"
        with c2:
            if st.button("Verify Ticket"):
                st.session_state.mode = "verify"
        if st.button("⬅ Back to Events"):
            st.session_state.event_selected = None
            st.experimental_rerun()
    else:
        if st.button("⬅ Back to Actions"):
            st.session_state.mode = None
        if st.session_state.mode == "buy":
            buy_tickets(event_name, remaining)
        elif st.session_state.mode == "verify":
            verify_tickets_logic(event_name)


def buy_tickets(event_name, remaining):
    st.subheader("Enter Your Details to Buy Ticket")
    name = st.text_input("Name", key="buy_name")
    email = st.text_input("Email", key="buy_email")
    qty = st.number_input("Number of Tickets (max 10)", min_value=1, max_value=10, value=1, key="buy_qty")
    
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
            "timestamp": time.time()
        })
        
        # 2. Mine a new block
        st.session_state.blockchain.create_block(st.session_state.blockchain.last_block["hash"])
        
        st.success(f"Purchase Confirmed! Ticket ID: {ticket_id}")
        
        # 3. Send email confirmation
        body = (f"Hello {name},\n\nYou purchased {qty} ticket(s) for {event_name}.\n"
                f"Ticket ID: {ticket_id}\n\nPresent this ID at the venue for verification.")
        send_email(email, f"{event_name} Ticket Confirmation", body)


def verify_tickets_logic(event_name):
    st.subheader("Verify Ticket ID")
    ticket_id = st.text_input("Enter Ticket ID", key="verify_id").upper()
    num_entering = st.number_input("Number of people entering", min_value=1, value=1, key="verify_num")
    
    if st.button("Verify", key="verify_btn"):
        # 1. Fetch current status by recalculating from the blockchain
        _, _, _, ticket_details = get_ticket_status(event_name)
        
        t_status = ticket_details.get(ticket_id)
        t_info = st.session_state.purchased_tickets.get(ticket_id)

        if not t_status or t_info["event"] != event_name:
            st.error("❌ Invalid Ticket ID or Ticket ID for a different event.")
            return

        remaining_to_use = t_status["qty"] - t_status["scanned"]
        
        if remaining_to_use <= 0:
            st.error("❌ Ticket has already been fully used.")
            return
            
        if num_entering > remaining_to_use:
            st.error(f"❌ Only {remaining_to_use} tickets remain for this Ticket ID (Used: {t_status['scanned']}/{t_status['qty']}).")
            return
            
        # 2. Add VERIFY transaction to the blockchain (The CRITICAL STEP)
        st.session_state.blockchain.add_transaction({
            "type": "VERIFY", 
            "ticket_id": ticket_id, 
            "event": event_name, 
            "num_entering": num_entering,
            "verifier": "Venue Gate 1", 
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

# ------------------------ BLOCKCHAIN COUNTER ------------------------
st.markdown(f"<div class='footer'>Blocks Created: {len(st.session_state.blockchain.chain)}</div>", unsafe_allow_html=True)
