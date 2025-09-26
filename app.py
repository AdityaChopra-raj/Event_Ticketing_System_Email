import os
import streamlit as st
from blockchain import Blockchain
from events_data import events
from PIL import Image
import uuid
from io import BytesIO
import base64

# --- Initialize blockchain ---
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
blockchain = st.session_state.blockchain

# --- Set base directory ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Streamlit page config ---
st.set_page_config(page_title="Event Ticket Portal", layout="wide", page_icon="🎫")

# --- Header ---
st.markdown("<h1 style='text-align:center;color:#004AAD;'>🎫 Event Ticket Portal</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# --- CSS for Netflix-style buttons ---
st.markdown("""
<style>
div.stButton > button {
    background-color: #E50914;
    color: white;
    font-weight: bold;
    padding: 8px 12px;
    border-radius: 5px;
    width: 250px;
    margin: 5px auto 0 auto;
    display: block;
    cursor: pointer;
    font-family: Arial, sans-serif;
    box-shadow: 2px 2px 6px #aaa;
    transition: transform 0.2s;
}
div.stButton > button:hover {
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# --- Event Selection ---
st.markdown("<h2 style='color:#004AAD;'>Select Your Event</h2>", unsafe_allow_html=True)

cards_per_row = 4
cols = st.columns(cards_per_row)

# Persist selected event
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None

for i, (ename, data) in enumerate(events.items()):
    col = cols[i % cards_per_row]
    img_path = os.path.join(BASE_DIR, data["image"])
    if not os.path.exists(img_path):
        col.error(f"Image not found: {img_path}")
        continue

    img = Image.open(img_path)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # Display image
    col.markdown(f"""
    <div style="text-align:center; margin-bottom:10px;">
        <img src="data:image/png;base64,{img_str}" 
            style="width:250px; display:block; margin:0 auto; border-radius:5px;"/>
    </div>
    """, unsafe_allow_html=True)

    # Event selection button
    if col.button(ename, key=f"btn_{i}"):
        st.session_state.selected_event = ename

    # Stats
    col.markdown(f"""
    <div style='text-align:center;'>
        <p style='font-size:12px;margin:2px 0;'>Tickets Scanned: <b>{data['tickets_scanned']}</b></p>
        <p style='font-size:12px;margin:2px 0;'>Remaining Capacity: <b>{data['capacity']}</b></p>
    </div>
    """, unsafe_allow_html=True)

selected_event = st.session_state.selected_event

# --- Buy Ticket Section ---
if selected_event:
    st.markdown(f"<h2 style='color:#004AAD;'>Selected Event: {selected_event}</h2>", unsafe_allow_html=True)
    st.markdown("### Enter Your Details to Buy Ticket")

    name = st.text_input("Name", key="name_input")
    phone = st.text_input("Phone Number", key="phone_input")
    email = st.text_input("Email", key="email_input")
    uid = st.text_input("Unique ID (UID)", key="uid_input")

    if st.button("Confirm Purchase", key="confirm_purchase"):
        if not name or not phone or not email or not uid:
            st.warning("Please fill all fields")
        elif events[selected_event]["capacity"] <= 0:
            st.error("Sorry, event is full!")
        else:
            ticket_id = str(uuid.uuid4())[:8]

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
            events[selected_event]["capacity"] -= 1

            # TODO: integrate email sending function
            # send_email(email, ticket_id, selected_event)

            st.success(f"✅ Ticket Purchased Successfully! Ticket ID sent to {email}")
