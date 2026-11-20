"""Automated UI tests for NyayaSathi using Streamlit AppTest framework."""

from pathlib import Path
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_boots_without_error():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    # Verify title or main components render
    assert len(at.chat_input) == 1
    assert len(at.sidebar.selectbox) == 1


def test_disclaimer_is_rendered():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    # Check that the disclaimer is present in the markdown
    markdown_texts = [m.value for m in at.markdown]
    has_disclaimer = any("Disclaimer" in t or "AI assistant" in t for t in markdown_texts)
    assert has_disclaimer


def test_delete_my_data_button_exists():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    # Check sidebar button
    delete_buttons = [b for b in at.sidebar.button if "Delete My Data" in b.label]
    assert len(delete_buttons) == 1
