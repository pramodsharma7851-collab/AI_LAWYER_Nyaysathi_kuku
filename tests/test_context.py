"""Unit tests for context building and memory management in core/context.py."""

import uuid
from core.context import build_context
from core.database import db_manager
from core.models import CaseFacts


def test_build_context_order_and_structure():
    sid = str(uuid.uuid4())
    facts = CaseFacts(
        category="tenancy",
        complainant_name="Vikram Seth",
        opposite_party_name="Mr. Sharma",
        dispute_amount="Rs. 75,000",
        city_state="Pune, Maharashtra",
        summary_of_facts="Landlord refusing to refund deposit after vacation",
    )
    db_manager.save_case_facts(sid, facts)
    db_manager.add_message(sid, "user", "I vacated on 1st October.")
    db_manager.add_message(sid, "assistant", "Did you have a written rent agreement?")

    ctx = build_context(session_id=sid, current_query="what about the notice?")

    # Verify return object
    assert ctx.system_prompt is not None
    assert "Vikram Seth" in ctx.case_file_json
    assert "Rs. 75,000" in ctx.case_file_json
    assert len(ctx.recent_messages) == 2
    assert ctx.authority_block is not None
    assert len(ctx.allowed_citation_ids) > 0

    # Verify structural order in full_context_text
    full_text = ctx.full_context_text
    sys_idx = full_text.find("=== SYSTEM PROMPT ===")
    case_idx = full_text.find("=== CURRENT CASE FILE")
    summ_idx = full_text.find("=== ROLLING SUMMARY")
    rec_idx = full_text.find("=== RECENT CONVERSATION")
    auth_idx = full_text.find("=== GROUNDED LEGAL AUTHORITY")

    assert sys_idx != -1
    assert case_idx > sys_idx
    assert summ_idx > case_idx
    assert rec_idx > summ_idx
    assert auth_idx > rec_idx


def test_composite_retrieval_for_followup():
    sid = str(uuid.uuid4())
    facts = CaseFacts(
        category="tenancy",
        dispute_amount="Rs. 50,000",
        summary_of_facts="Landlord refusing security deposit return",
    )
    db_manager.save_case_facts(sid, facts)

    # Short follow-up question
    ctx = build_context(session_id=sid, current_query="what about the notice?")
    # Authority block must retrieve tenancy provisions (e.g. MTA or TPA)
    assert any("TPA" in cid or "MTA" in cid for cid in ctx.allowed_citation_ids)


def test_budget_triggers_summarization():
    sid = str(uuid.uuid4())
    facts = CaseFacts(category="consumer", dispute_amount="Rs. 30,000")
    db_manager.save_case_facts(sid, facts)

    # Insert 25 messages
    for i in range(25):
        role = "user" if i % 2 == 0 else "assistant"
        db_manager.add_message(sid, role, f"Message turn {i}: discussing laptop repair status and refund.")

    # Context with max_recent_messages=10
    ctx = build_context(session_id=sid, current_query="Can I file a case?", max_recent_messages=10)

    # Recent messages must be exactly 10
    assert len(ctx.recent_messages) == 10
    # Summary must have been generated for older messages
    summ = db_manager.get_summary(sid)
    assert summ is not None
    assert summ["covers_up_to_message_id"] > 0
    assert ctx.rolling_summary != ""
