"""Unit tests for CaseBuilder and language detection."""

from core.case_builder import CaseBuilder, detect_language_simple
from core.models import CaseFacts


def test_language_detection():
    assert detect_language_simple("Hello, my landlord is not giving back my deposit") == "English"
    assert detect_language_simple("मेरा मकान मालिक सिक्योरिटी डिपॉजिट वापस नहीं कर रहा है") == "Hindi (हिन्दी)"
    assert detect_language_simple("Maine rent diya tha par deposit wapas nahi mila") == "Hinglish"
    assert detect_language_simple("என் நில உரிமையாளர் வாடகை முன்பணத்தை திருப்பித் தரவில்லை") == "Tamil (தமிழ்)"
    assert detect_language_simple("আমার বাড়িওয়ালা সিকিউরিটি ডিপোজিট ফেরত দিচ্ছে না") == "Bengali (বাংলা)"


def test_mock_case_builder_extraction():
    builder = CaseBuilder(mock_mode=True)
    facts = CaseFacts()
    updated, questions = builder.process_turn(
        user_message="My landlord in Delhi refused to return my deposit of 50000 rupees",
        current_facts=facts,
        language="English",
    )
    assert updated.category == "tenancy"
    assert len(questions) <= 3
    assert len(questions) > 0


def test_merge_facts_preserves_existing():
    from core.case_builder import CaseExtractionOutput
    builder = CaseBuilder(mock_mode=True)
    orig = CaseFacts(
        complainant_name="Vikram Singh",
        city_state="Pune, Maharashtra",
        dispute_amount="Rs. 35,000",
    )
    ext = CaseExtractionOutput(
        category="tenancy",
        complainant_name="",  # Empty should not wipe existing
        opposite_party_name="Sharma Properties",
        dispute_amount="Rs. 35,000",
    )
    merged = builder._merge_facts(orig, ext)
    assert merged.complainant_name == "Vikram Singh"
    assert merged.city_state == "Pune, Maharashtra"
    assert merged.opposite_party_name == "Sharma Properties"
