"""
Transcription service — provider interface behind STT_PROVIDER.

Active provider: gemini (reuse google-genai + GEMINI_API_KEY for both transcription + summary).
Future swap: openai_whisper (wired-but-inert until OPENAI_API_KEY is set).
All providers return "" + log on error, never raise into the worker.
"""
import logging
import os
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


def _transcribe_gemini(audio_path: str) -> str:
    api_key = getattr(settings, "GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
    api_key = api_key.strip() if isinstance(api_key, str) else ""
    if not api_key:
        logger.warning("GEMINI_API_KEY not set — skipping transcription")
        return ""
    if not audio_path or not Path(audio_path).exists():
        logger.warning("Audio file not found for transcription: %s", audio_path)
        return ""
    try:
        from google.genai import Client

        client = Client(api_key=api_key)
        # Upload audio file; then ask Gemini to transcribe verbatim.
        # client.files.upload accepts a file path; fallback to bytes if needed.
        try:
            uploaded = client.files.upload(file=audio_path)
        except TypeError:
            # Some versions expect a file-like; read bytes
            with open(audio_path, "rb") as f:
                uploaded = client.files.upload(file=f)
        prompt = "Transcribe this audio verbatim. Return only the transcript, no commentary."
        # Generate content with the uploaded file + prompt
        # The API expects contents as list; file reference + text
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[uploaded, prompt],
        )
        text = getattr(response, "text", None)
        if text and text.strip():
            return text.strip()
        # fallback candidates
        candidates = getattr(response, "candidates", None) or []
        for cand in candidates:
            content = getattr(cand, "content", None)
            parts = getattr(content, "parts", None) if content else None
            if parts:
                for part in parts:
                    t = getattr(part, "text", "")
                    if t and t.strip():
                        return t.strip()
        logger.warning("Gemini transcription returned empty for %s", audio_path)
        return ""
    except Exception as exc:  # noqa: BLE001 — must never raise
        logger.warning("Gemini transcription failed for %s: %s", audio_path, exc)
        return ""


def _transcribe_openai_whisper(audio_path: str) -> str:
    # Wired-but-inert until OPENAI_API_KEY is set. Do not require openai dep for default path.
    api_key = getattr(settings, "OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
    api_key = api_key.strip() if isinstance(api_key, str) else ""
    if not api_key:
        logger.warning("OPENAI_API_KEY not set — openai_whisper provider inert")
        return ""
    if not audio_path or not Path(audio_path).exists():
        logger.warning("Audio file not found for transcription: %s", audio_path)
        return ""
    try:
        # Lazy import — only needed when this provider is active with a key
        import openai  # type: ignore

        openai.api_key = api_key
        model = getattr(settings, "WHISPER_MODEL", "whisper-1") or "whisper-1"
        with open(audio_path, "rb") as f:
            # openai>=1.0 uses client.audio.transcriptions.create; legacy uses openai.Audio.transcribe
            try:
                client = openai.OpenAI(api_key=api_key)
                resp = client.audio.transcriptions.create(model=model, file=f)
                # resp.text is transcript
                text = getattr(resp, "text", None) or getattr(resp, "transcript", None) or str(resp)
                return text.strip() if isinstance(text, str) else ""
            except AttributeError:
                # fallback legacy
                resp = openai.Audio.transcribe(model, f)  # type: ignore
                text = resp.get("text", "") if isinstance(resp, dict) else getattr(resp, "text", "")
                return text.strip() if isinstance(text, str) else ""
    except Exception as exc:  # noqa: BLE001
        logger.warning("openai_whisper transcription failed for %s: %s", audio_path, exc)
        return ""


def _transcribe_local_whisper(audio_path: str) -> str:
    logger.warning("local_whisper provider not implemented — returning empty")
    return ""


def transcribe(audio_path: str) -> str:
    """
    Provider interface: transcribe(audio_path) -> str
    Selected by STT_PROVIDER (gemini | openai_whisper | local_whisper), default gemini.
    Returns "" on error, never raises.
    """
    provider = (getattr(settings, "STT_PROVIDER", None) or os.environ.get("STT_PROVIDER", "gemini")).strip().lower()
    if provider in ("gemini", "google", "gemini-2.5-flash"):
        return _transcribe_gemini(audio_path)
    if provider in ("openai_whisper", "whisper", "openai"):
        return _transcribe_openai_whisper(audio_path)
    if provider in ("local_whisper", "faster_whisper", "local"):
        return _transcribe_local_whisper(audio_path)
    logger.warning("Unknown STT_PROVIDER=%s — defaulting to gemini", provider)
    return _transcribe_gemini(audio_path)
