"""Unit tests for LegalLLMClient offline mock mode."""

from core.llm import LegalLLMClient
from core.models import ConfidenceLevel


def test_mock_llm_pipeline_tenancy():
    client = LegalLLMClient(mock_mode=True)
    advice = client.generate_legal_advice(
        user_problem="Landlord is withholding my security deposit of 40000 rupees without explanation",
        domain="tenancy",
        language="English",
    )
    assert advice.summary is not None
    assert len(advice.options) > 0
    assert len(advice.citations) > 0
    assert advice.citations[0].corpus_id.startswith(("MTA", "TPA", "ICA", "LSAA"))


def test_mock_llm_pipeline_consumer():
    client = LegalLLMClient(mock_mode=True)
    advice = client.generate_legal_advice(
        user_problem="Laptop stopped working in 2 days and service center refuses replacement",
        domain="consumer",
        language="Hindi",
    )
    assert len(advice.options) > 0
    assert any("CPA" in c.corpus_id for c in advice.citations)


def test_mock_llm_pipeline_employment():
    client = LegalLLMClient(mock_mode=True)
    advice = client.generate_legal_advice(
        user_problem="Company did not pay last two months salary after I resigned",
        domain="employment",
        language="Hinglish",
    )
    assert len(advice.options) > 0
    assert any("PWA" in c.corpus_id or "IDA" in c.corpus_id for c in advice.citations)
