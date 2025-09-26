import streamlit as st
from PIL import Image
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import hashlib
import json

# ------------------------ BLOCKCHAIN ------------------------
class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.create_block(previous_hash="0")

    def create_block(self, previous_hash: str):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": self.pending_transactions,
            "previous_hash": previous_hash,
            "hash": ""
        }
        block["hash"] = self.hash_block(block)
        self.pending_transactions = []
        self.chain.append(block)
        return block

    def add_transaction(self, transaction: dict):
        self.pending_transactions.append(transaction)
        return self.last_block["index"] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash_block(block: dict) -> str:
        temp = block.copy()
        temp["hash"] = ""
        return hashlib.sha256(json.dumps(temp, sort_keys=True).encode()).hexdigest()


# ------------------------ EMAIL FUNCTION ------------------------
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
        st.error(f"Error sending email: {e}")


# ------------------------ APP STATE ------------------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
if "tickets" not in st.session_state:
    st.session_state.tickets = {}  # ticket_id -> {event, name, qty, verified, email}
if "event_selected" not in st.session_state:
    st.session_state.event_selected = None
if "mode" not in st.session_state:
    st.session_state.mode = None

EVENTS = {
    "Navratri Pooja": {"capacity": 150, "image": "navratri.jpg"},
    "Diwali Dance": {"capacity": 150, "image": "diwali.jpg"},
    "Freshers": {"capacity": 150, "image": "freshers.jpg"},
    "Ravan Dehan": {"capacity": 150, "image": "ravan.jpg"}
}

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


# ------------------------ HELPER FUNCTIONS ------------------------
def capacity_info(event_name):
    total = EVENTS[event_name]["capacity"]
    scanned = 0
    purchased = 0
    for txn in st.session_state.tickets.values():
        if txn["event"] == event_name:
            purchased += txn["qty"]
            scanned += txn["verified"]
    remaining = total - purchased
    return remaining, scanned

# ------------------------ UI FUNCTIONS ------------------------
def show_events():
    st.session_state.mode = None
    cols = st.columns(len(EVENTS))
    for idx, (ename, edata) in enumerate(EVENTS.items()):
        with cols[idx]:
            img = Image.open(edata["image"])
            st.image(img, use_column_width=True)
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
        if st.button("⬅ Back"):
            st.session_state.event_selected = None
            st.experimental_rerun()
    else:
        if st.button("⬅ Back"):
            st.session_state.mode = None
        if st.session_state.mode == "buy":
            buy_tickets(event_name, remaining)
        elif st.session_state.mode == "verify":
            verify_tickets(event_name)


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
        st.session_state.tickets[ticket_id] = {
            "event": event_name, "name": name, "qty": qty, "verified": 0, "email": email
        }
        st.session_state.blockchain.add_transaction({
            "ticket_id": ticket_id, "event": event_name, "quantity": qty, "holder": name
        })
        st.session_state.blockchain.create_block(st.session_state.blockchain.last_block["hash"])
        st.success(f"Purchase Confirmed! Ticket ID: {ticket_id}")
        body = (f"Hello {name},\n\nYou purchased {qty} ticket(s) for {event_name}.\n"
                f"Ticket ID: {ticket_id}\n\nPresent this ID at the venue for verification.")
        send_email(email, f"{event_name} Ticket Confirmation", body)


def verify_tickets(event_name):
    st.subheader("Verify Ticket ID")
    ticket_id = st.text_input("Enter Ticket ID", key="verify_id")
    num_entering = st.number_input("Number of people entering", min_value=1, value=1, key="verify_num")
    if st.button("Verify", key="verify_btn"):
        t = st.session_state.tickets.get(ticket_id)
        if not t or t["event"] != event_name:
            st.error("Invalid Ticket ID for this event.")
            return
        remaining_to_use = t["qty"] - t["verified"]
        if num_entering > remaining_to_use:
            st.error(f"Only {remaining_to_use} tickets remain for this Ticket ID.")
            return
        t["verified"] += num_entering
        st.success(f"Verified {num_entering} guest(s). Remaining: {t['qty'] - t['verified']}")
        body = (f"Hello {t['name']},\n\n{num_entering} guest(s) used your Ticket ID {ticket_id} for {event_name}.\n"
                f"Remaining tickets: {t['qty'] - t['verified']}")
        send_email(t["email"], f"{event_name} Ticket Verification Update", body)


# ------------------------ PAGE FLOW ------------------------
if st.session_state.event_selected is None:
    show_events()
else:
    show_event_actions(st.session_state.event_selected)

# ------------------------ BLOCKCHAIN COUNTER ------------------------
st.markdown(f"<div class='footer'>Blocks Created: {len(st.session_state.blockchain.chain)}</div>", unsafe_allow_html=True)
