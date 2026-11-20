"""Tests for privacy and PII redaction."""

from core.privacy import redact_pii, sanitize_for_log


def test_redact_phone_numbers():
    text = "Contact me at +919876543210 or 9876543210 for details."
    redacted = redact_pii(text)
    assert "+919876543210" not in redacted
    assert "9876543210" not in redacted
    assert "[REDACTED_PHONE]" in redacted


def test_redact_aadhaar():
    text = "My Aadhaar number is 1234 5678 9012."
    redacted = redact_pii(text)
    assert "1234 5678 9012" not in redacted
    assert "[REDACTED_AADHAAR]" in redacted


def test_redact_email():
    text = "Reach me at citizen.help@example.com anytime."
    redacted = redact_pii(text)
    assert "citizen.help@example.com" not in redacted
    assert "[REDACTED_EMAIL]" in redacted


def test_redact_api_key():
    dummy_key = "AIzaSy" + "D98f7g8d7f8d7f8d7f8d7f8d7f8d7f8d7"
    text = f"My key is {dummy_key}"
    redacted = redact_pii(text)
    assert "AIzaSy" not in redacted
    assert "[REDACTED_API_KEY]" in redacted


def test_sanitize_dict_recursive():
    payload = {
        "user": "Ramesh",
        "api_key": "secret_key_12345",
        "nested": {
            "email": "test@domain.com",
            "token": "token_abc"
        }
    }
    sanitized = sanitize_for_log(payload)
    assert sanitized["api_key"] == "[REDACTED_CREDENTIAL]"
    assert sanitized["nested"]["token"] == "[REDACTED_CREDENTIAL]"
    assert "[REDACTED_EMAIL]" in sanitized["nested"]["email"]
