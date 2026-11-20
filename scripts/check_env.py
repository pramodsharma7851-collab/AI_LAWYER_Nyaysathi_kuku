"""Environment and API Key Checker for NyayaSathi.

Follows the non-blocking API key protocol.
Never prints, echoes, or logs the key, even partially or masked.
"""

import os
import sys
from pathlib import Path

# Placeholder token
PLACEHOLDER = "PASTE_YOUR_GEMINI_API_KEY_HERE"

BANNER = (
    ">>> ACTION NEEDED: open the .env file in the project root, "
    "replace PASTE_YOUR_GEMINI_API_KEY_HERE with your key, save. "
    "Or run: python scripts/set_key.py. The build continues meanwhile. <<<"
)


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_env_file(root: Path) -> dict:
    """Read .env file directly to avoid stale caching."""
    env_path = root / ".env"
    data = {}
    if not env_path.exists():
        return data
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    data[key.strip()] = val.strip().strip("'\"")
    except Exception:
        pass
    return data


def resolve_api_key(root: Path) -> str | None:
    """Lookup order: environment variable, then .env, then Streamlit secrets."""
    # 1. Environment variable
    key = os.environ.get("GEMINI_API_KEY")
    if key and key.strip() and key.strip() != PLACEHOLDER:
        return key.strip()

    # 2. .env file
    env_data = read_env_file(root)
    key = env_data.get("GEMINI_API_KEY")
    if key and key.strip() and key.strip() != PLACEHOLDER:
        return key.strip()

    # 3. Streamlit secrets
    secrets_path = root / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            with open(secrets_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY"):
                        _, val = line.split("=", 1)
                        val = val.strip().strip("'\"")
                        if val and val != PLACEHOLDER:
                            return val
        except Exception:
            pass

    return None


def resolve_model_name(root: Path) -> str:
    """Resolve model name, defaults to auto."""
    val = os.environ.get("GEMINI_MODEL")
    if val and val.strip():
        return val.strip()

    env_data = read_env_file(root)
    val = env_data.get("GEMINI_MODEL")
    if val and val.strip():
        return val.strip()

    return "auto"


def update_model_in_env(root: Path, model_name: str) -> None:
    """Update only the GEMINI_MODEL line in .env, never touching the key."""
    env_path = root / ".env"
    if not env_path.exists():
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = []
        model_found = False
        for line in lines:
            if line.strip().startswith("GEMINI_MODEL"):
                new_lines.append(f"GEMINI_MODEL={model_name}\n")
                model_found = True
            else:
                new_lines.append(line)
        if not model_found:
            new_lines.append(f"\nGEMINI_MODEL={model_name}\n")
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception:
        pass


def test_key_and_model(api_key: str, model_candidate: str, root: Path) -> tuple[bool, str, str]:
    """Test live connectivity using official google-genai SDK.

    Returns (success, short_reason, chosen_model).
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return False, "google-genai SDK not installed in environment", model_candidate

    try:
        client = genai.Client(api_key=api_key)

        candidates = [
            "gemini-3.5-flash-lite",
            "gemini-3.8-flash",
            "gemini-3.5-flash",
        ]

        if model_candidate != "auto" and model_candidate:
            candidates = [model_candidate] + [c for c in candidates if c != model_candidate]

        last_error = ""
        chosen_model = None

        for c in candidates:
            try:
                response = client.models.generate_content(
                    model=c,
                    contents="hi",
                    config=types.GenerateContentConfig(max_output_tokens=5),
                )
                if response and response.text:
                    chosen_model = c
                    break
            except Exception as e:
                last_error = str(e)
                continue

        if chosen_model:
            update_model_in_env(root, chosen_model)
            return True, "PASS", chosen_model

        # If none succeeded, classify reason
        if "API_KEY_INVALID" in last_error or "400" in last_error or "invalid" in last_error.lower():
            return False, "invalid key", model_candidate
        elif "RESOURCE_EXHAUSTED" in last_error or "429" in last_error or "quota" in last_error.lower():
            return False, "quota exceeded", model_candidate
        elif "UNAVAILABLE" in last_error or "503" in last_error:
            return False, "upstream model capacity/unavailable", model_candidate
        else:
            return False, f"model error or network failure ({last_error[:50]})", model_candidate

    except Exception as e:
        return False, f"network or client error ({type(e).__name__})", model_candidate


def main():
    root = get_project_root()
    key = resolve_api_key(root)

    if not key:
        print("API KEY NOT FOUND")
        print(BANNER)
        sys.exit(1)

    print("API KEY FOUND, CHECKING")
    model_name = resolve_model_name(root)
    success, reason, resolved_model = test_key_and_model(key, model_name, root)

    if success:
        print("PASS")
        sys.exit(0)
    else:
        print(f"FAIL: {reason}")
        sys.exit(2)


if __name__ == "__main__":
    main()
