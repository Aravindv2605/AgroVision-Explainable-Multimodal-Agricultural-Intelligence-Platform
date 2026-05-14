"""
voice_handler.py
----------------
Text-to-speech (TTS) for AgroVision Assistant.

Uses gTTS (Google Text-to-Speech) — no API key required.
Returns MP3 audio as bytes for Streamlit st.audio() playback.
Supports English and Tamil.
"""

import io
import re
from typing import Literal

SUPPORTED_LANGS = {
    "English": "en",
    "Tamil": "ta",
}


def text_to_speech(text: str, language: str = "English") -> bytes:
    """
    Convert markdown/text to speech audio bytes.

    Parameters
    ----------
    text     : response text (markdown will be stripped)
    language : 'English' or 'Tamil'

    Returns
    -------
    MP3 bytes (empty bytes on failure)
    """
    lang_code = SUPPORTED_LANGS.get(language, "en")
    clean = _strip_markdown(text)

    # Limit TTS to first 500 chars to keep audio short
    if len(clean) > 500:
        clean = clean[:500] + "... For full details, please read the text response."

    try:
        from gtts import gTTS
        tts = gTTS(text=clean, lang=lang_code, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except ImportError:
        return b""  # gTTS not installed
    except Exception:
        return b""  # Network or other error


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting for cleaner TTS pronunciation."""
    # Remove headers
    text = re.sub(r"#{1,6}\s*", "", text)
    # Remove bold/italic
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
    # Remove links
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Remove table delimiters
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"-{3,}", "", text)
    # Remove backticks
    text = re.sub(r"`+", "", text)
    # Collapse multiple newlines/spaces
    text = re.sub(r"\n{2,}", ". ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()
