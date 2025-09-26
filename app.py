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

# --- CSS for Netflix-style layout and centered buttons ---
st.markdown("""
<style>
div.stButton > button {
    background-color: #E50914;
    color: white;
    font-weight: bold;
    padding: 10px 16px;
    border-radius: 6px;
    width: 200px;
    margin: 10px auto;
    display: block;
    cursor: pointer;
    font-family: Arial, sans-serif;
    font-size: 16px;
    box-shadow: 2px 2px 8px #aaa;
    transition: transform 0.3s, opacity 0.5s;
    text-align: center;
    line-height: 1.5;
}
div.stButton > button:hover {
    transform: scale(1.05);
}
.event-card {
    display: inline-block;
    text-align: center;
    margin: 15px;
    width: 250px;
    vertical-align: top;
    transition: transform 0.5s, opacity 0.5s;
}
.event-card img {
    width: 100%;
    height: 140px;
    border-radius: 8px;
    box-shadow: 2px 2px 8px #aaa;
    transition: transform 0.5s;
}
.event-card img:hover {
    transform: scale(1.05);
}
.event-card h4 {
    font-size: 18px;
    font-weight: bold;
    color: white;
    margin: 8px 0 4px 0;
    word-wrap: break-word;
}
</style>
""", unsafe_allow_html=True)

# --- Netflix-themed Headings ---
st.markdown("""
<h1 style='text-align:center;color:#E50914;font-family:Helvetica, Arial, sans-serif;
           font-size:48px;font-weight:bold;letter-spacing:2px;margin-bottom:10px;
           text-shadow: 2px 2px 4px #000;'>🎬 Event Ticket Portal</h1>
""", unsafe_allow_html=True)
st.markdown("""
<h2 style='text-align:center;color:white;background-color:#141414;
           font-family:Helvetica, Arial, sans-serif;font-size:32px;font-weight:bold;
           padding:10px 0;border-radius:8px;letter-spacing:1px;margin-bottom:20px;
           text-shadow:1px 1px 3px #000;'>Select Your Event</h2>
""", unsafe_allow_html=True)

# --- Session State ---
if "view" not in st.session_state:
    st.session_state.view = "events"
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None
if "action" not in st.session_state:
    st.session_state.action = "Buy Ticket"

# --- Back Button ---
if st.session_state.view == "event_detail":
    if st.button("← Back to Events"):
        st.session_state.view = "events"
        st.session_state.selected_event = None
        st.experimental_rerun()

# --- Display Event Cards ---
st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
cols = st.columns(4)
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

    # Expand selected, fade others
    if st.session_state.view == "event_detail" and st.session_state.selected_event == ename:
        style = "transform: scale(1.6); z-index:10; transition: all 0.5s; margin:0 auto;"
        opacity = 1
        show_heading_button = False
    elif st.session_state.view == "event_detail":
        style = "transform: scale(0.8); opacity:0; transition: all 0.5s;"
        opacity = 0
        show_heading_button = False
    else:
        style = "transform: scale(1); transition: all 0.5s;"
        opacity = 1
        show_heading_button = True

    card_html = f'<div class="event-card" style="{style}; opacity:{opacity};">'
    card_html += f'<img src="data:image/png;base64,{img_str}" />'
    if show_heading_button:
        card_html += f'<h4>{ename}</h4>'
    card_html += '</div>'
    col.markdown(card_html, unsafe_allow_html=True)

    # Buttons under card
    if show_heading_button:
        if st.session_state.view == "events":
            if col.button(f"Select {ename}", key=f"btn_{i}"):
                st.session_state.selected_event = ename
                st.session_state.view = "event_detail"
                st.experimental_rerun()

st.markdown("</div>", unsafe_allow_html=True)

# --- Event Detail Section ---
if st.session_state.view == "event_detail" and st.session_state.selected_event:
    selected_event = st.session_state.selected_event

    st.markdown(f"<h2 style='text-align:center;color:#E50914;font-family:Helvetica, Arial, sans-serif; \
               font-size:36px;font-weight:bold;margin-top:20px;text-shadow:1px 1px 3px #000;'>\
               {selected_event} Details</h2>", unsafe_allow_html=True)

    st.markdown(f"<div style='text-align:center; margin-bottom:15px;'>\
        <span style='color:#E50914; font-weight:bold; margin-right:20px;'>Tickets Scanned: {events[selected_event]['tickets_scanned']}</span>\
        <span style='color:#E50914; font-weight:bold;'>Remaining Capacity: {events[selected_event]['capacity']}</span></div>", unsafe_allow_html=True)

    # --- Action Choice ---
    action = st.radio("Choose an action", ["Buy Ticket", "Verify Ticket"], horizontal=True)
    st.session_state.action = action

    # --- Buy Ticket ---
    if st.session_state.action == "Buy Ticket":
        st.markdown("### Enter Your Details to Buy Ticket")
        name = st.text_input("Name", key="name")
        phone = st.text_input("Phone Number", key="phone")
        email = st.text_input("Email", key="email")
        uid = st.text_input("Unique ID (UID)", key="uid")
        num_tickets = st.number_input("Number of Tickets (Max 10)", min_value=1, max_value=10, step=1, key="num_tickets")

        if st.button("Confirm Purchase", key="confirm_purchase"):
            if not name or not phone or not email or not uid:
                st.warning("Please fill all fields")
            elif events[selected_event]["capacity"] < num_tickets:
                st.error(f"Sorry, only {events[selected_event]['capacity']} tickets left!")
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
                    quantity=num_tickets,
                    scanned_count=0
                )
                blockchain.mine_block()
                events[selected_event]["capacity"] -= num_tickets

                st.success(f"✅ {num_tickets} Ticket(s) Purchased! Ticket ID: **{ticket_id}**")

                ticket_text = f"Event: {selected_event}\nName: {name}\nPhone: {phone}\nEmail: {email}\nUID: {uid}\nTicket ID: {ticket_id}\nQuantity: {num_tickets}"
                st.download_button(label="Download Ticket ID", data=ticket_text,
                                   file_name=f"{selected_event}_ticket_{ticket_id}.txt", mime="text/plain")
                st.experimental_rerun()

    # --- Verify Ticket ---
    elif st.session_state.action == "Verify Ticket":
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align:center;color:#E50914;font-family:Helvetica, Arial, sans-serif;\
                   font-size:28px;font-weight:bold;margin-top:10px;text-shadow:1px 1px 3px #000;'>Verify Your Ticket</h3>", unsafe_allow_html=True)

        verify_email = st.text_input("Enter Email for Verification", key="verify_email")
        verify_ticket_id = st.text_input("Enter Ticket ID", key="verify_ticket_id")
        num_entering = st.number_input("Number of Guests Entering", min_value=1, max_value=10, step=1, key="num_entering")

        if st.button("Verify Ticket", key="verify_ticket"):
            if not verify_email or not verify_ticket_id:
                st.warning("Please fill all fields")
            else:
                found = False
                for block in blockchain.chain:
                    for txn in block["transactions"]:
                        if (txn["ticket_id"] == verify_ticket_id and
                            txn["event_name"] == selected_event and
                            txn["customer_email"] == verify_email):

                            found = True
                            remaining = txn["quantity"] - txn["scanned_count"]

                            if remaining == 0:
                                st.error("❌ All tickets for this Ticket ID have already been used")
                            elif num_entering > remaining:
                                st.warning(f"⚠ You can verify a maximum of {remaining} guest(s) at this time")
                            else:
                                txn["scanned_count"] += num_entering
                                events[selected_event]["tickets_scanned"] += num_entering
                                remaining_after = txn["quantity"] - txn["sc
