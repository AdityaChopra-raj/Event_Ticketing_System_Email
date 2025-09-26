import streamlit as st
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# IMPORT FIX: Centralized Blockchain and helper function
from blockchain import Blockchain, get_ticket_status
from events_data import events

# ------------------------ CONFIGURATION & SECRETS (Needed for email) ------------------------
# Ensure these secrets are available in your environment's secrets.toml
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
        st.toast("Check-in Email sent successfully!", icon='📧')
    except Exception as e:
        st.error(f"Error sending email. Check secrets.toml and App Password. Error: {e}")

# ------------------------ APP STATE AND CONFIG ------------------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
blockchain = st.session_state.blockchain

# Initialize event selection state
if "verify_event" not in st.session_state:
    st.session_state.verify_event = list(events.keys())[0] if events else None

st.set_page_config(page_title="Ticket Verification", layout="centered", page_icon="✅")

# ------------------------ NETFLIX-THEME STYLING ------------------------
st.markdown("""
<style>
/* Base Dark Theme & Font */
.stApp {
    background-color: #141414;
    color: white;
    font-family: 'Inter', sans-serif;
}
/* Page Header (Netflix Red) */
h1 {
    text-align: center;
    color: #E50914;
    font-size: 3em;
    font-weight: 700;
    letter-spacing: 2px;
    text-shadow: 2px 2px 4px #000000;
}
hr {
    border-top: 2px solid #E50914;
}

/* Streamlit Button Styling (Red and smooth) */
div.stButton > button {
    background-color: #E50914; 
    color: white;
    font-weight: bold;
    padding: 10px 20px;
    border-radius: 6px;
    width: 250px;
    margin: 20px auto;
    display: block;
    cursor: pointer;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    transition: background-color 0.2s, transform 0.2s;
}
div.stButton > button:hover {
    background-color: #f6121d; 
    transform: scale(1.03);
}

/* Inputs */
.stTextInput > div > div > input, .stNumberInput > div > div > input {
    background-color: #333;
    color: white;
    border: 1px solid #555;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

# --- Heading (Page 4 of PDF) ---
st.markdown("<h1>✅ Ticket Verification</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Input fields
if st.session_state.verify_event:
    event_name = st.selectbox("Select Event", list(events.keys()), key="event_select_box", index=list(events.keys()).index(st.session_state.verify_event))
    st.session_state.verify_event = event_name

# Get the latest ticket status every time the event or page loads
total_purchased, total_scanned, remaining_capacity, ticket_details, purchased_tickets_cache = get_ticket_status(blockchain, st.session_state.verify_event)

st.markdown(f"""
    <div style='background-color:#333; padding: 10px; border-radius: 4px; margin-bottom: 20px;'>
        <p style='margin: 0; font-weight: bold;'>Event Capacity Status for {st.session_state.verify_event}:</p>
        <small>Total Purchased: {total_purchased} | Scanned: {total_scanned} | Remaining Capacity: {remaining_capacity}</small>
    </div>
    """, unsafe_allow_html=True)

ticket_id = st.text_input("Enter Ticket ID").upper() 
email_input = st.text_input("Enter Customer Email", help="Required for double-checking customer identity.") # Email field is back
num_entering = st.number_input("No. of People Entering", min_value=1, value=1, key="verify_num", help="How many people are entering using this ID?")

# Verify button
if st.button("Verify Ticket"):
    if not ticket_id or not email_input:
        st.warning("Please enter both Ticket ID and Customer Email.")
        st.stop()
    
    # Get the current status for the specific ticket ID
    t_status = ticket_details.get(ticket_id)
    t_purchase_info = purchased_tickets_cache.get(ticket_id)
    
    if not t_status or not t_purchase_info:
        st.error("❌ Invalid Ticket ID for this event or ticket was purchased for another event.")
        
    elif t_purchase_info['email'].lower() != email_input.lower():
        st.error("❌ Email address does not match the purchasing customer on record for this Ticket ID.")
        
    else:
        total_tickets = t_status["qty"]
        scanned_tickets = t_status["scanned"]
        remaining_to_use = total_tickets - scanned_tickets
        
        if remaining_to_use <= 0:
            st.error("❌ Ticket has already been fully used.")
            
        elif num_entering > remaining_to_use:
            st.error(f"❌ Cannot check in {num_entering} guests. Only {remaining_to_use} tickets remain for this Ticket ID (Used: {scanned_tickets}/{total_tickets}).")
            
        else:
            # 1. Add a new, immutable VERIFY transaction
            blockchain.add_transaction({
                "type": "VERIFY", 
                "ticket_id": ticket_id, 
                "event": st.session_state.verify_event, 
                "num_entering": num_entering,
                "verifier": "Venue Gate - Verify App", 
                "timestamp": time.time()
            })
            
            # 2. Mine a new block
            blockchain.create_block(blockchain.last_block["hash"])
            
            # 3. Recalculate new status to reflect the check-in
            # Rerun status calculation to get the absolute latest status after the new block
            _, _, _, new_ticket_details, _ = get_ticket_status(blockchain, st.session_state.verify_event)
            new_scanned_tickets = new_ticket_details[ticket_id]["scanned"]
            new_remaining = total_tickets - new_scanned_tickets
            
            st.balloons()
            st.success(f"✅ VERIFIED {num_entering} GUEST(S) for {t_purchase_info['name']}. Remaining: **{new_remaining}**")

            # Prepare and send confirmation email using the email stored during PURCHASE
            email_body = (
                f"Hello {t_purchase_info['name']},\n\n"
                f"A check-in was successfully processed for your **{st.session_state.verify_event}** ticket.\n\n"
                f"**Ticket ID:** {ticket_id}\n"
                f"**Guests Checked In Now:** {num_entering}\n"
                f"**Total Used Tickets:** {new_scanned_tickets} / {total_tickets}\n"
                f"**Tickets Remaining:** {new_remaining}\n\n"
                f"This activity was recorded at the venue gate.\n\n"
                f"--- Check-In Confirmation from Verification Gate ---"
            )
            
            send_email(
                t_purchase_info['email'], 
                f"Check-In Update: {st.session_state.verify_event} - {num_entering} Guests Entered", 
                email_body
            )
            
            # Rerun to clear input fields and update stats
            st.rerun()
