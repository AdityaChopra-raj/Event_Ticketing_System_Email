import streamlit as st
from blockchain import Blockchain
from events_data import events

# --- Initialize blockchain ---
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
blockchain = st.session_state.blockchain

st.set_page_config(page_title="Ticket Verification", layout="centered", page_icon="✅")
st.markdown("<h1 style='text-align:center;color:#004AAD;'>✅ Ticket Verification Portal</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# --- Input Fields ---
event_name = st.selectbox("Select Event", list(events.keys()))
email = st.text_input("Enter Email")
ticket_id = st.text_input("Enter Ticket ID")

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
                        events[event_name]["capacity"] -= 1
                        st.success(f"✅ Ticket Verified! Welcome to {event_name}")
                    break
            if found:
                break
        if not found:
            st.error("❌ Ticket ID and Email do not match any record")
