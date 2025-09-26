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

# --- CSS for Netflix style ---
st.markdown("""
<style>
div.stButton > button {
    background-color: #E50914;
    color: white;
    font-weight: bold;
    padding: 8px 12px;
    border-radius: 5px;
    width: 250px;
    margin: 10px auto;
    display: block;
    cursor: pointer;
    font-family: Arial, sans-serif;
    box-shadow: 2px 2px 6px #aaa;
    transition: transform 0.3s, opacity 0.5s;
}
div.stButton > button:hover {
    transform: scale(1.05);
}
.event-card {
    display: inline-block;
    text-align: center;
    margin: 10px;
    transition: transform 0.5s, opacity 0.5s;
}
.event-card img {
    width: 250px;
    height: 140px;
    border-radius: 8px;
    box-shadow: 2px 2px 6px #aaa;
    transition: transform 0.3s;
}
.event-card img:hover {
    transform: scale(1.05);
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
if "show_verification" not in st.session_state:
    st.session_state.show_verification = False
if "verify_event" not in st.session_state:
    st.session_state.verify_event = None

# --- Back Button ---
if st.session_state.view == "event_detail":
    if st.button("← Back to Events"):
        st.session_state.view = "events"
        st.session_state.selected_event = None
        st.session_state.show_verification = False
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

    # Style for selected/other cards
    if st.session_state.view == "event_detail" and st.session_state.selected_event == ename:
        style = "transform: scale(1.5); z-index: 10; transition: all 0.5s; margin:0 auto;"
        opacity = 1
    elif st.session_state.view == "event_detail":
        style = "transform: scale(0.8); opacity:0.2; transition: all 0.5s;"
        opacity = 0.2
    else:
        style = "transform: scale(1); transition: all 0.5s;"
        opacity = 1

    col.markdown(f"""
    <div class="event-card" style="{style}; opacity:{opacity};">
        <img src="data:image/png;base64,{img_str}" />
        <h4 style='margin:5px 0 2px 0;color:white;'>{ename}</h4>
        <p style='font-size:12px;margin:2px 0;color:#E50914;'>Tickets Scanned: <b>{data['tickets_scanned']}</b></p>
        <p style='font-size:12px;margin:2px 0;color:#E50914;'>Remaining Capacity: <b>{data['capacity']}</b></p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.view == "events":
        if col.button(f"Select {ename}", key=f"btn_{i}"):
            st.session_state.selected_event = ename
            st.session_state.view = "event_detail"
            st.experimental_rerun()

    if st.session_state.view == "event_detail" and st.session_state.selected_event == ename:
        if col.button(f"Verify Ticket - {ename}", key=f"verify_{i}"):
            st.session_state.show_verification = True
            st.session_state.verify_event = ename
            st.experimental_rerun()

st.markdown("</div>", unsafe_allow_html=True)

# --- Event Detail Section ---
if st.session_state.view == "event_detail" and st.session_state.selected_event:
    selected_event = st.session_state.selected_event

    st.markdown(f"""
    <h2 style='text-align:center;color:#E50914;font-family:Helvetica, Arial, sans-serif;
               font-size:36px;font-weight:bold;margin-top:20px;text-shadow:1px 1px 3px #000;'>
               {selected_event} Details</h2>
    """, unsafe_allow_html=True)

    # --- Show real-time counts ---
    st.markdown(f"""
    <div style='text-align:center; margin-bottom:15px;'>
        <span style='color:#E50914; font-weight:bold; margin-right:20px;'>
            Tickets Scanned: {events[selected_event]['tickets_scanned']}
        </span>
        <span style='color:#E50914; font-weight:bold;'>
            Remaining Capacity: {events[selected_event]['capacity']}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # --- Buy Ticket ---
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

            st.success(f"✅ {num_tickets} Ticket(s) Purchased Successfully! Your Ticket ID: **{ticket_id}**")

            ticket_text = f"Event: {selected_event}\nName: {name}\nPhone: {phone}\nEmail: {email}\nUID: {uid}\nTicket ID: {ticket_id}\nQuantity: {num_tickets}"
            st.download_button(
                label="Download Ticket ID",
                data=ticket_text,
                file_name=f"{selected_event}_ticket_{ticket_id}.txt",
                mime="text/plain"
            )
            st.experimental_rerun()  # Refresh counts

# --- Verification Section ---
if st.session_state.show_verification:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"""
    <h2 style='text-align:center;color:#E50914;font-family:Helvetica, Arial, sans-serif;
               font-size:36px;font-weight:bold;margin-top:20px;text-shadow:1px 1px 3px #000;'>
               Verify Your Ticket</h2>
    """, unsafe_allow_html=True)

    verify_event = st.selectbox("Select Event for Verification",
                                list(events.keys()),
                                index=list(events.keys()).index(st.session_state.get("verify_event", list(events.keys())[0])))
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
                        txn["event_name"] == verify_event and
                        txn["customer_email"] == verify_email):

                        found = True
                        remaining = txn["quantity"] - txn["scanned_count"]

                        if remaining == 0:
                            st.error("❌ All tickets under this Ticket ID have already been used")
                        elif num_entering > remaining:
                            st.warning(f"⚠ You can verify a maximum of {remaining} guest(s) at this time")
                        else:
                            txn["scanned_count"] += num_entering
                            events[verify_event]["tickets_scanned"] += num_entering
                            remaining_after = txn["quantity"] - txn["scanned_count"]
                            st.success(f"✅ {num_entering} ticket(s) verified! {remaining_after} remaining under this Ticket ID for {verify_event}")
                        st.experimental_rerun()  # Refresh counts
                        break
                if found:
                    break
            if not found:
                st.error("❌ Ticket ID and Email do not match any record")
