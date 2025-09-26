import streamlit as st
import hashlib, json, time, smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

# ----------------------------------------------------------------------
# -------------------------  BLOCKCHAIN LOGIC  -------------------------
# ----------------------------------------------------------------------
class Blockchain:
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        self.create_block(previous_hash="0")

    def create_block(self, previous_hash: str) -> Dict[str, Any]:
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": self.pending_transactions,
            "previous_hash": previous_hash,
            "hash": "",
        }
        block["hash"] = self.hash_block(block)
        self.pending_transactions = []
        self.chain.append(block)
        return block

    def add_transaction(self, transaction: Dict[str, Any]) -> int:
        self.pending_transactions.append(transaction)
        return self.last_block["index"] + 1

    @property
    def last_block(self) -> Dict[str, Any]:
        return self.chain[-1]

    @staticmethod
    def hash_block(block: Dict[str, Any]) -> str:
        temp = block.copy()
        temp["hash"] = ""
        return hashlib.sha256(json.dumps(temp, sort_keys=True).encode()).hexdigest()

# ----------------------------------------------------------------------
# ---------------------------  EMAIL UTILS  ----------------------------
# ----------------------------------------------------------------------
def send_email(to_address: str, subject: str, body: str):
    """Send email via Gmail SMTP using credentials in .streamlit/secrets.toml"""
    email_user = st.secrets["email"]["address"]
    email_pass = st.secrets["email"]["password"]

    msg = MIMEMultipart()
    msg["From"] = email_user
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(email_user, email_pass)
        server.sendmail(email_user, to_address, msg.as_string())

# ----------------------------------------------------------------------
# --------------------------  APP STATE INIT  --------------------------
# ----------------------------------------------------------------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
if "tickets" not in st.session_state:
    st.session_state.tickets = {}    # ticket_id -> {event, name, qty, verified}
if "event_selected" not in st.session_state:
    st.session_state.event_selected = None
if "mode" not in st.session_state:
    st.session_state.mode = None

EVENTS = {
    "Navratri Pooja": 100,
    "Diwali Dance": 150,
    "Freshers": 200,
    "Ravan Dehan": 120
}

# ----------------------------------------------------------------------
# ---------------------------  STYLING  --------------------------------
# ----------------------------------------------------------------------
st.set_page_config(page_title="Event Ticket Portal", layout="wide")

st.markdown(
    """
    <style>
    body {background-color:#141414;color:white;}
    .event-card {border-radius:15px;padding:30px;margin:20px;
                 background:#222;color:white;text-align:center;}
    .event-button button {background:#E50914;color:white;border:none;
                          padding:12px 25px;font-size:18px;border-radius:8px;
                          margin-top:15px;cursor:pointer;}
    .event-button button:hover {background:#f6121d;}
    .footer {position:fixed;bottom:10px;left:20px;font-size:16px;color:#E50914;}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1 style='text-align:center;color:#E50914;'>Event Ticket Portal</h1>", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# ----------------------------  UI LOGIC  ------------------------------
# ----------------------------------------------------------------------
def show_events():
    st.session_state.mode = None
    cols = st.columns(len(EVENTS))
    for i, (event, capacity) in enumerate(EVENTS.items()):
        with cols[i]:
            with st.container():
                st.markdown(f"<div class='event-card'><h2>{event}</h2></div>", unsafe_allow_html=True)
                if st.button("Select", key=f"select_{event}"):
                    st.session_state.event_selected = event

def show_event_actions(event_name):
    st.markdown(f"<h2 style='text-align:center;color:#E50914;'>{event_name}</h2>", unsafe_allow_html=True)
    if st.session_state.mode is None:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Buy Ticket"):
                st.session_state.mode = "buy"
        with col2:
            if st.button("Verify Ticket"):
                st.session_state.mode = "verify"
        if st.button("⬅ Back"):
            st.session_state.event_selected = None
    else:
        if st.button("⬅ Back"):
            st.session_state.event_selected = None
            st.session_state.mode = None
        if st.session_state.mode == "buy":
            buy_tickets(event_name)
        elif st.session_state.mode == "verify":
            verify_tickets(event_name)

def buy_tickets(event_name):
    st.subheader("Enter Your Details to Buy Ticket")
    name = st.text_input("Name")
    email = st.text_input("Email")
    qty = st.number_input("Number of Tickets (max 10)", min_value=1, max_value=10, value=1)
    capacity = EVENTS[event_name]
    scanned = sum(t["verified"] for t in st.session_state.tickets.values() if t["event"] == event_name)
    remaining = capacity - scanned
    st.write(f"**Tickets Scanned:** {scanned} | **Remaining Capacity:** {remaining}")

    if st.button("Confirm Purchase"):
        if qty > remaining:
            st.error("Not enough capacity.")
            return
        ticket_id = hashlib.sha256(f"{name}{time.time()}".encode()).hexdigest()[:10].upper()
        st.session_state.tickets[ticket_id] = {"event": event_name, "name": name,
                                               "qty": qty, "verified": 0, "email": email}
        st.session_state.blockchain.add_transaction({"ticket_id": ticket_id,
                                                     "event": event_name,
                                                     "quantity": qty,
                                                     "holder": name})
        st.session_state.blockchain.create_block(
            previous_hash=st.session_state.blockchain.last_block["hash"]
        )
        st.success(f"Purchase Successful! Your Ticket ID is: {ticket_id}")
        if email:
            body = (f"Hello {name},\n\n"
                    f"Thank you for purchasing {qty} ticket(s) for {event_name}.\n"
                    f"Your Ticket ID is: {ticket_id}\n\n"
                    f"Please show this ID at entry for verification.\n\n"
                    f"Enjoy the event!\n")
            send_email(email, f"Your {event_name} Ticket", body)

def verify_tickets(event_name):
    st.subheader("Verify Ticket")
    ticket_id = st.text_input("Enter Ticket ID")
    num_entering = st.number_input("Number of people entering now", min_value=1, max_value=10, value=1)
    if st.button("Verify"):
        t = st.session_state.tickets.get(ticket_id)
        if not t or t["event"] != event_name:
            st.error("Invalid Ticket ID.")
            return
        remaining = t["qty"] - t["verified"]
        if remaining <= 0:
            st.error("All tickets for this Ticket ID have already been used.")
            return
        if num_entering > remaining:
            st.error(f"Only {remaining} ticket(s) remaining on this Ticket ID.")
            return
        t["verified"] += num_entering
        st.success(f"Verified {num_entering} guest(s). Remaining on this Ticket ID: {t['qty'] - t['verified']}")
        if t["email"]:
            body = (f"Hello {t['name']},\n\n"
                    f"{num_entering} guest(s) have just entered the venue using your Ticket ID {ticket_id} "
                    f"for {event_name}.\n"
                    f"Tickets used: {t['verified']} of {t['qty']}.\n"
                    f"Remaining: {t['qty'] - t['verified']}.\n\n"
                    f"Thank you!")
            send_email(t["email"], f"{event_name} Ticket Verification Update", body)

# ----------------------------------------------------------------------
# ---------------------------  PAGE FLOW  ------------------------------
# ----------------------------------------------------------------------
if st.session_state.event_selected is None:
    show_events()
else:
    show_event_actions(st.session_state.event_selected)

# ----------------------------------------------------------------------
# ----------------------  BLOCKCHAIN COUNTER  --------------------------
# ----------------------------------------------------------------------
st.markdown(
    f"<div class='footer'>Blocks Created: {len(st.session_state.blockchain.chain)}</div>",
    unsafe_allow_html=True
)
