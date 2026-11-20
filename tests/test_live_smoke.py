"""Live smoke tests for NyayaSathi against real Gemini API (Lane B).

Tests full pipeline (RAG -> Gemini Model -> Pydantic Schema -> Citation Verifier)
for Tenancy, Consumer, and Employment domains.
"""

import pytest
from core.config import config
from core.corpus import corpus_db
from core.llm import LegalLLMClient


@pytest.fixture
def live_client():
    if not config.is_api_configured():
        pytest.skip("Gemini API key is not configured. Skipping live smoke tests.")
    return LegalLLMClient(mock_mode=False)


@pytest.mark.live
def test_live_smoke_tenancy(live_client):
    problem = (
        "I vacated my rented flat in Bengaluru last month after giving 1 month notice. "
        "The landlord is withholding my security deposit of Rs. 60,000 claiming he needs to repaint the house, "
        "even though there is no damage beyond normal wear and tear."
    )
    advice = live_client.generate_legal_advice(
        user_problem=problem,
        domain="tenancy",
        language="English",
    )
    assert advice.summary is not None
    assert len(advice.options) > 0
    # Every returned citation must exist in the verified corpus
    for cit in advice.citations:
        assert corpus_db.get_entry(cit.corpus_id) is not None
    assert advice.confidence in ["high", "medium", "low"]


@pytest.mark.live
def test_live_smoke_consumer(live_client):
    problem = (
        "Maine ek smartphone online order kiya tha 25,000 rupees ka. "
        "Delivery ke agle din screen flickering shuru ho gayi. Company replacement ya refund dene se mana kar rahi hai."
    )
    advice = live_client.generate_legal_advice(
        user_problem=problem,
        domain="consumer",
        language="Hinglish",
    )
    assert advice.summary is not None
    assert len(advice.options) > 0
    for cit in advice.citations:
        assert corpus_db.get_entry(cit.corpus_id) is not None


@pytest.mark.live
def test_live_smoke_employment(live_client):
    problem = (
        "I was working at a tech startup for 2 years. Last month they fired me immediately without notice "
        "and withheld my last month salary and severance."
    )
    advice = live_client.generate_legal_advice(
        user_problem=problem,
        domain="employment",
        language="English",
    )
    assert advice.summary is not None
    assert len(advice.options) > 0
    for cit in advice.citations:
        assert corpus_db.get_entry(cit.corpus_id) is not None
