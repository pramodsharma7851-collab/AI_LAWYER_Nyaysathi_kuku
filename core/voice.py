"""Voice processing adapter for NyayaSathi.

Accepts audio recordings (WAV/MP3/M4A) from Streamlit audio_input,
transcribes them into text using Gemini's native audio multi-modal understanding
(supporting Hindi, Hinglish, Tamil, Bengali, Marathi, and English),
and returns the transcript for user review and confirmation before submission.
"""

from typing import Optional
from google import genai
from google.genai import types

from core.config import config


class VoiceAdapter:
    """Handles audio transcription with multi-lingual Indian speech recognition."""

    def __init__(self):
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> Optional[genai.Client]:
        if self._client:
            return self._client
        api_key = config.get_api_key()
        if not api_key:
            return None
        self._client = genai.Client(api_key=api_key)
        return self._client

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
        language_hint: str = "Hindi or English",
    ) -> str:
        """Transcribe audio bytes to plain text."""
        if not audio_bytes or len(audio_bytes) < 100:
            return ""

        if not config.is_api_configured():
            return "Sample transcribed text: My landlord has not returned my security deposit."

        client = self._get_client()
        if not client:
            return ""

        model_name = config.get_model_name()
        if model_name == "auto":
            model_name = "gemini-3.5-flash-lite"

        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        prompt = (
            f"Please transcribe the spoken words in this audio exactly as uttered. "
            f"The speaker may be talking in {language_hint}. "
            f"Do not add any preamble, explanations, commentary, or quotes. Output ONLY the exact transcription."
        )

        try:
            res = client.models.generate_content(
                model=model_name,
                contents=[audio_part, prompt],
                config=types.GenerateContentConfig(
                    temperature=0.0,  # Zero temperature for literal speech-to-text
                ),
            )
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            print(f"[WARN] Audio transcription error: {e}")
            return f"[Transcription error: {str(e)[:80]}]"

        return ""


# Global singleton voice adapter
voice_adapter = VoiceAdapter()
