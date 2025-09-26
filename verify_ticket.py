import streamlit as st
import time
# Import the centralized Blockchain class
from blockchain import Blockchain
from events_data import events
# Import helper to read ticket status from the chain
from app import get_ticket_status 

# Initialize blockchain (Requires state sharing with app.py for proper function)
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
ticket_id = st.text_input("Enter Ticket ID").upper()
num_entering = st.number_input("Number of people entering", min_value=1, value=1, key="verify_num")
st.markdown("</div>", unsafe_allow_html=True)

# Verify button
if st.button("Verify Ticket"):
    if not ticket_id:
        st.warning("Please enter a Ticket ID")
    else:
        # Fetch current status from the blockchain (re-reads the entire chain)
        _, _, _, ticket_details = get_ticket_status(event_name)
        
        t_status = ticket_details.get(ticket_id)
        
        # Check if the ticket ID exists for this event
        if not t_status:
            st.error("❌ Ticket ID does not match any record for this event.")
            
        elif t_status["qty"] <= 0:
            st.error("❌ Ticket ID found but has no purchase quantity.")

        else:
            remaining_to_use = t_status["qty"] - t_status["scanned"]
            
            if remaining_to_use <= 0:
                st.error("❌ Ticket has already been fully used.")
                
            elif num_entering > remaining_to_use:
                st.error(f"❌ Only {remaining_to_use} tickets remain for this Ticket ID (Used: {t_status['scanned']}/{t_status['qty']}).")
                
            else:
                # CRITICAL FIX: Add a new, immutable VERIFY transaction
                blockchain.add_transaction({
                    "type": "VERIFY", 
                    "ticket_id": ticket_id, 
                    "event": event_name, 
                    "num_entering": num_entering,
                    "verifier": "Venue Gate - Verify App", 
                    "timestamp": time.time()
                })
                
                # Mine a new block
                blockchain.create_block(blockchain.last_block["hash"])
                
                new_remaining = remaining_to_use - num_entering
                st.success(f"✅ Verified {num_entering} guest(s). Remaining: {new_remaining}")
                
# ARCHITECTURAL NOTE: This script still depends on the main app.py initializing
# and updating the blockchain in a shared state (e.g., a single multi-page app)
# for the verification to be meaningful.
