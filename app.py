import streamlit as st
import uuid
from blockchain import Blockchain
from events_data import events
from PIL import Image
import os
from io import BytesIO
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ---------------------- SMTP CONFIG ----------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]

# ---------------------- EMAIL FUNCTION ----------------------
def send_ticket_email(to_email, ticket_id, event_name, num_tickets, customer_name="", action="purchase", num_verified=0, remaining=0):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    if action == "purchase":
        msg['Subject'] = f"🎫 Your Ticket for {event_name}"
        body = f"""
        <html>
        <body>
        <h2 style="color:#E50914;">Hello {customer_name},</h2>
        <p>Thank you for purchasing tickets for <b>{event_name}</b>!</p>
        <p><b>Ticket ID:</b> {ticket_id}</p>
        <p><b>Number of tickets:</b> {num_tickets}</p>
        <p>Keep this Ticket ID safe. You will need it to verify entry at the event.</p>
        <p>We look forward to seeing you!</p>
        <hr>
        <p style="font-size:12px;color:gray;">This is an automated message from Event Ticket Portal.</p>
        </body>
        </html>
        """
    elif action == "verify":
        msg['Subject'] = f"✅ Ticket Verification Update for {event_name}"
        body = f"""
        <html>
        <body>
        <h2 style="color:#E50914;">Hello {customer_name},</h2>
        <p>Your Ticket ID <b>{ticket_id}</b> for <b>{event_name}</b> has been used for entry.</p>
        <p><b>Number of tickets verified:</b> {num_verified}</p>
        <p><b>Remaining tickets under this Ticket ID:</b> {remaining}</p>
        <p>Thank you for attending, and enjoy the event!</p>
        <hr>
        <p style="font-size:12px;color:gray;">This is an automated message from Event Ticket Portal.</p>
        </body>
        </html>
        """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

# ---------------------- SESSION STATE ----------------------
if "view" not in st.session_state:
    st.session_state.view = "events"
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None
if "action" not in st.session_state:
    st.session_state.action = "Buy Ticket"
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
blockchain = st.session_state.blockchain

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Event Ticket Portal", layout="wide", page_icon="🎫")

# ---------------------- CSS ----------------------
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

# ---------------------- HEADINGS ----------------------
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

# ---------------------- BACK BUTTON ----------------------
if st.session_state.view == "event_detail":
    if st.button("← Back to Events"):
        st.session_state.view = "events"
        st.session_state.selected_event = None

# ---------------------- EVENT CARDS ----------------------
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

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------- EVENT DETAIL ----------------------
if st.session_state.view == "event_detail" and st.session_state.selected_event:
    selected_event = st.session_state.selected_event

    st.markdown(f"<h2 style='text-align:center;color:#E50914;font-family:Helvetica, Arial, sans-serif; \
               font-size:36px;font-weight:bold;margin-top:20px;text-shadow:1px 1px 3px #000;'>\
               {selected_event} Details</h2>", unsafe_allow_html=True)

    st.markdown(f"<div style='text-align:center; margin-bottom:15px;'>\
        <span style='color:#E50914; font-weight:bold; margin-right:20px;'>Tickets Scanned: {events[selected_event]['tickets_scanned']}</span>\
        <span style='color:#E50914; font-weight:bold;'>Remaining Capacity: {events[selected_event]['capacity']}</span></div>", unsafe_allow_html=True)

    # ---------------------- ACTION CHOICE ----------------------
    action = st.radio("Choose an action", ["Buy Ticket", "Verify Ticket"], horizontal=True)
    st.session_state.action = action
