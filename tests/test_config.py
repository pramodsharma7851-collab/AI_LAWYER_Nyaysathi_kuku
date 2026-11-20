"""Tests for configuration and environment loading."""

import os
from unittest.mock import patch
from core.config import AppConfig, PLACEHOLDER


def test_missing_key_detection():
    config = AppConfig()
    with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=True):
        with patch("core.config.get_fresh_env_dict", return_value={"GEMINI_API_KEY": ""}):
            assert not config.is_api_configured()


def test_placeholder_key_detection():
    config = AppConfig()
    with patch.dict(os.environ, {"GEMINI_API_KEY": PLACEHOLDER}, clear=True):
        with patch("core.config.get_fresh_env_dict", return_value={"GEMINI_API_KEY": PLACEHOLDER}):
            assert not config.is_api_configured()


def test_valid_key_detection():
    config = AppConfig()
    with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSy_fake_test_key_for_unit_tests"}, clear=True):
        with patch("core.config.get_fresh_env_dict", return_value={}):
            assert config.is_api_configured()
            assert config.get_api_key() == "AIzaSy_fake_test_key_for_unit_tests"


def test_default_model_auto():
    config = AppConfig()
    with patch.dict(os.environ, {}, clear=True):
        with patch("core.config.get_fresh_env_dict", return_value={"GEMINI_MODEL": "auto"}):
            assert config.get_model_name() in ["auto", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
