import streamlit as st
import uuid
from blockchain import Blockchain
from events_data import events
from PIL import Image
import os
from io import BytesIO
import base64

# Initialize blockchain
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
blockchain = st.session_state.blockchain

# Page config
st.set_page_config(page_title="Event Ticket Portal", layout="wide", page_icon="🎫")
st.markdown("<h1 style='text-align:center;color:#004AAD;'>🎫 Event Ticket Portal</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# CSS for Netflix-style buttons
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
.event-card {
    display: inline-block;
    text-align: center;
    margin: 10px;
}
.event-card img {
    width: 250px;
    height: 140px;
    border-radius: 8px;
    box-shadow: 2px 2px 6px #aaa;
    transition: transform 0.2s;
}
.event-card img:hover {
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# --- Display events as Netflix-style cards ---
st.markdown("<h2 style='color:#004AAD;text-align:center;'>Select Your Event</h2>", unsafe_allow_html=True)
cols = st.columns(4)

if "selected_event" not in st.session_state:
    st.session_state.selected_event = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

for i, (ename, data) in enumerate(events.items()):
    col = cols[i % 4]
    img_path = os.path.join(BASE_DIR, data["image"])
    if not os.path.exists(img_path):
        col.error(f"Image not found: {img_path}")
        continue
    img = Image.open(img_path)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    col.markdown(f"""
    <div class="event-card">
        <img src="data:image/png;base64,{img_str}" />
        <h4 style='margin:5px 0 2px 0;'>{ename}</h4>
        <p style='font-size:12px;margin:2px 0;'>Tickets Scanned: <b>{data['tickets_scanned']}</b></p>
        <p style='font-size:12px;margin:2px 0;'>Remaining Capacity: <b>{data['capacity']}</b></p>
    </div>
    """, unsafe_allow_html=True)

    if col.button(f"Select {ename}", key=f"btn_{i}"):
        st.session_state.selected_event = ename

selected_event = st.session_state.selected_event

# --- Buy Ticket Section ---
if selected_event:
    st.markdown(f"<h2 style='color:#004AAD;text-align:center;'>Selected Event: {selected_event}</h2>", unsafe_allow_html=True)
    st.markdown("### Enter Your Details to Buy Ticket")
    name = st.text_input("Name")
    phone = st.text_input("Phone Number")
    email = st.text_input("Email")
    uid = st.text_input("Unique ID (UID)")

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

            st.success(f"✅ Ticket Purchased Successfully! Your Ticket ID: **{ticket_id}**")

            # Download ticket text file
            ticket_text = f"Event: {selected_event}\nName: {name}\nPhone: {phone}\nEmail: {email}\nUID: {uid}\nTicket ID: {ticket_id}"
            st.download_button(
                label="Download Ticket ID",
                data=ticket_text,
                file_name=f"{selected_event}_ticket_{ticket_id}.txt",
                mime="text/plain"
            )
