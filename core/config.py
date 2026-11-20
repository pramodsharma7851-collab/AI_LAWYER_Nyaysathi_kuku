"""Configuration manager for NyayaSathi.

Loads settings fresh from environment variables, .env, and Streamlit secrets.
Never exposes or logs the API key.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field

PLACEHOLDER = "PASTE_YOUR_GEMINI_API_KEY_HERE"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_fresh_env_dict() -> dict[str, str]:
    """Read .env directly from disk to detect any runtime updates."""
    env_file = PROJECT_ROOT / ".env"
    data = {}
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip().strip("'\"")
        except Exception:
            pass
    return data


def get_streamlit_secret(key: str) -> str | None:
    """Safely check Streamlit secrets if running inside Streamlit."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            val = str(st.secrets[key]).strip()
            if val and val != PLACEHOLDER:
                return val
    except Exception:
        pass
    # Check secrets.toml directly on disk if file exists
    toml_path = PROJECT_ROOT / ".streamlit" / "secrets.toml"
    if toml_path.exists():
        try:
            with open(toml_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(key):
                        _, val = line.split("=", 1)
                        val = val.strip().strip("'\"")
                        if val and val != PLACEHOLDER:
                            return val
        except Exception:
            pass
    return None


class AppConfig(BaseModel):
    project_root: Path = Field(default_factory=lambda: PROJECT_ROOT)
    data_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "data")
    corpus_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "corpus")
    templates_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "templates")
    session_expiry_days: int = 30
    rate_limit_per_minute: int = 15
    max_input_length: int = 4000

    def get_api_key(self) -> str | None:
        """Lookup order: 1) os.environ, 2) .env file (fresh), 3) Streamlit secrets."""
        # 1. os.environ
        env_val = os.environ.get("GEMINI_API_KEY")
        if env_val and env_val.strip() and env_val.strip() != PLACEHOLDER:
            return env_val.strip()

        # 2. .env file
        disk_env = get_fresh_env_dict()
        file_val = disk_env.get("GEMINI_API_KEY")
        if file_val and file_val.strip() and file_val.strip() != PLACEHOLDER:
            return file_val.strip()

        # 3. Streamlit secrets
        secret_val = get_streamlit_secret("GEMINI_API_KEY")
        if secret_val:
            return secret_val

        return None

    def get_model_name(self) -> str:
        """Lookup model name from os.environ, .env, or default to auto."""
        if "GEMINI_MODEL" in os.environ and os.environ["GEMINI_MODEL"].strip():
            return os.environ["GEMINI_MODEL"].strip()

        disk_env = get_fresh_env_dict()
        if "GEMINI_MODEL" in disk_env and disk_env["GEMINI_MODEL"].strip():
            return disk_env["GEMINI_MODEL"].strip()

        secret_val = get_streamlit_secret("GEMINI_MODEL")
        if secret_val:
            return secret_val

        return "auto"

    def is_api_configured(self) -> bool:
        """Returns True if a real API key is configured."""
        key = self.get_api_key()
        return bool(key and key != PLACEHOLDER)


# Global singleton config
config = AppConfig()
