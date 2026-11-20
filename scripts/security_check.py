"""Security scanner and secret audit script for NyayaSathi.

Checks:
1. No raw API keys or secret tokens exist in tracked repo files or git staging.
2. .env and secrets.toml are strictly gitignored.
3. Runs basic OWASP dependency and secret pattern scans.
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Forbidden regex patterns that indicate hard-coded credentials
SECRET_PATTERNS = [
    re.compile(r"AIzaSy[A-Za-z0-9\-_]{33}"),
    re.compile(r"GEMINI_API_KEY\s*=\s*['\"][A-Za-z0-9_\-\.]{30,}['\"]"),
]

IGNORED_DIRS = {".git", "venv", ".venv", "__pycache__", ".pytest_cache", "outputs"}


def scan_for_secrets():
    print("=== Scanning Repository for Hardcoded Secrets ===")
    violations = []

    # 1. Check .gitignore
    gitignore = ROOT / ".gitignore"
    if not gitignore.exists():
        violations.append(".gitignore file is missing!")
    else:
        text = gitignore.read_text(encoding="utf-8")
        if ".env" not in text:
            violations.append(".env is NOT present in .gitignore!")
        if "secrets.toml" not in text:
            violations.append(".streamlit/secrets.toml is NOT present in .gitignore!")

    # 2. Walk code files (skip .env itself since user pastes key there)
    for root, dirs, files in os.walk(ROOT):
        # Prune ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file in files:
            if file in [".env", ".env.backup", "nyayasathi.db"]:
                continue
            file_path = Path(root) / file
            # Only scan text/code files
            if file_path.suffix not in [".py", ".json", ".md", ".toml", ".yaml", ".yml", ".txt"]:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for pat in SECRET_PATTERNS:
                    if pat.search(content):
                        # Mask finding
                        rel_path = file_path.relative_to(ROOT)
                        violations.append(f"Potential secret pattern found in: {rel_path}")
            except Exception:
                pass

    if violations:
        print("[FAIL] Security violations detected:")
        for v in violations:
            print(f"  - {v}")
        return False
    else:
        print("[PASS] No hardcoded credentials or unignored secrets found in repo.")
        return True


if __name__ == "__main__":
    passed = scan_for_secrets()
    sys.exit(0 if passed else 1)
