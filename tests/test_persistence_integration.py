"""Integration tests for Session Persistence, Multi-Turn Context Use,
Summarisation under Budget, No-Duplicate Guarantees, and Data Deletion.
"""

import uuid
import pytest
from core.case_builder import CaseBuilder
from core.config import config
from core.context import build_context
from core.database import db_manager
from core.llm import LegalLLMClient
from core.models import CaseFacts


def test_persistence_across_session_reloads_mock():
    """Test 1 (OFFLINE MOCK): Send 3 messages, reload the session via session ID,
    confirm all messages and the case file come back and appear in next model call's context.
    """
    sid = str(uuid.uuid4())
    db_manager.touch_session(sid)
    builder = CaseBuilder(mock_mode=True)

    # 1. First turn: user mentions dispute
    msg1 = "My landlord Mr. Ramesh Rao is withholding my deposit in Bengaluru."
    db_manager.add_message(sid, "user", msg1)
    facts, _ = builder.process_turn(msg1, CaseFacts(), session_id=sid)
    db_manager.save_case_facts(sid, facts)
    db_manager.add_message(sid, "assistant", "How much was the deposit amount?")

    # 2. Second turn: user gives amount
    msg2 = "The deposit amount was Rs. 80,000."
    db_manager.add_message(sid, "user", msg2)
    facts, _ = builder.process_turn(msg2, facts, session_id=sid)
    db_manager.save_case_facts(sid, facts)
    db_manager.add_message(sid, "assistant", "Do you have the rental agreement?")

    # 3. Third turn: user confirms agreement
    msg3 = "Yes, I have an 11-month registered rent agreement."
    db_manager.add_message(sid, "user", msg3)
    facts, _ = builder.process_turn(msg3, facts, session_id=sid)
    db_manager.save_case_facts(sid, facts)
    db_manager.add_message(sid, "assistant", "Got it. You have strong documentation.")

    # SIMULATE APP RESTART / RELOAD: query by session ID fresh
    reloaded_messages = db_manager.get_messages(sid)
    reloaded_facts = db_manager.get_or_create_case_facts(sid)

    assert len(reloaded_messages) == 6
    assert reloaded_messages[0]["content"] == msg1
    assert reloaded_messages[2]["content"] == msg2
    assert reloaded_messages[4]["content"] == msg3

    # Confirm case file was preserved
    assert reloaded_facts.category == "tenancy"
    assert reloaded_facts.opposite_party_name == "Mr. Ramesh Rao"
    assert "80,000" in reloaded_facts.dispute_amount

    # Confirm next model call's context contains all restored facts and messages
    ctx = build_context(sid, current_query="what about the notice?")
    assert "Mr. Ramesh Rao" in ctx.case_file_json
    assert "80,000" in ctx.case_file_json
    assert "11-month registered rent agreement" in ctx.full_context_text


def test_context_use_facts_retained_in_turn_4_mock():
    """Test 2 (OFFLINE MOCK): Say landlord's name and deposit amount in message 1,
    then ask 'how much should I demand?' in message 4. The answer must use those facts.
    """
    sid = str(uuid.uuid4())
    db_manager.touch_session(sid)
    builder = CaseBuilder(mock_mode=True)
    client = LegalLLMClient(mock_mode=True)

    # Message 1
    m1 = "My landlord Mr. Kulkarni has refused to return my security deposit of Rs. 65,000."
    db_manager.add_message(sid, "user", m1)
    facts, _ = builder.process_turn(m1, CaseFacts(), session_id=sid)
    db_manager.save_case_facts(sid, facts)
    db_manager.add_message(sid, "assistant", "Did you give proper notice before vacating?")

    # Message 2
    m2 = "Yes, 30 days written notice via WhatsApp and email."
    db_manager.add_message(sid, "user", m2)
    facts, _ = builder.process_turn(m2, facts, session_id=sid)
    db_manager.save_case_facts(sid, facts)
    db_manager.add_message(sid, "assistant", "Did he inspect the premises?")

    # Message 3
    m3 = "Yes, keys were handed over on 1st November."
    db_manager.add_message(sid, "user", m3)
    facts, _ = builder.process_turn(m3, facts, session_id=sid)
    db_manager.save_case_facts(sid, facts)
    db_manager.add_message(sid, "assistant", "Understood.")

    # Message 4: Ask without restating facts
    m4 = "how much should I demand?"
    db_manager.add_message(sid, "user", m4)

    # Generate advice
    advice = client.generate_legal_advice(
        user_problem=m4,
        domain="tenancy",
        session_id=sid,
    )

    combined_text = advice.summary + " " + " ".join(advice.facts_extracted) + " " + " ".join(opt.description for opt in advice.options)
    assert ("65,000" in combined_text or "65000" in combined_text or "Kulkarni" in combined_text)


def test_summarisation_under_budget():
    """Test 3: Simulate a long chat that exceeds the budget.
    Confirm a summary is created and old facts are still available to the model.
    """
    sid = str(uuid.uuid4())
    db_manager.touch_session(sid)
    facts = CaseFacts(
        category="consumer",
        opposite_party_name="Flipkart India",
        dispute_amount="Rs. 42,000",
        summary_of_facts="Purchased a television which had dead pixels on arrival",
    )
    db_manager.save_case_facts(sid, facts)

    # Generate 22 messages with substantial content to exceed budget
    for i in range(22):
        role = "user" if i % 2 == 0 else "assistant"
        db_manager.add_message(
            sid, role, f"Turn {i}: Detailed discussion on invoice number INV-998822 and customer support escalation ticket {i}."
        )

    # Build context with max_recent_messages=8
    ctx = build_context(sid, current_query="Can I file a case?", max_recent_messages=8)

    # Summary record must exist in DB
    summary_rec = db_manager.get_summary(sid)
    assert summary_rec is not None
    assert summary_rec["covers_up_to_message_id"] > 0
    assert summary_rec["rolling_summary"] != ""

    # Old facts remain available in the structured case file and summary
    assert "Flipkart India" in ctx.case_file_json
    assert "Rs. 42,000" in ctx.case_file_json
    assert len(ctx.recent_messages) == 8


def test_no_duplicate_messages_on_multiple_retrievals():
    """Test 4: Confirm that repeated DB reads, touches, or context builds do not duplicate rows."""
    sid = str(uuid.uuid4())
    db_manager.touch_session(sid)

    db_manager.add_message(sid, "user", "Message A")
    db_manager.add_message(sid, "assistant", "Message B")

    # Call get_messages multiple times
    msgs1 = db_manager.get_messages(sid)
    msgs2 = db_manager.get_messages(sid)
    assert len(msgs1) == 2
    assert len(msgs2) == 2

    # Multiple touch calls
    db_manager.touch_session(sid)
    db_manager.touch_session(sid)
    sess_count = len(db_manager.get_messages(sid))
    assert sess_count == 2


def test_delete_my_data_complete_wipe():
    """Test 5: Confirms all rows in sessions, messages, case_files, and summaries are removed."""
    sid = str(uuid.uuid4())
    db_manager.touch_session(sid)
    db_manager.add_message(sid, "user", "Sensitive Aadhaar: 1234-5678-9012")
    db_manager.add_message(sid, "assistant", "Understood.")
    db_manager.save_case_facts(sid, CaseFacts(complainant_name="Secret Citizen"))
    db_manager.save_summary(sid, "Secret summary", covers_up_to_message_id=2)

    # Verify rows exist
    assert len(db_manager.get_messages(sid)) == 2
    assert db_manager.get_summary(sid) is not None
    assert db_manager.get_or_create_case_facts(sid).complainant_name == "Secret Citizen"

    # Execute Wipe
    deleted = db_manager.delete_session_data(sid)
    assert deleted is True

    # Verify completely empty
    assert len(db_manager.get_messages(sid)) == 0
    assert db_manager.get_summary(sid) is None
    assert db_manager.get_session(sid) is None
    # Fresh retrieval creates clean slate
    clean_facts = db_manager.get_or_create_case_facts(sid)
    assert clean_facts.complainant_name == "[TO BE FILLED]"


@pytest.mark.live
@pytest.mark.live
def test_persistence_and_context_live():
    """LANE B LIVE TEST: Multi-turn persistence and context reasoning against real Gemini API."""
    if not config.is_api_configured():
        pytest.skip("Gemini API key is not configured in .env.")

    sid = str(uuid.uuid4())
    db_manager.touch_session(sid)
    client = LegalLLMClient(mock_mode=False)

    facts = CaseFacts(
        category="tenancy",
        opposite_party_name="Mr. Kulkarni",
        dispute_amount="Rs. 65,000",
        city_state="Bengaluru, Karnataka",
        summary_of_facts="Landlord refusing to refund Rs. 65,000 security deposit after full vacation and keys handover",
        is_confirmed=True,
    )
    db_manager.save_case_facts(sid, facts)
    db_manager.add_message(sid, "user", "My landlord Mr. Kulkarni is withholding my Rs 65000 deposit.")
    db_manager.add_message(sid, "assistant", "Understood. Did you give full notice?")
    db_manager.add_message(sid, "user", "Yes, 30 days notice was served in writing.")
    db_manager.add_message(sid, "assistant", "Good. You have fulfilled notice requirements.")

    # Live call using build_context with follow-up query
    advice = client.generate_legal_advice(
        user_problem="how much should I demand in the legal notice?",
        domain="tenancy",
        session_id=sid,
    )

    assert advice.summary is not None
    assert len(advice.options) > 0
    assert advice.confidence in ["high", "medium", "low"]
    # Check that the model recognized the dispute context
    combined = advice.summary + " " + " ".join(advice.facts_extracted) + " " + " ".join(o.description for o in advice.options)
    assert any(term in combined.lower() for term in ["65,000", "65000", "deposit", "kulkarni", "notice"])
