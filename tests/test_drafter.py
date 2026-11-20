"""Unit tests for DocumentDrafter (PDF, DOCX, and placeholder integrity)."""

from core.drafter import DISCLAIMER_TEXT, DocumentDrafter
from core.models import CaseFacts, CitationItem


def test_placeholders_left_as_to_be_filled():
    drafter = DocumentDrafter()
    blank_facts = CaseFacts()
    draft = drafter.draft_legal_notice(blank_facts, citations=[])

    assert "[TO BE FILLED]" in draft
    assert "Date:" in draft
    assert DISCLAIMER_TEXT in draft


def test_filled_facts_appear_in_notice():
    drafter = DocumentDrafter()
    facts = CaseFacts(
        complainant_name="Rohit Verma",
        complainant_address="Flat 402, Green Valley, Pune",
        complainant_contact="rohit@example.com",
        opposite_party_name="Kailash Sharma (Owner)",
        opposite_party_address="House 12, MG Road, Pune",
        city_state="Pune, Maharashtra",
        dispute_amount="Rs. 45,000",
        incident_date="01-10-2026",
        summary_of_facts="Landlord refused to refund 45,000 deposit despite handing over keys.",
        relief_sought="immediate refund of Rs. 45,000",
    )
    citations = [
        CitationItem(
            corpus_id="MTA_2021_SEC_11",
            provision_name="Model Tenancy Act 2021 Section 11",
            relevance="Deposit refund due on handing over vacant possession.",
        )
    ]
    draft = drafter.draft_legal_notice(facts, citations)

    assert "Rohit Verma" in draft
    assert "Kailash Sharma (Owner)" in draft
    assert "Rs. 45,000" in draft
    assert "Pune, Maharashtra" in draft
    assert "Model Tenancy Act 2021 Section 11" in draft
    assert DISCLAIMER_TEXT in draft


def test_consumer_complaint_drafting():
    drafter = DocumentDrafter()
    facts = CaseFacts(
        complainant_name="Sneha Patil",
        opposite_party_name="QuickCart Online Retail",
        dispute_amount="Rs. 22,000",
        city_state="Mumbai, Maharashtra",
        summary_of_facts="Purchased refrigerator that was defective on delivery.",
    )
    citations = [
        CitationItem(
            corpus_id="CPA_2019_SEC_2_11",
            provision_name="Consumer Protection Act, 2019 Section 2(11)",
            relevance="Deficiency in service.",
        )
    ]
    draft = drafter.draft_consumer_complaint(facts, citations)

    assert "Sneha Patil" in draft
    assert "QuickCart Online Retail" in draft
    assert "Section 35 of the Consumer Protection Act, 2019" in draft
    assert "MUMBAI, MAHARASHTRA" in draft
    assert DISCLAIMER_TEXT in draft


def test_docx_export_produces_valid_bytes():
    drafter = DocumentDrafter()
    sample_text = "LEGAL NOTICE\n\nTest content.\n\nDISCLAIMER: Test disclaimer."
    docx_stream = drafter.generate_docx(sample_text, title="Test Notice")
    bytes_data = docx_stream.getvalue()

    assert len(bytes_data) > 0
    # DOCX is a zip file, starting with PK (0x50, 0x4B)
    assert bytes_data[:2] == b"PK"


def test_pdf_export_produces_valid_bytes():
    drafter = DocumentDrafter()
    sample_text = "LEGAL NOTICE\n\nTest content for PDF export.\n\nDISCLAIMER: Test disclaimer."
    pdf_stream = drafter.generate_pdf(sample_text, title="Test Notice")
    bytes_data = pdf_stream.getvalue()

    assert len(bytes_data) > 0
    # PDF begins with %PDF
    assert bytes_data[:4] == b"%PDF"
