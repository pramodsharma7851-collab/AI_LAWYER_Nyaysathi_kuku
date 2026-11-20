"""Health check script for NyayaSathi.

Validates core imports, corpus loading, DB readiness, and LLM configuration status.
Does not leak any sensitive keys or credentials.
"""

import sys
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

try:
    from core.config import config
    from core.privacy import redact_pii
except Exception as e:
    print(f"[FAIL] Core import error: {e}")
    sys.exit(1)


def check_health():
    print("=== NyayaSathi Health Check ===")
    status_ok = True

    # 1. Config & Project Root
    if config.project_root.exists():
        print(f"[OK] Project root: {config.project_root}")
    else:
        print("[FAIL] Project root not found")
        status_ok = False

    # 2. Database Directory
    config.data_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Data directory ready: {config.data_dir}")

    # 3. Corpus Directory
    if config.corpus_dir.exists():
        files = list(config.corpus_dir.glob("*.json"))
        print(f"[OK] Corpus directory found with {len(files)} JSON files")
    else:
        print("[WARN] Corpus directory not yet populated")

    # 4. LLM Configuration Status
    is_configured = config.is_api_configured()
    if is_configured:
        print(f"[OK] LLM API: CONFIGURED (Model: {config.get_model_name()})")
    else:
        print("[INFO] LLM API: NOT CONFIGURED (Running in offline fallback/mock mode)")

    # 5. PII Redaction
    sample = "Call me at +919876543210 or email test@example.com"
    redacted = redact_pii(sample)
    if "+919876543210" not in redacted and "test@example.com" not in redacted:
        print("[OK] PII Redaction filter active")
    else:
        print("[FAIL] PII Redaction failed test")
        status_ok = False

    if status_ok:
        print("=== Health: HEALTHY ===")
        sys.exit(0)
    else:
        print("=== Health: UNHEALTHY ===")
        sys.exit(1)


if __name__ == "__main__":
    check_health()
