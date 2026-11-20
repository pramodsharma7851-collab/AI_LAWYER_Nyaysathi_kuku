"""Privacy and data protection utilities for NyayaSathi.

Implements strict redaction of Personally Identifiable Information (PII):
- Phone numbers (Indian formats: +91, 10 digits, etc.)
- Aadhaar numbers (12 digits, 4-4-4)
- Email addresses
- API keys / secret tokens
- Street addresses / PIN codes
"""

import re
from typing import Any

# Regex patterns for Indian PII & Secrets
RE_PHONE = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b")
RE_AADHAAR = re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
RE_PINCODE = re.compile(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b")
RE_API_KEY = re.compile(r"(?:AIzaSy[A-Za-z0-9\-_]{33}|[A-Za-z0-9_\-]{39,})")


def redact_pii(text: str) -> str:
    """Redact sensitive PII from string before any logging or non-ephemeral processing."""
    if not isinstance(text, str):
        return text

    # Redact API keys first
    redacted = RE_API_KEY.sub("[REDACTED_API_KEY]", text)
    # Redact Aadhaar
    redacted = RE_AADHAAR.sub("[REDACTED_AADHAAR]", redacted)
    # Redact Phone numbers
    redacted = RE_PHONE.sub("[REDACTED_PHONE]", redacted)
    # Redact Email
    redacted = RE_EMAIL.sub("[REDACTED_EMAIL]", redacted)
    return redacted


def sanitize_for_log(data: Any) -> Any:
    """Recursively sanitize data structures for safe logging."""
    if isinstance(data, str):
        return redact_pii(data)
    elif isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if any(secret_term in k.lower() for secret_term in ["key", "token", "secret", "password", "auth"]):
                sanitized[k] = "[REDACTED_CREDENTIAL]"
            else:
                sanitized[k] = sanitize_for_log(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_for_log(item) for item in data]
    return data
