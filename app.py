# --- Event Detail Section ---
if st.session_state.view == "event_detail" and st.session_state.selected_event:
    selected_event = st.session_state.selected_event

    st.markdown(f"""
    <h2 style='text-align:center;color:#E50914;font-family:Helvetica, Arial, sans-serif;
               font-size:36px;font-weight:bold;margin-top:20px;text-shadow:1px 1px 3px #000;'>
               {selected_event} Details</h2>
    """, unsafe_allow_html=True)

    # Real-time Counts
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

    # --- Choose Action ---
    action = st.radio("Choose an action", ["Buy Ticket", "Verify Ticket"], horizontal=True)

    if action == "Buy Ticket":
        # Buy Ticket Section
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
                st.experimental_rerun()

    elif action == "Verify Ticket":
        # Verification Section
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(f"""
        <h3 style='text-align:center;color:#E50914;font-family:Helvetica, Arial, sans-serif;
                   font-size:28px;font-weight:bold;margin-top:10px;text-shadow:1px 1px 3px #000;'>
                   Verify Your Ticket</h3>
        """, unsafe_allow_html=True)

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
                                st.error("❌ All tickets under this Ticket ID have already been used")
                            elif num_entering > remaining:
                                st.warning(f"⚠ You can verify a maximum of {remaining} guest(s) at this time")
                            else:
                                txn["scanned_count"] += num_entering
                                events[selected_event]["tickets_scanned"] += num_entering
                                remaining_after = txn["quantity"] - txn["scanned_count"]
                                st.success(f"✅ {num_entering} ticket(s) verified! {remaining_after} remaining under this Ticket ID for {selected_event}")
                            st.experimental_rerun()
                            break
                    if found:
                        break
                if not found:
                    st.error("❌ Ticket ID and Email do not match any record")
