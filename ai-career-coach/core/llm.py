"""Thin wrapper around the Claude API: plain text calls, JSON calls, and model fallback."""
import json
import re

from core import config

# Tried in order if the configured model isn't available on the account.
FALLBACK_MODELS = ["claude-sonnet-4-5", "claude-3-7-sonnet-latest", "claude-3-5-sonnet-latest"]

_client = None
_working_model = None


def client():
    global _client
    if _client is None:
        import anthropic
        key = config.anthropic_key()
        if not key:
            raise RuntimeError("No ANTHROPIC_API_KEY found. Add it in Streamlit secrets (see README).")
        _client = anthropic.Anthropic(api_key=key)
    return _client


def create_message(**kwargs):
    """messages.create with automatic fallback to an older model name if the configured one 404s."""
    global _working_model
    import anthropic
    candidates = [_working_model] if _working_model else [config.claude_model()] + FALLBACK_MODELS
    last_err = None
    for m in candidates:
        try:
            resp = client().messages.create(model=m, **kwargs)
            _working_model = m
            return resp
        except anthropic.NotFoundError as e:
            last_err = e
            continue
    raise last_err


def ask(system: str, prompt: str, max_tokens: int = 2000, temperature: float = 0.4) -> str:
    if config.fake_mode():
        from core import fake
        return fake.text(system, prompt)
    resp = create_message(
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start, end = text.find(open_c), text.rfind(close_c)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("The AI response was not valid JSON. Try again.")


def ask_json(system: str, prompt: str, max_tokens: int = 3000, temperature: float = 0.3):
    if config.fake_mode():
        from core import fake
        return fake.json_for(system, prompt)
    system = system + "\n\nRespond with ONLY valid JSON. No markdown fences, no commentary."
    out = ask(system, prompt, max_tokens=max_tokens, temperature=temperature)
    try:
        return extract_json(out)
    except ValueError:
        # one repair attempt
        fixed = ask("You fix malformed JSON. Return only the corrected JSON.", out, max_tokens=max_tokens, temperature=0)
        return extract_json(fixed)
