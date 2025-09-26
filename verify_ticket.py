import streamlit as st
import time
# IMPORT FIX: Centralized Blockchain and helper function
from blockchain import Blockchain, get_ticket_status
from events_data import events

# ------------------------ APP STATE AND CONFIG ------------------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
blockchain = st.session_state.blockchain

st.set_page_config(page_title="Ticket Verification", layout="centered", page_icon="✅")

# ------------------------ NETFLIX-THEME STYLING ------------------------
st.markdown("""
<style>
/* Base Dark Theme & Font */
.stApp {
    background-color: #141414;
    color: white;
    font-family: 'Inter', sans-serif;
}
/* Page Header (Netflix Red) */
h1 {
    text-align: center;
    color: #E50914;
    font-size: 3em;
    font-weight: 700;
    letter-spacing: 2px;
    text-shadow: 2px 2px 4px #000000;
}
hr {
    border-top: 2px solid #E50914;
}

/* Streamlit Button Styling (Red and smooth) */
div.stButton > button {
    background-color: #E50914; 
    color: white;
    font-weight: bold;
    padding: 10px 20px;
    border-radius: 6px;
    width: 250px;
    margin: 20px auto;
    display: block;
    cursor: pointer;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    transition: background-color 0.2s, transform 0.2s;
}
div.stButton > button:hover {
    background-color: #f6121d; 
    transform: scale(1.03);
}

/* Inputs */
.stTextInput > div > div > input, .stNumberInput > div > div > input {
    background-color: #333;
    color: white;
    border: 1px solid #555;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

# --- Heading (Page 4 of PDF) ---
st.markdown("<h1>✅ Ticket Verification</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Input fields
st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
event_name = st.selectbox("Select Event", list(events.keys()), help="Select the event you are verifying tickets for.")
# Matches PDF Design: Enter Ticket IP
ticket_id = st.text_input("Enter Ticket ID").upper() 
# Matches PDF Design: No. of People Entering
num_entering = st.number_input("No. of People Entering", min_value=1, value=1, key="verify_num", help="How many people are entering using this ID?")
st.markdown("</div>", unsafe_allow_html=True)

# Verify button
if st.button("Verify Ticket"):
    if not ticket_id:
        st.warning("Please enter a Ticket ID")
    else:
        # 1. Fetch current status by reading the blockchain
        _, _, _, ticket_details, _ = get_ticket_status(blockchain, event_name)
        
        t_status = ticket_details.get(ticket_id)
        
        if not t_status:
            st.error("❌ Invalid Ticket ID for this event.")
            
        else:
            remaining_to_use = t_status["qty"] - t_status["scanned"]
            
            if remaining_to_use <= 0:
                st.error("❌ Ticket has already been fully used.")
                
            elif num_entering > remaining_to_use:
                st.error(f"❌ Only {remaining_to_use} tickets remain for this Ticket ID (Used: {t_status['scanned']}/{t_status['qty']}).")
                
            else:
                # 2. Add a new, immutable VERIFY transaction
                blockchain.add_transaction({
                    "type": "VERIFY", 
                    "ticket_id": ticket_id, 
                    "event": event_name, 
                    "num_entering": num_entering,
                    "verifier": "Venue Gate - Verify App", 
                    "timestamp": time.time()
                })
                
                # 3. Mine a new block
                blockchain.create_block(blockchain.last_block["hash"])
                
                new_remaining = remaining_to_use - num_entering
                st.balloons()
                st.success(f"✅ VERIFIED {num_entering} GUEST(S). Remaining: **{new_remaining}**")
