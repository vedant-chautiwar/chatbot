import pytest
from unittest.mock import patch
from app.config import Settings, settings
from app.agents.graph import get_chat_model


def test_settings_load_defaults():
    """Verify Settings initializes with expected defaults and properties."""
    assert settings.GROQ_MODEL == "openai/gpt-oss-120b"
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.effective_jwt_secret is not None
    assert len(settings.effective_jwt_secret) > 0
    assert isinstance(settings.cors_origins, list)


def test_settings_clean_api_keys():
    """Verify that quotes and surrounding whitespace are stripped from API keys."""
    test_settings = Settings(
        GROQ_API_KEY='  "gsk_test_clean_key"  ',
        TAVILY_API_KEY=" 'tvly-test_clean_key' ",
    )
    assert test_settings.GROQ_API_KEY == "gsk_test_clean_key"
    assert test_settings.TAVILY_API_KEY == "tvly-test_clean_key"


def test_get_chat_model_testing_environment():
    """In testing environment, get_chat_model uses fallback test key without raising."""
    with patch.object(settings, "ENVIRONMENT", "testing"):
        with patch.object(settings, "GROQ_API_KEY", ""):
            model = get_chat_model()
            assert model is not None
            assert model.model_name == settings.GROQ_MODEL


def test_get_chat_model_raises_missing_key_in_non_testing(monkeypatch):
    """In non-testing environment, missing GROQ_API_KEY raises a descriptive ValueError."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    with pytest.raises(ValueError, match="GROQ_API_KEY is not configured"):
        get_chat_model(api_key=None)


def test_get_chat_model_raises_placeholder_key_in_non_testing(monkeypatch):
    """In non-testing environment, placeholder GROQ_API_KEY raises ValueError."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_your_groq_api_key_here")

    with pytest.raises(ValueError, match="GROQ_API_KEY is not configured"):
        get_chat_model(api_key=None)


def test_get_chat_model_succeeds_with_valid_key(monkeypatch):
    """Providing a valid key initializes ChatGroq with expected parameters."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_real_format_mock_key_1234567890abcdef")

    model = get_chat_model()
    assert model is not None
    assert model.model_name == settings.GROQ_MODEL


def test_validate_runtime_keys(caplog):
    """validate_runtime_keys logs warning when required keys are missing in production."""
    test_settings = Settings(
        ENVIRONMENT="production",
        GROQ_API_KEY="",
        TAVILY_API_KEY="",
    )
    with caplog.at_level("WARNING"):
        test_settings.validate_runtime_keys()
        assert "Missing environment variables" in caplog.text


def test_no_supabase_dependency():
    """Verify Settings does not require or contain obsolete Supabase fields."""
    assert not hasattr(settings, "SUPABASE_URL")
    assert not hasattr(settings, "SUPABASE_JWT_SECRET")
    assert not hasattr(settings, "SUPABASE_JWT_ALGORITHM")
