"""NyayaSathi - Practice Mode Page.

Simulate negotiation with the opposing party (Landlord, Company, Employer)
with realistic excuses, and receive tactical coaching feedback on evidence and tone.
"""

import streamlit as st
from core.database import db_manager
from core.models import CaseFacts
from core.practice import practice_engine
from core.scope import ALLOWED_TOPICS, scope_gate

st.set_page_config(page_title="Practice Mode - NyayaSathi", page_icon="🎭", layout="wide")

st.title("🎭 Practice Mode: Opponent Rehearsal")
st.caption("Rehearse your arguments against a realistic opposing party before calling or meeting them.")

# Session persistence
query_sid = st.query_params.get("session_id")
session_id = query_sid or st.session_state.get("session_id")
if session_id:
    st.session_state.session_id = session_id
    st.query_params["session_id"] = session_id
    st.session_state.case_facts = db_manager.get_or_create_case_facts(session_id)
else:
    if "case_facts" not in st.session_state:
        st.session_state.case_facts = CaseFacts()

facts: CaseFacts = st.session_state.case_facts

# Persona mapping
persona_options = {
    "🏠 Unreasonable Landlord": "landlord",
    "🛒 Evasive E-commerce Manager": "ecommerce",
    "💼 Stubborn Employer / HR": "employer",
}

col_ctrl, col_sim = st.columns([0.8, 1.2], gap="large")

with col_ctrl:
    st.subheader("1. Setup Rehearsal")
    selected_label = st.selectbox("Choose who you want to practice against:", list(persona_options.keys()))
    current_persona = persona_options[selected_label]

    # Initialize roleplay state when persona changes
    if "practice_persona" not in st.session_state or st.session_state.practice_persona != current_persona:
        st.session_state.practice_persona = current_persona
        st.session_state.practice_messages = [
            {"role": "assistant", "content": f"I am ready. Speak to me as your {selected_label.split()[1].lower()}. State your demand."}
        ]
        st.session_state.practice_user_args = []
        st.session_state.practice_feedback = None

    if st.button("🔄 Reset Rehearsal", use_container_width=True):
        st.session_state.practice_messages = [
            {"role": "assistant", "content": f"I am ready. Speak to me as your {selected_label.split()[1].lower()}. State your demand."}
        ]
        st.session_state.practice_user_args = []
        st.session_state.practice_feedback = None
        st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Negotiation Tips")
    st.info(
        "1. **Stay Calm & Factual**: Avoid getting angry or making idle threats.\n"
        "2. **State Specific Dates & Amounts**: Clear numbers show you have records.\n"
        "3. **Ask for Invoices**: If deductions are claimed, ask for written itemized bills.\n"
        "4. **Cite Written Agreements**: Remind them of contractual clauses."
    )

    if st.session_state.practice_user_args:
        if st.button("📊 Evaluate My Arguments & Give Feedback", type="primary", use_container_width=True):
            with st.spinner("Analyzing your negotiation posture and evidence needs..."):
                feedback = practice_engine.evaluate_arguments(
                    persona=current_persona,
                    user_arguments=st.session_state.practice_user_args,
                    facts=facts,
                    language=st.session_state.get("language", "English"),
                )
                st.session_state.practice_feedback = feedback
            st.rerun()

with col_sim:
    st.subheader("2. Rehearsal Chat")

    # Render roleplay history
    for msg in st.session_state.practice_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User input
    user_reply = st.chat_input(f"Argue your case with the {current_persona}...")
    if user_reply:
        reply_text = user_reply.strip()
        if reply_text:
            st.session_state.practice_messages.append({"role": "user", "content": reply_text})
            st.session_state.practice_user_args.append(reply_text)

            # Opponent replies
            with st.spinner("Opponent is replying..."):
                opponent_resp = practice_engine.play_opponent_turn(
                    persona=current_persona,
                    user_argument=reply_text,
                    facts=facts,
                    conversation_history=st.session_state.practice_messages,
                    language=st.session_state.get("language", "English"),
                    session_id=st.session_state.get("session_id"),
                )
            st.session_state.practice_messages.append({"role": "assistant", "content": opponent_resp})
            st.rerun()

# Feedback Display Section below
if st.session_state.practice_feedback:
    fb = st.session_state.practice_feedback
    st.divider()
    st.subheader("🎯 Negotiation Coach Feedback")

    st.write(f"**Overall Assessment:** {fb.user_argument_strength}")

    c1, c2 = st.columns(2)
    with c1:
        st.success("**Key Strengths:**")
        for s in fb.key_strengths:
            st.markdown(f"- {s}")

        st.warning("**Potential Pitfalls & Weak Spots:**")
        for p in fb.potential_pitfalls:
            st.markdown(f"- {p}")

    with c2:
        st.info("**Concrete Evidence You Should Have Ready:**")
        for e in fb.evidence_to_prepare:
            st.markdown(f"- 📁 {e}")

        st.markdown("**Recommended Counter-Phrasing to Use:**")
        st.code(fb.recommended_counter_response, language="markdown")
