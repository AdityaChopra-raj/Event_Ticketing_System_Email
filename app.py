import streamlit as st
import uuid
from blockchain import Blockchain
from events_data import events   # contains the events dictionary

# -----------------------
# Streamlit page config
# -----------------------
st.set_page_config(
    page_title="🎟️ Event Ticketing Portal",
    page_icon="🎟️",
    layout="wide"
)

# -----------------------
# Session state: single shared blockchain ledger
# -----------------------
if 'blockchain' not in st.session_state:
    st.session_state.blockchain = Blockchain()

chain = st.session_state.blockchain

# -----------------------
# Role Selector
# -----------------------
role = st.radio(
    "Select Mode:",
    ["Customer Booking", "Gate Attendant"],
    horizontal=True
)

# ======================================================
# ===============  CUSTOMER BOOKING PAGE  ==============
# ======================================================
if role == "Customer Booking":
    st.title("🎉 Cultural Event Ticketing")

    event_names = list(events.keys())
    choice = st.selectbox("Choose an event", event_names)

    ev = events[choice]
    st.image(ev["image"], use_column_width=True)
    st.subheader(choice)
    st.write(f"**Location:** {ev['location']}")
    st.write(f"**Time:** {ev['time']}")
    st.write(ev["description"])

    st.markdown("---")

    st.subheader("Book Your Ticket")
    email = st.text_input("Enter your Email")
    num_guests = st.number_input("Number of tickets", 1, 10, 1)

    if st.button("Generate Ticket"):
        if email.strip() == "":
            st.error("Please enter a valid email address.")
        else:
            ticket_id = str(uuid.uuid4())[:8]
            chain.add_transaction("BOOK", choice, ticket_id, email, num_guests)
            proof = chain.proof_of_work(chain.last_block['proof'])
            chain.create_block(proof, chain.hash(chain.last_block))

            st.success("✅ Ticket Generated!")
            st.info(f"🎟️ **Ticket ID:** {ticket_id}")
            st.write("Please keep this Ticket ID and your email safe for entry.")

    st.markdown("---")
    st.subheader("Event Stats")

    status = chain.get_ticket_status()
    for e in event_names:
        purchased = sum(v['purchased'] for k, v in status.items() if v['event'] == e)
        checked_in = sum(v['checked_in'] for k, v in status.items() if v['event'] == e)
        st.write(f"**{e}** – Tickets Sold: {purchased} | Checked In: {checked_in}")

# ======================================================
# ==============  GATE ATTENDANT PAGE  =================
# ======================================================
else:
    st.title("🛂 Gate Attendant Verification")

    tid = st.text_input("Ticket ID")
    email_v = st.text_input("Ticket Holder Email")
    guests = st.number_input("Guests entering", 1, 10, 1)

    if st.button("Verify Entry", type="primary"):
        status = chain.get_ticket_status()
        if tid not in status:
            st.error("❌ Ticket ID not found")
        elif status[tid]['email'] != email_v:
            st.error("❌ Email does not match")
        elif status[tid]['checked_in'] + guests > status[tid]['purchased']:
            st.error("❌ Not enough unused entries")
        else:
            with st.spinner("Mining verification block..."):
                chain.add_transaction("VERIFY", status[tid]['event'], tid, email_v, guests)
                proof = chain.proof_of_work(chain.last_block['proof'])
                chain.create_block(proof, chain.hash(chain.last_block))
            st.success(f"✅ Guests verified! Block #{chain.last_block['index']}")
