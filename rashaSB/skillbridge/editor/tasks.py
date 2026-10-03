import logging

from celery import shared_task

from .models import SessionRecording
from .transcription import transcribe

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=1, default_retry_delay=5)
def transcribe_recording(self, recording_id):
    """
    Async transcription task: processing -> transcribe(audio_path) -> done/failed.
    Never raises into the worker — logs and marks failed instead.
    """
    try:
        recording = SessionRecording.objects.get(id=recording_id)
    except SessionRecording.DoesNotExist:
        logger.warning("transcribe_recording: recording %s not found", recording_id)
        return

    if not recording.audio_file:
        recording.status = "failed"
        recording.error = "no audio file"
        recording.save(update_fields=["status", "error"])
        return

    recording.status = "processing"
    recording.error = ""
    recording.save(update_fields=["status", "error"])

    try:
        # Resolve storage path to filesystem path for transcription
        audio_path = recording.audio_file.path  # local MEDIA_ROOT; for S3 this would need download
    except Exception as exc:
        # S3 path not locally available — log and fail gracefully
        logger.warning("Cannot resolve audio path for recording %s: %s", recording_id, exc)
        recording.status = "failed"
        recording.error = "storage path unavailable"
        recording.save(update_fields=["status", "error"])
        return

    try:
        transcript = transcribe(audio_path)
    except Exception as exc:  # noqa: BLE001 — provider must not raise, but guard anyway
        logger.warning("transcribe failed for %s: %s", recording_id, exc)
        recording.status = "failed"
        recording.error = str(exc)[:300]
        recording.save(update_fields=["status", "error"])
        return

    if not transcript:
        # Provider returned "" — treat as failed with message (keeps status visible)
        # If the provider is inert (no key), this is expected in CI
        recording.status = "failed"
        recording.error = "transcription returned empty (check GEMINI_API_KEY/STT_PROVIDER)"
        recording.save(update_fields=["status", "error"])
        return

    recording.transcript = transcript
    recording.status = "done"
    recording.error = ""
    recording.save(update_fields=["transcript", "status", "error"])
