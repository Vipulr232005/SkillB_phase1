from django.core.management.base import BaseCommand

from editor.models import SessionRecording
from editor.tasks import transcribe_recording


class Command(BaseCommand):
    help = "Transcribe pending SessionRecordings without a broker (no-broker fallback for debugging)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=10, help="Max recordings to process")

    def handle(self, *args, **options):
        limit = options["limit"]
        qs = SessionRecording.objects.filter(status__in=["uploaded", "failed"]).order_by("created_at")[:limit]
        if not qs:
            self.stdout.write("No pending recordings (uploaded/failed).")
            return
        for rec in qs:
            self.stdout.write(f"Transcribing recording {rec.id} (session {rec.session_id}, status {rec.status})...")
            # Run synchronously — bypass broker
            transcribe_recording(rec.id)
            rec.refresh_from_db()
            self.stdout.write(f"  -> {rec.status}: transcript len={len(rec.transcript)} error={rec.error!r}")
        self.stdout.write(self.style.SUCCESS(f"Done. Processed {len(qs)} recording(s)."))
