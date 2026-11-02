"""Speech-to-text for the mock interview microphone, using OpenAI's transcription API."""
from core import config


def transcribe(audio_bytes: bytes, filename: str = "answer.wav") -> str:
    if config.fake_mode():
        return ("In my role as VP of Finance I noticed our budget tracking was all manual, so I built a shared "
                "spreadsheet with automated formulas. I trained the board on it and we cut reconciliation time "
                "by about half.")
    key = config.openai_key()
    if not key:
        raise RuntimeError("Add OPENAI_API_KEY to secrets to use the microphone. You can type your answer instead.")
    from openai import OpenAI
    model = config.get_secret("TRANSCRIBE_MODEL", "whisper-1")
    resp = OpenAI(api_key=key).audio.transcriptions.create(model=model, file=(filename, audio_bytes))
    return resp.text.strip()
