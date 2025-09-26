import streamlit as st
from blockchain import Blockchain
from events_data import events

# Initialize blockchain
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
blockchain = st.session_state.blockchain

# Page config
st.set_page_config(page_title="Ticket Verification", layout="centered", page_icon="✅")

# --- Netflix-themed Heading ---
st.markdown("""
<h1 style='text-align:center;
           color:#E50914;
           font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
           font-size:48px;
           font-weight:bold;
           letter-spacing:2px;
           margin-bottom:10px;
           text-shadow: 2px 2px 4px #000000;'>
✅ Ticket Verification
</h1>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# CSS for Netflix-style button
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
    transition: transform 0.2s;
}
div.stButton > button:hover {
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# Centered input fields
st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
event_name = st.selectbox("Select Event", list(events.keys()))
email = st.text_input("Enter Email")
ticket_id = st.text_input("Enter Ticket ID")
st.markdown("</div>", unsafe_allow_html=True)

# Verify button
if st.button("Verify Ticket"):
    if not email or not ticket_id:
        st.warning("Please fill all fields")
    else:
        found = False
        for block in blockchain.chain:
            for txn in block["transactions"]:
                if (txn["ticket_id"] == ticket_id and
                    txn["event_name"] == event_name and
                    txn["customer_email"] == email):
                    
                    found = True
                    if txn["scanned"]:
                        st.error("❌ Ticket has already been used")
                    else:
                        txn["scanned"] = True
                        events[event_name]["tickets_scanned"] += 1
                        st.success(f"✅ Ticket Verified! Welcome to {event_name}")
                    break
            if found:
                break
        if not found:
            st.error("❌ Ticket ID and Email do not match any record")
