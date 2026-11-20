"""NyayaSathi - AI Legal Helper for Ordinary People in India.

Streamlit frontend supporting multi-lingual conversational intake (text & voice),
live editable case fact sheet, grounded legal options, and strict safety hard-gates.
Restricted exclusively to Tenancy, Consumer Disputes, and Employment/Wages.
"""

from datetime import datetime
import uuid
import streamlit as st

from core.case_builder import SUPPORTED_LANGUAGES, case_builder, detect_language_simple
from core.config import config
from core.corpus import corpus_db
from core.database import db_manager
from core.llm import llm_client
from core.models import CaseFacts, ConfidenceLevel, StructuredLegalAdvice
from core.scope import ALLOWED_TOPICS, scope_gate
from core.voice import voice_adapter

# Page Configuration
st.set_page_config(
    page_title="NyayaSathi - AI Legal Helper",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for high readability and mobile responsiveness
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1B365D;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .disclaimer-banner {
        background-color: #FEF3C7;
        border-left: 5px solid #F59E0B;
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
        color: #92400E;
        border-radius: 4px;
        margin-bottom: 1.2rem;
    }
    .key-missing-banner {
        background-color: #FEE2E2;
        border-left: 5px solid #EF4444;
        padding: 0.85rem 1rem;
        font-size: 0.95rem;
        color: #991B1B;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
    .stButton>button {
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# Session Initialization & URL Persistence (st.query_params)
# -------------------------------------------------------------
query_sid = st.query_params.get("session_id")
if query_sid and db_manager.get_session(query_sid):
    session_id = query_sid
elif "session_id" in st.session_state and db_manager.get_session(st.session_state.session_id):
    session_id = st.session_state.session_id
else:
    session_id = str(uuid.uuid4())
    db_manager.touch_session(session_id)

st.session_state.session_id = session_id
st.query_params["session_id"] = session_id
db_manager.touch_session(session_id)

# Reload messages and case file fresh from the database on every start or refresh
stored_records = db_manager.get_messages(session_id)
st.session_state.messages = [
    {"role": m["role"], "content": m["content"], "in_scope": m.get("in_scope", True)}
    for m in stored_records
]
st.session_state.case_facts = db_manager.get_or_create_case_facts(session_id)

if "latest_advice" not in st.session_state:
    st.session_state.latest_advice = None

if "language" not in st.session_state:
    sess_info = db_manager.get_session(session_id)
    st.session_state.language = sess_info.get("language") if sess_info else "English"

if "voice_transcript" not in st.session_state:
    st.session_state.voice_transcript = ""

# -------------------------------------------------------------
# Sidebar: Settings, Status, Case Facts & Data Deletion
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚖️ NyayaSathi")
    st.caption("AI Legal Information Helper (India)")

    # API Key & Status
    api_configured = config.is_api_configured()
    if api_configured:
        st.success(f"● AI Model Active: `{config.get_model_name()}`")
    else:
        st.error("● AI Service Offline (Demo/Fallback Mode)")

    # Language Selector
    selected_lang = st.selectbox(
        "Choose Your Language / भाषा चुनें",
        SUPPORTED_LANGUAGES,
        index=SUPPORTED_LANGUAGES.index(st.session_state.language)
        if st.session_state.language in SUPPORTED_LANGUAGES
        else 0,
    )
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        db_manager.touch_session(session_id, language=selected_lang)

    st.divider()

    # Download chat as text button
    if st.session_state.messages:
        chat_lines = [
            "============================================================",
            "NyayaSathi (न्यायसाथी) - Citizen Consultation Transcript",
            f"Session ID: {session_id}",
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "============================================================\n",
        ]
        for m in st.session_state.messages:
            role_label = "Citizen" if m["role"] == "user" else "NyayaSathi"
            chat_lines.append(f"[{role_label}]:\n{m['content']}\n")
        chat_text = "\n".join(chat_lines)
        st.download_button(
            "📥 Download Chat Transcript (.txt)",
            data=chat_text,
            file_name=f"NyayaSathi_Chat_{session_id[:8]}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # Data Deletion Action
    if st.button("🗑️ Delete My Data (Session Wipe)", use_container_width=True, type="secondary"):
        db_manager.delete_session_data(session_id)
        new_sid = str(uuid.uuid4())
        db_manager.touch_session(new_sid)
        st.session_state.session_id = new_sid
        st.query_params["session_id"] = new_sid
        st.session_state.messages = []
        st.session_state.case_facts = CaseFacts()
        st.session_state.latest_advice = None
        st.session_state.voice_transcript = ""
        st.success("All session records permanently deleted.")
        st.rerun()

    st.markdown("---")
    st.markdown(
        """
        **Strictly Supported Everyday Domains:**
        - 🏠 **Tenancy**: Unreturned deposits, eviction threats, rent disputes
        - 🛒 **Consumer**: Defective items, refund denials, service deficiency
        - 💼 **Employment**: Unpaid salary, wrongful termination, FNF delay
        
        *Criminal defense, matrimonial/divorce, court automation, and physical disputes are strictly out-of-scope.*
        """
    )

# -------------------------------------------------------------
# Main Chat & Case Panel UI
# -------------------------------------------------------------
# Top Disclaimer
st.markdown(
    '<div class="disclaimer-banner"><strong>⚠️ Important Disclaimer:</strong> '
    "NyayaSathi is an AI assistant providing general legal information and document drafts, not a licensed lawyer. "
    "For complex litigation or representation, please consult an advocate or your District Legal Services Authority (DLSA / NALSA Helpline 15100).</div>",
    unsafe_allow_html=True,
)

# Missing Key Banner if applicable
if not api_configured:
    st.markdown(
        '<div class="key-missing-banner"><strong>The AI service is not configured.</strong> '
        "Add <code>GEMINI_API_KEY</code> to <code>.env</code> in the project root, then refresh this page. "
        "Offline mock and deterministic fallback rules are currently active.</div>",
        unsafe_allow_html=True,
    )

st.markdown('<div class="main-title">NyayaSathi (न्यायसाथी)</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Tell me your problem in your own words. We will organize the facts, check your legal rights, and prepare actionable documents.</div>',
    unsafe_allow_html=True,
)

def execute_chat_turn(user_text: str):
    """Processes a user message turn adhering strictly to Issue 1 and Issue 2 constraints:
    1. Save user message first to DB.
    2. Run scope gate before calling answering model.
    3. If out-of-scope: return exact fixed reply 'I do not know.' (or emergency) and save with in_scope=False without calling answering model.
    4. If greeting: return fixed greeting.
    5. If in-scope: extract facts, call answering model via build_context, save assistant reply with in_scope=True.
    """
    if not user_text.strip():
        return

    user_clean = user_text.strip()

    # Detect language if not explicitly changed
    if st.session_state.language == "English":
        auto_lang = detect_language_simple(user_clean)
        if auto_lang != "English":
            st.session_state.language = auto_lang
            db_manager.touch_session(session_id, language=auto_lang)

    # 1. SAVE USER MESSAGE FIRST
    db_manager.add_message(
        session_id=session_id,
        role="user",
        content=user_clean,
        language=st.session_state.language,
        in_scope=True,
    )
    # Reload local state
    st.session_state.messages = db_manager.get_messages(session_id)

    # 2. RUN SCOPE GATE BEFORE CALLING ANSWERING MODEL
    ongoing_case_type = (
        st.session_state.case_facts.category
        if st.session_state.case_facts.category in ALLOWED_TOPICS
        else None
    )
    history_ctx = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages[-6:]
    )
    scope_res = scope_gate.classify(
        user_message=user_clean,
        conversation_context=history_ctx,
        ongoing_case_type=ongoing_case_type,
    )

    # OUT OF SCOPE CASE
    if scope_res.topic == "out_of_scope":
        fixed_reply = scope_gate.get_fixed_reply(
            topic="out_of_scope",
            language=st.session_state.language,
            is_emergency=scope_res.is_emergency,
        ) or "I do not know."
        db_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=fixed_reply,
            language=st.session_state.language,
            in_scope=False,
        )
        st.session_state.messages = db_manager.get_messages(session_id)
        st.rerun()

    # GREETING OR INTAKE CASE
    if scope_res.topic == "greeting_or_intake":
        greeting_reply = scope_gate.get_fixed_reply(
            topic="greeting_or_intake",
            language=st.session_state.language,
        ) or "Namaste! I am NyayaSathi."
        db_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=greeting_reply,
            language=st.session_state.language,
            in_scope=True,
        )
        st.session_state.messages = db_manager.get_messages(session_id)
        st.rerun()

    # IN SCOPE: (tenancy | consumer | employment)
    # Mixed messages: if an in-scope portion was extracted, answer only that portion
    query_to_answer = scope_res.in_scope_portion if scope_res.in_scope_portion else user_clean

    try:
        # A. Fact Extraction
        updated_facts, questions = case_builder.process_turn(
            user_message=query_to_answer,
            current_facts=st.session_state.case_facts,
            language=st.session_state.language,
            session_id=session_id,
        )
        st.session_state.case_facts = updated_facts
        db_manager.save_case_facts(session_id, updated_facts)

        # B. Answering Model Call using build_context
        advice = llm_client.generate_legal_advice(
            user_problem=query_to_answer,
            domain=updated_facts.category if updated_facts.category in ALLOWED_TOPICS else scope_res.topic,
            language=st.session_state.language,
            session_id=session_id,
        )
        st.session_state.latest_advice = advice

        # C. Format Assistant Response
        resp_parts = [advice.summary]
        if advice.options:
            resp_parts.append("\n**Recommended Steps You Can Take:**")
            for i, opt in enumerate(advice.options[:2], 1):
                resp_parts.append(f"{i}. **{opt.title}**: {opt.description}")
        if questions:
            resp_parts.append("\n**To help you better, could you clarify:**")
            for q in questions:
                resp_parts.append(f"- {q}")

        bot_reply = "\n\n".join(resp_parts)
        db_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=bot_reply,
            language=st.session_state.language,
            in_scope=True,
        )
        st.session_state.messages = db_manager.get_messages(session_id)
    except Exception as e:
        # User message was already safely saved in DB. Show error.
        st.error(f"Error during legal reasoning: {e}")
        error_reply = "I encountered an issue processing this response. Your information was saved; please try rephrasing or consulting DLSA / an advocate."
        db_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=error_reply,
            language=st.session_state.language,
            in_scope=True,
        )
        st.session_state.messages = db_manager.get_messages(session_id)

    st.rerun()


# Two-column layout: Left = Conversational Intake, Right = Live Case Facts Panel
col_chat, col_facts = st.columns([1.2, 0.8], gap="large")

with col_chat:
    st.subheader("💬 Legal Consultation Chat")

    # Optional Voice Input Accordion
    with st.expander("🎙️ Speak Your Problem (Voice Input / बोलकर बताएं)", expanded=False):
        st.caption("Record your voice in any Indian language. Review the transcript before sending.")
        audio_val = st.audio_input("Record audio from microphone")
        if audio_val:
            if st.button("Transcribe Audio", key="transcribe_btn"):
                with st.spinner("Transcribing your audio..."):
                    audio_bytes = audio_val.read()
                    st.session_state.voice_transcript = voice_adapter.transcribe_audio(
                        audio_bytes=audio_bytes,
                        language_hint=st.session_state.language,
                    )

        if st.session_state.voice_transcript:
            edited_transcript = st.text_area(
                "Review & Edit Spoken Words:",
                value=st.session_state.voice_transcript,
                height=90,
            )
            if st.button("Send Confirmed Transcript to Legal Helper", type="primary"):
                user_msg = edited_transcript.strip()
                st.session_state.voice_transcript = ""
                execute_chat_turn(user_msg)

    # Render greeting visually if chat is brand new
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown(
                "Namaste! I am NyayaSathi, your AI legal helper for everyday problems in India.\n\n"
                "I can help you with:\n"
                "- 🏠 **Tenancy**: Withheld security deposit, eviction notice, rent disputes\n"
                "- 🛒 **Consumer**: Defective product, refund denied, deficient service\n"
                "- 💼 **Employment**: Unpaid salary, wrongful termination, FNF dues\n\n"
                "Please tell me what happened in as much detail as you can."
            )

    # Display chat message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User Input Field
    user_input = st.chat_input("Explain what happened or reply to questions...")
    if user_input:
        execute_chat_turn(user_input)

with col_facts:
    st.subheader("📋 Live Case Fact Sheet")
    st.caption("These confirmed facts are used to draft legal notices and complaints.")

    facts: CaseFacts = st.session_state.case_facts

    with st.form("case_facts_editor"):
        category = st.selectbox(
            "Dispute Category",
            ["tenancy", "consumer", "employment", "general"],
            index=["tenancy", "consumer", "employment", "general"].index(facts.category)
            if facts.category in ["tenancy", "consumer", "employment", "general"]
            else 3,
        )
        comp_name = st.text_input("Your Full Name (Complainant)", value=facts.complainant_name)
        comp_contact = st.text_input("Your Contact / Email", value=facts.complainant_contact)
        comp_addr = st.text_area("Your Address", value=facts.complainant_address, height=70)
        opp_name = st.text_input("Opposite Party / Landlord / Company", value=facts.opposite_party_name)
        opp_addr = st.text_area("Opposite Party Address", value=facts.opposite_party_address, height=70)
        city_state = st.text_input("City, State (Jurisdiction)", value=facts.city_state)
        amount = st.text_input("Disputed Monetary Amount", value=facts.dispute_amount)
        incident_date = st.text_input("Key Date / Agreement Date", value=facts.incident_date)
        relief = st.text_input("Relief Sought (e.g. Full Refund + 18% Interest)", value=facts.relief_sought)
        summary = st.text_area("Summary of Facts", value=facts.summary_of_facts, height=90)

        is_confirmed = st.checkbox("I confirm these facts are accurate", value=facts.is_confirmed)
        save_btn = st.form_submit_button("💾 Save & Update Case File", use_container_width=True)

        if save_btn:
            updated = CaseFacts(
                category=category,
                complainant_name=comp_name.strip() or "[TO BE FILLED]",
                complainant_contact=comp_contact.strip() or "[TO BE FILLED]",
                complainant_address=comp_addr.strip() or "[TO BE FILLED]",
                opposite_party_name=opp_name.strip() or "[TO BE FILLED]",
                opposite_party_address=opp_addr.strip() or "[TO BE FILLED]",
                city_state=city_state.strip() or "[TO BE FILLED]",
                dispute_amount=amount.strip() or "[TO BE FILLED]",
                incident_date=incident_date.strip() or "[TO BE FILLED]",
                agreement_details=facts.agreement_details,
                summary_of_facts=summary.strip() or "[TO BE FILLED]",
                relief_sought=relief.strip() or "[TO BE FILLED]",
                evidence_has=facts.evidence_has,
                evidence_missing=facts.evidence_missing,
                steps_taken_so_far=facts.steps_taken_so_far,
                is_confirmed=is_confirmed,
            )
            st.session_state.case_facts = updated
            db_manager.save_case_facts(session_id, updated)
            st.success("Case file updated successfully!")
            st.rerun()

# -------------------------------------------------------------
# Detailed Legal Standing & Corpus Grounding Section
# -------------------------------------------------------------
if st.session_state.latest_advice:
    adv: StructuredLegalAdvice = st.session_state.latest_advice
    st.divider()
    st.subheader("📚 Verified Legal Standing & Corpus Citations")

    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        if adv.confidence == ConfidenceLevel.HIGH:
            st.success(f"Confidence Level: **HIGH**")
        elif adv.confidence == ConfidenceLevel.MEDIUM:
            st.warning(f"Confidence Level: **MEDIUM**")
        else:
            st.error(f"Confidence Level: **LOW / UNCERTAIN**")

    with col_meta2:
        if adv.needs_lawyer:
            st.warning(f"⚠️ Advocate Consultation Recommended: {adv.lawyer_reason or 'Legal complexity'}")
        else:
            st.info("ℹ️ Standard Self-Help Resolution Applicable")

    with col_meta3:
        st.write(f"Verified Citations: **{len(adv.citations)}** provisions")

    if adv.citations:
        st.markdown("#### Citations from Source of Truth Corpus")
        for cit in adv.citations:
            entry = corpus_db.get_entry(cit.corpus_id)
            with st.expander(f"📖 {cit.provision_name} [{cit.corpus_id}]", expanded=True):
                st.write(f"**Application:** {cit.relevance}")
                if entry:
                    st.write(f"**Act & Status:** {entry.act_name} ({entry.year}) — `{entry.status.value}`")
                    st.write(f"**Plain Summary:** {entry.summary}")
                    st.write(f"**Verbatim Extract:** _{entry.verbatim_extract}_")
                    st.markdown(f"[Official Government Gazette / India Code Link]({entry.official_source_url})")
    else:
        st.info("No specific statutory citations applicable to this general query.")
