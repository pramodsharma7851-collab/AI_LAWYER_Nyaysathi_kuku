"""NyayaSathi - Document Drafter Page.

Allows citizens to generate, review, and download formatted Legal Notices
and Consumer Complaints in both DOCX and PDF formats.
"""

import streamlit as st
from core.database import db_manager
from core.drafter import drafter
from core.models import CaseFacts
from core.scope import ALLOWED_TOPICS

st.set_page_config(page_title="Document Drafter - NyayaSathi", page_icon="📄", layout="wide")

st.title("📄 Document Drafter")
st.caption("Generate formal legal notices and consumer complaints based strictly on confirmed facts.")

# Session persistence across tabs/pages
query_sid = st.query_params.get("session_id")
session_id = query_sid or st.session_state.get("session_id")
if session_id:
    st.session_state.session_id = session_id
    st.query_params["session_id"] = session_id
    st.session_state.case_facts = db_manager.get_or_create_case_facts(session_id)
else:
    if "case_facts" not in st.session_state:
        st.session_state.case_facts = CaseFacts()

# Top Disclaimer
st.warning(
    "⚠️ **Legal Notice**: These drafts are prepared for communication and pre-litigation. "
    "Any fact marked as `[TO BE FILLED]` must be completed before sending or filing."
)

facts: CaseFacts = st.session_state.case_facts

# Scope restriction check
if facts.category not in ALLOWED_TOPICS and facts.category != "general":
    st.error("I do not know.\n\nDocument drafting is strictly restricted to Tenancy, Consumer Disputes, and Employment cases.")
    st.stop()
citations = []
if "latest_advice" in st.session_state and st.session_state.latest_advice:
    citations = st.session_state.latest_advice.citations

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Select Document Type & Review Facts")
    doc_type = st.radio(
        "Choose document to generate:",
        ["Formal Legal Demand Notice", "Consumer Complaint (District Commission / e-Daakhil)"],
    )

    with st.expander("Review Facts Used for Drafting", expanded=True):
        st.write(f"**Complainant:** {facts.complainant_name}")
        st.write(f"**Opposite Party:** {facts.opposite_party_name}")
        st.write(f"**Disputed Amount:** {facts.dispute_amount}")
        st.write(f"**Jurisdiction (City/State):** {facts.city_state}")
        st.write(f"**Summary:** {facts.summary_of_facts}")
        if not facts.is_confirmed:
            st.info("💡 You can edit and confirm these facts anytime on the main Chat page.")

    # Generate draft text
    if doc_type == "Formal Legal Demand Notice":
        draft_text = drafter.draft_legal_notice(facts, citations)
        title_for_file = "Legal_Notice"
    else:
        draft_text = drafter.draft_consumer_complaint(facts, citations)
        title_for_file = "Consumer_Complaint"

    st.subheader("2. Export Document")
    # Generate in-memory files
    docx_io = drafter.generate_docx(draft_text, title=doc_type)
    pdf_io = drafter.generate_pdf(draft_text, title=doc_type)

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.download_button(
            label="📥 Download Microsoft Word (.docx)",
            data=docx_io,
            file_name=f"NyayaSathi_{title_for_file}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

    with btn_col2:
        st.download_button(
            label="📥 Download Adobe PDF (.pdf)",
            data=pdf_io,
            file_name=f"NyayaSathi_{title_for_file}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

with col2:
    st.subheader("3. Live Document Preview")
    st.text_area("Document Content", value=draft_text, height=580)
