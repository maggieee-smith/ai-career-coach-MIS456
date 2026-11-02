"""Reads API keys and settings from Streamlit secrets (when deployed) or environment variables (local)."""
import os


def get_secret(name: str, default: str | None = None) -> str | None:
    try:
        import streamlit as st
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


def anthropic_key():
    return get_secret("ANTHROPIC_API_KEY")


def openai_key():
    return get_secret("OPENAI_API_KEY")


def claude_model():
    return get_secret("CLAUDE_MODEL", "claude-sonnet-5-5")


def fake_mode() -> bool:
    """Offline test mode: returns canned AI responses so the UI can be tested without API keys."""
    return os.getenv("CAREER_COACH_FAKE") == "1"
