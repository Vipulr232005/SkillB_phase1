import logging
import os

logger = logging.getLogger(__name__)


def generate_session_summary(session) -> str:
    """
    Generate an AI summary for a completed session.

    Uses Gemini 2.5 Flash via google-genai. Reads GEMINI_API_KEY from env.
    Returns "" and logs on missing key or any API error — never raises.
    """
    # Config-driven: read from settings or env (same pattern as JITSI_BASE_URL/STT_PROVIDER)
    from django.conf import settings as _settings
    _raw = getattr(_settings, "GEMINI_API_KEY", None)
    if _raw is None:
        _raw = os.environ.get("GEMINI_API_KEY", "")
    api_key = str(_raw or "").strip()
    if not api_key:
        logger.warning("GEMINI_API_KEY not set — skipping summary generation")
        return ""

    skill_name = getattr(getattr(session, "skill", None), "name", "") or "this skill"
    # Prefer transcript when present, else fall back to notes (existing behavior)
    transcript = ""
    try:
        rec = getattr(session, "recording", None)
        if rec is not None:
            # May be not prefetched — try to get transcript safely
            transcript = (getattr(rec, "transcript", "") or "").strip()
    except Exception:
        transcript = ""
    notes = (getattr(session, "notes", "") or "").strip()
    source_text = transcript if transcript else notes
    source_label = "Transcript" if transcript else "Session notes"
    if not source_text:
        logger.warning("No notes/transcript for session %s — skipping summary", getattr(session, "pk", "?"))
        return ""
    # Truncate very long transcripts to keep prompt within token limits
    if len(source_text) > 8000:
        source_text = source_text[:8000] + "..."
    prompt = (
        f"You are an AI assistant helping students summarize a peer learning session.\n"
        f"Skill: {skill_name}\n"
        f"{source_label}: {source_text}\n\n"
        "Generate a concise, readable summary with exactly these sections:\n"
        "1. Topics Covered\n"
        "2. Key Concepts\n"
        "3. Suggested Next Topics\n"
        "Keep it structured with bullet points and friendly tone. "
        "Keep total length under 250 words."
    )

    try:
        from google.genai import Client

        client = Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
        )
        # google-genai response.text is the canonical accessor
        text = getattr(response, "text", None)
        if text:
            text = text.strip()
            if text:
                return text
        # fallback: check candidates
        candidates = getattr(response, "candidates", None) or []
        for cand in candidates:
            content = getattr(cand, "content", None)
            parts = getattr(content, "parts", None) if content else None
            if parts:
                for part in parts:
                    t = getattr(part, "text", "")
                    if t and t.strip():
                        return t.strip()
        logger.warning("Gemini returned empty response for session %s", getattr(session, "pk", "?"))
        return ""
    except Exception as exc:  # noqa: BLE001 — must never raise into request
        logger.warning("generate_session_summary failed for session %s: %s", getattr(session, "pk", "?"), exc)
        return ""
