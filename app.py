import streamlit as st
import uuid
from blockchain import Blockchain
from events_data import EVENTS_DATA

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Secure Cultural Event Ticketing Portal",
    layout="wide",
    page_icon="🎟"
)

# --- Custom Netflix-Red Dark Theme styling ---
st.markdown("""
<style>
body {background-color: #141414; color: white;}
div.stButton > button {
    background-color:#E50914; color:white; border-radius:8px;
}
div.stButton > button:hover {
    transform: scale(1.05); box-shadow:0 0 10px #E50914;
}
</style>
""", unsafe_allow_html=True)

# --- Initialise blockchain in session state ---
if 'blockchain' not in st.session_state:
    st.session_state.blockchain = Blockchain()
chain = st.session_state.blockchain

# --- Sidebar navigation ---
st.sidebar.title("Navigation")
view = st.sidebar.radio("Go to", ["Home", "Admin Audit"])

# =========================
# ====== HOME VIEW ========
# =========================
if view == "Home":
    st.title("🎟 Cultural Events")
    cols = st.columns(3)

    for i, (ename, edata) in enumerate(EVENTS_DATA.items()):
        with cols[i % 3]:
            st.image(edata["image"], use_column_width=True)
            st.subheader(ename)
            st.caption(f"{edata['time']} – {edata['location']}")

            # --- real-time tickets remaining ---
            status = chain.get_ticket_status()
            sold = sum(s['purchased'] for s in status.values() if s['event'] == ename)
            checked = sum(s['checked_in'] for s in status.values() if s['event'] == ename)
            remaining = edata["capacity"] - sold
            st.write(f"**Remaining:** {remaining} / {edata['capacity']}")

            if st.button(f"View {ename}", key=ename):
                st.session_state.selected_event = ename

    # --- Event detail view (when selected) ---
    if "selected_event" in st.session_state:
        ename = st.session_state.selected_event
        edata = EVENTS_DATA[ename]
        st.header(ename)
        st.write(edata["description"])
        st.write(f"Capacity: {edata['capacity']}")
        st.write(f"Tickets Sold: {sum(s['purchased'] for s in chain.get_ticket_status().values() if s['event']==ename)}")
        st.write(f"Guests Checked In: {sum(s['checked_in'] for s in chain.get_ticket_status().values() if s['event']==ename)}")

        tab1, tab2 = st.tabs(["Buy Tickets", "Check-In (Attendant)"])

        # ---- Purchase Tab ----
        with tab1:
            name = st.text_input("Your Name")
            email = st.text_input("Your Email")
            num = st.number_input("Number of tickets", 1, 10, 1)
            if st.button("Purchase"):
                if not name or not email:
                    st.error("Name and Email required")
                else:
                    sold = sum(s['purchased'] for s in chain.get_ticket_status().values() if s['event']==ename)
                    if sold + num > edata["capacity"]:
                        st.error("Not enough capacity!")
                    else:
                        with st.spinner("Mining block..."):
                            tid = str(uuid.uuid4())[:8]
                            chain.add_transaction("PURCHASE", ename, tid, email, num)
                            proof = chain.proof_of_work(chain.last_block['proof'])
                            chain.create_block(proof, chain.hash(chain.last_block))
                        st.success(f"✅ Ticket purchased! Ticket ID: {tid} | Block #{chain.last_block['index']}")

        # ---- Verification Tab ----
        with tab2:
            tid = st.text_input("Ticket ID")
            email_v = st.text_input("Ticket Holder Email")
            guests = st.number_input("Guests entering", 1, 10, 1)
            if st.button("Verify Entry"):
                status = chain.get_ticket_status()
                if tid not in status:
                    st.error("Ticket ID not found")
                elif status[tid]['email'] != email_v:
                    st.error("Email does not match")
                elif status[tid]['checked_in'] + guests > status[tid]['purchased']:
                    st.error("Not enough unused entries")
                else:
                    with st.spinner("Mining verification block..."):
                        chain.add_transaction("VERIFY", status[tid]['event'], tid, email_v, guests)
                        proof = chain.proof_of_work(chain.last_block['proof'])
                        chain.create_block(proof, chain.hash(chain.last_block))
                    st.success(f"✅ Guests verified! Block #{chain.last_block['index']}")

# =========================
# ===== ADMIN AUDIT =======
# =========================
else:
    st.title("🔐 Admin Audit View")
    for block in chain.chain:
        st.markdown(f"### Block {block['index']}")
        st.write({
            "timestamp": block['timestamp'],
            "proof": block['proof'],
            "previous_hash": block['previous_hash'],
            "hash": chain.hash(block)
        })
        st.table(block['transactions'])
