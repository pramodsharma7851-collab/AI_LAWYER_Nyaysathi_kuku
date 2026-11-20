"""Secure key setter for NyayaSathi.

Prompts for GEMINI_API_KEY with getpass, writes it into .env,
and prints only 'Key saved.'
Never echoes, prints, or logs the key.
"""

import getpass
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    env_path = root / ".env"

    try:
        key = getpass.getpass("Enter your Gemini API Key (input hidden): ").strip()
    except Exception:
        print("Error reading input.", file=sys.stderr)
        sys.exit(1)

    if not key:
        print("No key entered. Aborted.", file=sys.stderr)
        sys.exit(1)

    # Read existing .env lines or create default template
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = [
            "# ============================================================\n",
            "# >>> PASTE YOUR GEMINI API KEY ON THE LINE BELOW <<<\n",
            "# Replace PASTE_YOUR_GEMINI_API_KEY_HERE with your key. No quotes, no spaces.\n",
            "# Get a key at https://aistudio.google.com  (never share or commit this file)\n",
            "# ============================================================\n",
            "GEMINI_API_KEY=PASTE_YOUR_GEMINI_API_KEY_HERE\n\n",
            "# Model is chosen automatically. Leave as \"auto\" unless you want to force one.\n",
            "GEMINI_MODEL=auto\n",
        ]

    new_lines = []
    key_written = False
    for line in lines:
        if line.strip().startswith("GEMINI_API_KEY="):
            new_lines.append(f"GEMINI_API_KEY={key}\n")
            key_written = True
        else:
            new_lines.append(line)

    if not key_written:
        new_lines.insert(0, f"GEMINI_API_KEY={key}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("Key saved.")


if __name__ == "__main__":
    main()
