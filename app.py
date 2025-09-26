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


# ------------------------ APP STATE ------------------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
if "event_selected" not in st.session_state:
    st.session_state.event_selected = None
if "mode" not in st.session_state:
    st.session_state.mode = None

st.set_page_config(page_title="Event Ticket Portal", layout="wide")

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
    text-align: center;
    color: #E50914; /* Netflix Red */
    font-size: 3em;
    font-weight: 700;
    letter-spacing: 1px;
}

/* Event Cards - Smooth Transitions */
.event-card-container {
    padding: 10px;
    cursor: pointer;
    transition: transform 0.3s ease-in-out, box-shadow 0.3s;
}
.event-card-container:hover {
    transform: scale(1.05); /* Smooth zoom effect */
    box-shadow: 0 8px 16px rgba(229, 9, 20, 0.4); /* Red glow on hover */
}
.event-card {
    border-radius: 8px;
    background: #222; /* Darker card background */
    padding: 15px;
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    overflow: hidden;
}

/* Event Stats Box (Matching PDF Design) */
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

/* Streamlit Button Styling (Red and smooth) */
div.stButton > button {
    background-color: #E50914; 
    color: white;
    border: none;
    padding: 10px 20px;
    font-size: 1em;
    border-radius: 6px;
    margin-top: 10px;
    cursor: pointer;
    transition: background-color 0.2s, transform 0.2s, box-shadow 0.2s;
    font-weight: bold;
}
div.stButton > button:hover {
    background-color: #f6121d; /* Slightly brighter red on hover */
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(229, 9, 20, 0.6);
}

/* Inputs */
.stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > select {
    background-color: #333;
    color: white;
    border: 1px solid #555;
    border-radius: 4px;
}
.footer {position:fixed;bottom:10px;left:20px;font-size:16px;color:#E50914;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>Event Ticket Portal</h1>", unsafe_allow_html=True)

# ------------------------ HELPER FUNCTIONS ------------------------
def capacity_info(event_name):
    """Fetches real-time status by reading the blockchain."""
    _, scanned, remaining, _, purchased_tickets_cache = get_ticket_status(st.session_state.blockchain, event_name)
    st.session_state.purchased_tickets_cache = purchased_tickets_cache 
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

# ------------------------ UI SCREENS ------------------------

def show_events():
    """Renders the main event selection screen (Page 1 of PDF)."""
    st.session_state.mode = None
    
    cols = st.columns(len(events))
    for idx, (ename, edata) in enumerate(events.items()):
        with cols[idx]:
            st.markdown("<div class='event-card-container'>", unsafe_allow_html=True) 
            try:
                img = Image.open(edata["image"])
                st.image(img, use_column_width=True)
            except FileNotFoundError:
                 st.image("https://placehold.co/300x200/E50914/FFFFFF?text=Image+Missing", use_column_width=True)
            
            st.markdown(f"<div class='event-card'><h3 style='color:white; margin:0;'>{ename}</h3></div>", unsafe_allow_html=True)
            if st.button(f"Select {ename}", key=f"select_{ename}"):
                st.session_state.event_selected = ename
                st.experimental_rerun()
            st.markdown("</div>", unsafe_allow_html=True) 

def show_event_actions(event_name):
    """Renders event actions (Buy/Check-In) and statistics (Page 2 of PDF)."""
    st.markdown(f"<h2 style='text-align:center;color:white;'>{event_name}</h2>", unsafe_allow_html=True)
    
    # Display statistics
    remaining, scanned = capacity_info(event_name)
    st.markdown(f"""
    <div class='event-stats'>
        <div>Available Tickets: {remaining}</div>
        <div>No. of guests in venue: {scanned}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.mode is None:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("⬅ Back to Events"):
                st.session_state.event_selected = None
                st.experimental_rerun()
        with c2:
            if st.button("Buy Ticket", key="action_buy"):
                st.session_state.mode = "buy"
        with c3:
            if st.button("Check-In", key="action_verify"): 
                st.session_state.mode = "verify"
    else:
        if st.button("⬅ Back to Actions"):
            st.session_state.mode = None
        
        if st.session_state.mode == "buy":
            buy_tickets(event_name, remaining)
        elif st.session_state.mode == "verify":
            # Direct the user to the dedicated verification app
            st.error("Please use the separate **Ticket Verification App** to check-in guests.")
            st.subheader("Check-In (Sales Portal View)")
            st.markdown("Gate attendants must use the dedicated 'Ticket Verification' application for security and logging purposes.")


def buy_tickets(event_name, remaining):
    """Renders the purchase form and adds an immutable PURCHASE transaction (Page 3 of PDF)."""
    st.subheader("Enter Your Details to Buy Ticket")
    
    # Matches PDF Design inputs: Name, Email, Phone Number, No. of Tickets
    with st.form(key='purchase_form'):
        name = st.text_input("Name", key="buy_name")
        email = st.text_input("Email", key="buy_email")
        phone_number = st.text_input("Phone Number", key="buy_phone") # INCLUDES PHONE NUMBER
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
        body = (f"Hello {name},\n\nYou purchased {qty} ticket(s) for {event_name}.\n"
                f"Ticket ID: {ticket_id}\n\nPresent this ID at the venue for verification.")
        send_email(email, f"{event_name} Ticket Confirmation", body)

# ------------------------ PAGE FLOW ------------------------
if st.session_state.event_selected is None:
    show_events()
else:
    show_event_actions(st.session_state.event_selected)

# ------------------------ DEVELOPER FOOTER ------------------------
blocks_count, purchase_count, check_in_count = get_blockchain_stats()
footer_text = f"Blocks Created:{blocks_count}-Purchase:{purchase_count} ; Check In:{check_in_count}"

st.markdown(f"<div class='footer'>{footer_text} | Dev only (to check all blocks)</div>", unsafe_allow_html=True)
