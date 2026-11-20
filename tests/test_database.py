"""Unit tests for SQLite database layer with Postgres-ready schema.

Verifies:
- Session creation, touch, and persistence
- Case facts JSON serialization and retrieval
- Message insertion with roles, order, and in_scope flags
- Rolling summary storage and retrieval
- Complete cascade wipe on 'Delete my data'
"""

import uuid
from core.database import db_manager
from core.models import CaseFacts


def test_session_creation_and_touch():
    sid = str(uuid.uuid4())
    db_manager.touch_session(sid, language="Hindi (हिन्दी)", case_type="tenancy")
    sess = db_manager.get_session(sid)
    assert sess is not None
    assert sess["language"] == "Hindi (हिन्दी)"
    assert sess["case_type"] == "tenancy"

    facts = db_manager.get_or_create_case_facts(sid)
    assert facts.complainant_name == "[TO BE FILLED]"
    assert not facts.is_confirmed


def test_save_and_retrieve_case_facts():
    sid = str(uuid.uuid4())
    facts = CaseFacts(
        category="tenancy",
        complainant_name="Aarav Sharma",
        dispute_amount="Rs. 50,000",
        city_state="Bengaluru, Karnataka",
        is_confirmed=True,
    )
    db_manager.save_case_facts(sid, facts)

    retrieved = db_manager.get_or_create_case_facts(sid)
    assert retrieved.complainant_name == "Aarav Sharma"
    assert retrieved.dispute_amount == "Rs. 50,000"
    assert retrieved.is_confirmed is True


def test_messages_ordered_and_scoped():
    sid = str(uuid.uuid4())
    m1_id = db_manager.add_message(sid, role="user", content="My landlord withheld Rs 60000 deposit", in_scope=True)
    m2_id = db_manager.add_message(sid, role="assistant", content="You have strong grounds under tenancy law", in_scope=True)
    m3_id = db_manager.add_message(sid, role="user", content="Who won the cricket match?", in_scope=False)
    m4_id = db_manager.add_message(sid, role="assistant", content="I do not know.", in_scope=False)

    msgs = db_manager.get_messages(sid)
    assert len(msgs) == 4
    assert msgs[0]["id"] == m1_id
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    assert msgs[2]["in_scope"] is False
    assert msgs[3]["content"] == "I do not know."


def test_rolling_summary_storage():
    sid = str(uuid.uuid4())
    db_manager.save_summary(sid, "Landlord withheld Rs 60,000 deposit in Bengaluru.", covers_up_to_message_id=5)

    summ = db_manager.get_summary(sid)
    assert summ is not None
    assert "Rs 60,000" in summ["rolling_summary"]
    assert summ["covers_up_to_message_id"] == 5


def test_delete_session_data_wipes_all_tables():
    sid = str(uuid.uuid4())
    facts = CaseFacts(complainant_name="Test User", dispute_amount="Rs. 40,000")
    db_manager.save_case_facts(sid, facts)
    db_manager.add_message(sid, "user", "Message 1")
    db_manager.add_message(sid, "assistant", "Message 2")
    db_manager.save_summary(sid, "Summary text", covers_up_to_message_id=2)

    # Confirm rows exist
    assert len(db_manager.get_messages(sid)) == 2
    assert db_manager.get_summary(sid) is not None
    assert db_manager.get_session(sid) is not None

    # Delete all data
    success = db_manager.delete_session_data(sid)
    assert success is True

    # Confirm all tables wiped for this session
    assert len(db_manager.get_messages(sid)) == 0
    assert db_manager.get_summary(sid) is None
    assert db_manager.get_session(sid) is None

    # Re-accessing creates clean blank slate
    new_facts = db_manager.get_or_create_case_facts(sid)
    assert new_facts.complainant_name == "[TO BE FILLED]"
