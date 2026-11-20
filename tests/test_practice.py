"""Unit tests for PracticeEngine (Opponent roleplay and argument feedback)."""

from core.models import CaseFacts
from core.practice import PracticeEngine


def test_mock_opponent_turns():
    engine = PracticeEngine(mock_mode=True)
    facts = CaseFacts(dispute_amount="Rs. 50,000")

    resp_landlord = engine.play_opponent_turn(
        persona="landlord",
        user_argument="I vacated the house cleanly and demand my 50000 deposit back",
        facts=facts,
        conversation_history=[],
    )
    assert len(resp_landlord) > 0
    assert "deposit" in resp_landlord.lower() or "clean" in resp_landlord.lower() or "deducted" in resp_landlord.lower()

    resp_ecommerce = engine.play_opponent_turn(
        persona="ecommerce",
        user_argument="The phone was broken out of the box",
        facts=facts,
        conversation_history=[],
    )
    assert "return" in resp_ecommerce.lower() or "policy" in resp_ecommerce.lower() or "7 days" in resp_ecommerce.lower()


def test_mock_argument_evaluation():
    engine = PracticeEngine(mock_mode=True)
    facts = CaseFacts(category="tenancy", dispute_amount="Rs. 40,000")
    user_args = [
        "I gave you 1 month notice as per our agreement.",
        "Here are the photos showing no damage to walls.",
    ]
    fb = engine.evaluate_arguments(
        persona="landlord",
        user_arguments=user_args,
        facts=facts,
    )
    assert len(fb.key_strengths) > 0
    assert len(fb.evidence_to_prepare) > 0
    assert len(fb.recommended_counter_response) > 0
