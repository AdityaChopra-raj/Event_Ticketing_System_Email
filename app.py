import streamlit as st
import uuid
from blockchain import Blockchain
from events_data import events

# Initialize blockchain
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
blockchain = st.session_state.blockchain

st.set_page_config(page_title="Event Ticket Portal", layout="wide", page_icon="🎫")
st.markdown("<h1 style='text-align:center;color:#004AAD;'>🎫 Event Ticket Portal</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Event selection
selected_event = st.selectbox("Select Event", list(events.keys()))
st.markdown(f"**Tickets Scanned:** {events[selected_event]['tickets_scanned']}  |  **Remaining Capacity:** {events[selected_event]['capacity']}")

st.markdown("### Enter Your Details to Buy Ticket")
name = st.text_input("Name")
phone = st.text_input("Phone Number")
email = st.text_input("Email")
uid = st.text_input("Unique ID (UID)")

if st.button("Confirm Purchase"):
    if not name or not phone or not email or not uid:
        st.warning("Please fill all fields")
    elif events[selected_event]["capacity"] <= 0:
        st.error("Sorry, event is full!")
    else:
        # Generate Ticket ID
        ticket_id = str(uuid.uuid4())[:8]

        # Add ticket to blockchain
        blockchain.add_transaction(
            sender="system",
            receiver=email,
            ticket_id=ticket_id,
            event_name=selected_event,
            customer_name=name,
            customer_email=email,
            phone=phone,
            uid=uid,
            scanned=False
        )
        blockchain.mine_block()

        # Update event capacity
        events[selected_event]["capacity"] -= 1

        st.success(f"✅ Ticket Purchased Successfully! Your Ticket ID: **{ticket_id}**")

        # Download Ticket ID as text file
        ticket_text = f"Event: {selected_event}\nName: {name}\nPhone: {phone}\nEmail: {email}\nUID: {uid}\nTicket ID: {ticket_id}"
        st.download_button(
            label="Download Ticket ID",
            data=ticket_text,
            file_name=f"{selected_event}_ticket_{ticket_id}.txt",
            mime="text/plain"
        )
