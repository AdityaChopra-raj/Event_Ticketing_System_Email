import streamlit as st
import uuid
from blockchain import Blockchain
from events_data import events as EVENTS_DATA

# -----------------------
# Streamlit Page Config
# -----------------------
st.set_page_config(
    page_title="🎟 Cultural Event Ticketing Portal",
    layout="wide",
    page_icon="🎟"
)

# -----------------------
# Netflix-inspired CSS
# -----------------------
st.markdown("""
<style>
/* Body and font */
body, .main {
    background-color: #141414;
    color: white;
    font-family: 'Helvetica', 'Arial', sans-serif;
}

/* Buttons */
div.stButton > button {
    background-color:#E50914;
    color:white;
    font-weight:bold;
    border-radius:5px;
    padding:10px 20px;
    transition: transform 0.3s, box-shadow 0.3s;
}
div.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 15px #E50914;
}

/* Event carousel */
.event-row {
    display: flex;
    overflow-x: auto;
    padding: 10px 0;
}
.event-card {
    min-width: 200px;
    margin-right: 20px;
    border-radius: 5px;
    transition: transform 0.3s, box-shadow 0.3s;
}
.event-card:hover {
    transform: scale(1.08);
    box-shadow: 0 0 25px #E50914;
}

/* Poster images */
.event-card img {
    width: 100%;
    aspect-ratio: 2/3;
    border-radius:5px;
    object-fit: cover;
}

/* Event captions */
.event-caption {
    margin-top: 5px;
    font-size: 0.9rem;
    color: #ddd;
}

/* Tabs header */
.css-1vq4p4l {
    color:white;
    font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# Initialise blockchain
# -----------------------
if 'blockchain' not in st.session_state:
    st.session_state.blockchain = Blockchain()
chain = st.session_state.blockchain

# -----------------------
# Role Selector
# -----------------------
role = st.radio(
    "Select Mode:",
    ["Customer Booking", "Gate Attendant"],
    horizontal=True
)

# =========================
# ====== CUSTOMER BOOKING PAGE  ==============
# =========================
if role == "Customer Booking":
    st.title("🎉 Cultural Event Ticketing")

    # Render events in horizontal scrollable row
    st.subheader("Events")
    st.markdown('<div class="event-row">', unsafe_allow_html=True)
    for ename, edata in EVENTS_DATA.items():
        purchased = sum(s['purchased'] for s in chain.get_ticket_status().values() if s['event']==ename)
        remaining = edata["capacity"] - purchased
        card_html = f"""
        <div class="event-card">
            <img src="{edata['image']}" alt="{ename}">
            <h4 style="margin:5px 0 2px 0;">{ename}</h4>
            <p class="event-caption">{edata['time']} – {edata['location']}</p>
            <p class="event-caption">Remaining: {remaining}/{edata['capacity']}</p>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Select an Event to Book / Check-In")
    choice = st.selectbox("Choose an event", list(EVENTS_DATA.keys()))
    ev = EVENTS_DATA[choice]

    st.image(ev["image"], use_column_width=True)
    st.write(f"**Location:** {ev['location']}")
    st.write(f"**Time:** {ev['time']}")
    st.write(ev["description"])
    st.write(f"Capacity: {ev['capacity']}")
    st.write(f"Tickets Sold: {sum(s['purchased'] for s in chain.get_ticket_status().values() if s['event']==choice)}")
    st.write(f"Guests Checked In: {sum(s['checked_in'] for s in chain.get_ticket_status().values() if s['event']==choice)}")

    tab1, tab2 = st.tabs(["Buy Tickets", "Check-In (Attendant)"])

    # ---- Buy Tickets ----
    with tab1:
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        num = st.number_input("Number of tickets", 1, 10, 1)
        if st.button("Purchase"):
            if not name or not email:
                st.error("Name and Email required")
            else:
                sold = sum(s['purchased'] for s in chain.get_ticket_status().values() if s['event']==choice)
                if sold + num > ev["capacity"]:
                    st.error("Not enough capacity!")
                else:
                    with st.spinner("Mining block..."):
                        tid = str(uuid.uuid4())[:8]
                        chain.add_transaction("PURCHASE", choice, tid, email, num)
                        proof = chain.proof_of_work(chain.last_block['proof'])
                        chain.create_block(proof, chain.hash(chain.last_block))
                    st.success(f"✅ Ticket purchased! Ticket ID: {tid} | Block #{chain.last_block['index']}")

    # ---- Check-In ----
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
# ====== GATE ATTENDANT PAGE ======
# =========================
else:
    st.title("🛂 Gate Attendant Verification")
    tid = st.text_input("Ticket ID")
    email_v = st.text_input("Ticket Holder Email")
    guests = st.number_input("Guests entering", 1, 10, 1)
    if st.button("Verify Entry", type="primary"):
        status = chain.get_ticket_status()
        if tid not in status:
            st.error("❌ Ticket ID not found")
        elif status[tid]['email'] != email_v:
            st.error("❌ Email does not match")
        elif status[tid]['checked_in'] + guests > status[tid]['purchased']:
            st.error("❌ Not enough unused entries")
        else:
            with st.spinner("Mining verification block..."):
                chain.add_transaction("VERIFY", status[tid]['event'], tid, email_v, guests)
                proof = chain.proof_of_work(chain.last_block['proof'])
                chain.create_block(proof, chain.hash(chain.last_block))
            st.success(f"✅ Guests verified! Block #{chain.last_block['index']}")
