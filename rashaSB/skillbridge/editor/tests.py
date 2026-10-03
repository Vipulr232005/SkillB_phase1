from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import CreditTransaction, Rating, Session, Skill, UserProfile, build_jitsi_url, jitsi_url


class SessionFlowTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user("teacher", "t@example.com", "pass12345")
        self.learner = User.objects.create_user("learner", "l@example.com", "pass12345")
        self.skill = Skill.objects.create(
            user=self.teacher, name="Python", category="Programming", skill_type="TEACH"
        )

    def test_request_accept_join_complete_rate_credits(self):
        self.client.force_login(self.learner)
        resp = self.client.post(reverse("request_session"), {"skill_id": self.skill.pk})
        self.assertEqual(resp.status_code, 302)
        session = Session.objects.get()
        self.assertEqual(session.status, "requested")
        self.assertEqual(UserProfile.objects.get(user=self.learner).credits, 10)

        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("accept_session", args=[session.pk]),
            {"scheduled_at": "2026-08-24T18:00"},
        )
        self.assertEqual(resp.status_code, 302)
        session.refresh_from_db()
        self.assertEqual(session.status, "accepted")
        # room_name is now config-driven and unique per session
        self.assertTrue(session.room_name.startswith("skillbridge-"))
        self.assertEqual(session.meet_url, build_jitsi_url(session.room_name))
        # new behavior: join redirects to embedded room page (config-driven, no hardcoded host)
        resp = self.client.get(reverse("join_session", args=[session.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(f"/sessions/{session.pk}/room/", resp["Location"])
        # room page itself loads external_api.js from JITSI_BASE_URL
        resp = self.client.get(reverse("room", args=[session.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "external_api.js")
        self.assertContains(resp, session.room_name)

        resp = self.client.post(reverse("complete_session", args=[session.pk]), {"notes": "Covered lists"})
        self.assertEqual(resp.status_code, 302)
        session.refresh_from_db()
        self.assertEqual(session.status, "completed")
        self.assertEqual(UserProfile.objects.get(user=self.learner).credits, 9)
        self.assertEqual(UserProfile.objects.get(user=self.teacher).credits, 11)
        self.assertEqual(CreditTransaction.objects.count(), 2)

        self.client.force_login(self.learner)
        self.client.post(reverse("rate_session", args=[session.pk]), {"stars": "5", "comment": "Great"})
        teacher_profile = UserProfile.objects.get(user=self.teacher)
        self.assertEqual(teacher_profile.rating_count, 1)
        self.assertEqual(teacher_profile.average_rating, 5.0)
        self.assertEqual(Rating.objects.count(), 1)

    def test_cancel_does_not_move_credits(self):
        self.client.force_login(self.learner)
        self.client.post(reverse("request_session"), {"skill_id": self.skill.pk})
        session = Session.objects.get()
        self.client.post(reverse("cancel_session", args=[session.pk]))
        session.refresh_from_db()
        self.assertEqual(session.status, "cancelled")
        self.assertEqual(UserProfile.objects.get(user=self.learner).credits, 10)
        self.assertEqual(CreditTransaction.objects.count(), 0)

    def test_discover_hides_private_profiles(self):
        self.teacher.profile.is_public = False
        self.teacher.profile.save()
        self.client.force_login(self.learner)
        resp = self.client.get(reverse("discover"))
        self.assertContains(resp, "No matching teachers")
        self.assertNotContains(resp, 'data-skill-id')


class SessionSummaryTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user("t2", "t2@example.com", "pass12345")
        self.learner = User.objects.create_user("l2", "l2@example.com", "pass12345")
        self.skill = Skill.objects.create(
            user=self.teacher, name="Guitar", category="Music", skill_type="TEACH"
        )
        # create a completed session with notes
        self.session = Session.objects.create(
            learner=self.learner,
            teacher=self.teacher,
            skill=self.skill,
            status="accepted",
        )
        self.client.force_login(self.learner)
        self.client.post(reverse("accept_session", args=[self.session.pk]), {"scheduled_at": "2026-08-24T18:00"})
        # need teacher to accept, then learner or teacher completes
        self.client.force_login(self.teacher)
        self.client.post(reverse("accept_session", args=[self.session.pk]), {"scheduled_at": "2026-08-24T18:00"})
        self.client.force_login(self.learner)
        # complete via view to ensure notes saved correctly; use direct update for brevity
        self.session.refresh_from_db()
        # manually complete to avoid credit issues in setup
        from django.utils import timezone

        self.session.status = "completed"
        self.session.notes = "Covered chords and strumming patterns"
        self.session.completed_at = timezone.now()
        self.session.save()

    @patch("editor.ai.generate_session_summary")
    def test_generate_summary_saves_and_displays(self, mock_gen):
        mock_gen.return_value = "Topics Covered: chords\nKey Concepts: G C D\nSuggested Next: barre chords"
        self.client.force_login(self.learner)
        resp = self.client.post(reverse("generate_summary", args=[self.session.pk]))
        self.assertEqual(resp.status_code, 302)
        self.session.refresh_from_db()
        self.assertTrue(self.session.ai_summary.startswith("Topics Covered"))
        self.assertIsNotNone(self.session.summary_generated_at)
        # appears on sessions page, not re-called on GET
        resp = self.client.get(reverse("sessions"))
        self.assertContains(resp, "AI summary")
        self.assertContains(resp, "Topics Covered")
        self.assertEqual(mock_gen.call_count, 1)
        # second GET does not call helper again (stored)
        resp = self.client.get(reverse("sessions"))
        self.assertEqual(mock_gen.call_count, 1)

    def test_generate_summary_participant_only_and_gated(self):
        outsider = User.objects.create_user("outsider", "o@example.com", "pass12345")
        self.client.force_login(outsider)
        resp = self.client.post(reverse("generate_summary", args=[self.session.pk]))
        # _own_session returns None -> error redirect
        self.assertEqual(resp.status_code, 302)
        self.session.refresh_from_db()
        self.assertEqual(self.session.ai_summary, "")

        # notes required
        self.session.notes = ""
        self.session.save(update_fields=["notes"])
        self.client.force_login(self.learner)
        resp = self.client.post(reverse("generate_summary", args=[self.session.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.session.ai_summary, "")

        # status must be completed
        self.session.notes = "some notes"
        self.session.status = "accepted"
        self.session.save(update_fields=["notes", "status"])
        resp = self.client.post(reverse("generate_summary", args=[self.session.pk]))
        self.assertEqual(resp.status_code, 302)
        self.session.refresh_from_db()
        self.assertEqual(self.session.ai_summary, "")

    @patch("editor.ai.generate_session_summary", return_value="")
    def test_generate_summary_graceful_on_empty(self, mock_gen):
        self.client.force_login(self.learner)
        resp = self.client.post(reverse("generate_summary", args=[self.session.pk]))
        self.assertEqual(resp.status_code, 302)
        self.session.refresh_from_db()
        self.assertEqual(self.session.ai_summary, "")

    @patch("editor.ai.generate_session_summary", return_value="")
    def test_complete_flow_fallback_without_key(self, mock_gen):
        # credits still move even when summary returns ""
        teacher2 = User.objects.create_user("t3", "t3@example.com", "pass12345")
        learner2 = User.objects.create_user("l3", "l3@example.com", "pass12345")
        skill2 = Skill.objects.create(user=teacher2, name="Python", category="Programming", skill_type="TEACH")
        s = Session.objects.create(learner=learner2, teacher=teacher2, skill=skill2, status="accepted")
        self.client.force_login(learner2)
        resp = self.client.post(reverse("complete_session", args=[s.pk]), {"notes": "did basics"})
        self.assertEqual(resp.status_code, 302)
        s.refresh_from_db()
        self.assertEqual(s.status, "completed")
        self.assertEqual(UserProfile.objects.get(user=learner2).credits, 9)
        self.assertEqual(UserProfile.objects.get(user=teacher2).credits, 11)


class RoomAndRecordingTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user("rteacher", "rt@example.com", "pass12345")
        self.learner = User.objects.create_user("rlearner", "rl@example.com", "pass12345")
        self.skill = Skill.objects.create(user=self.teacher, name="Piano", category="Music", skill_type="TEACH")
        self.session = Session.objects.create(learner=self.learner, teacher=self.teacher, skill=self.skill, status="requested")
        self.client.force_login(self.teacher)
        self.client.post(reverse("accept_session", args=[self.session.pk]), {"scheduled_at": "2026-08-24T18:00"})
        self.session.refresh_from_db()

    def test_room_requires_accepted_and_participant(self):
        outsider = User.objects.create_user("outsider2", "o2@example.com", "pass12345")
        self.client.force_login(outsider)
        resp = self.client.get(reverse("room", args=[self.session.pk]))
        self.assertEqual(resp.status_code, 302)
        # learner can access
        self.client.force_login(self.learner)
        resp = self.client.get(reverse("room", args=[self.session.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "external_api.js")
        self.assertContains(resp, self.session.room_name)

    def test_upload_consent_and_audio_gated(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from editor.models import SessionRecording
        self.client.force_login(self.learner)
        # without consent -> 400
        audio = SimpleUploadedFile("a.webm", b"fake", content_type="audio/webm")
        resp = self.client.post(reverse("upload_audio", args=[self.session.pk]), {"audio": audio})
        self.assertEqual(resp.status_code, 400)
        # set consent
        resp = self.client.post(reverse("upload_consent", args=[self.session.pk]), {"consent": "true"})
        self.assertEqual(resp.status_code, 200)
        rec = SessionRecording.objects.get(session=self.session)
        self.assertTrue(rec.consent_learner)
        # now upload succeeds
        audio2 = SimpleUploadedFile("b.webm", b"fake2", content_type="audio/webm")
        with patch("editor.tasks.transcribe_recording") as mock_task:
            # avoid needing Celery
            resp = self.client.post(reverse("upload_audio", args=[self.session.pk]), {"audio": audio2, "duration_seconds": "12"})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["status"], "uploaded")
        rec.refresh_from_db()
        self.assertEqual(rec.status, "uploaded")
        self.assertTrue(rec.audio_file.name.endswith(".webm"))
        self.assertEqual(rec.duration_seconds, 12)
        # participant-only
        outsider = User.objects.create_user("outsider3", "o3@example.com", "pass12345")
        self.client.force_login(outsider)
        audio3 = SimpleUploadedFile("c.webm", b"x", content_type="audio/webm")
        resp = self.client.post(reverse("upload_audio", args=[self.session.pk]), {"audio": audio3})
        self.assertIn(resp.status_code, [302, 403])


class TranscriptionTaskTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user("tt", "tt@example.com", "pass12345")
        self.learner = User.objects.create_user("ll", "ll@example.com", "pass12345")
        self.skill = Skill.objects.create(user=self.teacher, name="Drums", category="Music", skill_type="TEACH")
        self.session = Session.objects.create(learner=self.learner, teacher=self.teacher, skill=self.skill, status="completed", room_name="skillbridge-test")
        from editor.models import SessionRecording
        from django.core.files.base import ContentFile
        self.recording = SessionRecording.objects.create(session=self.session, status="uploaded", consent_learner=True)
        self.recording.audio_file.save("dummy.webm", ContentFile(b"dummy audio"))
        self.recording.save()

    @patch("editor.tasks.transcribe")
    def test_task_sets_done_on_transcript(self, mock_trans):
        from editor.tasks import transcribe_recording
        mock_trans.return_value = "hello transcript"
        transcribe_recording(self.recording.id)
        self.recording.refresh_from_db()
        self.assertEqual(self.recording.status, "done")
        self.assertEqual(self.recording.transcript, "hello transcript")
        self.assertEqual(self.recording.error, "")

    @patch("editor.tasks.transcribe")
    def test_task_sets_failed_on_empty(self, mock_trans):
        from editor.tasks import transcribe_recording
        mock_trans.return_value = ""
        transcribe_recording(self.recording.id)
        self.recording.refresh_from_db()
        self.assertEqual(self.recording.status, "failed")
        self.assertIn("empty", self.recording.error.lower())

    def test_transcription_interface_never_raises(self):
        from editor.transcription import transcribe
        # no key / missing file -> ""
        result = transcribe("/nonexistent/path.webm")
        self.assertEqual(result, "")


class SummaryPrefersTranscriptTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user("st", "st2@example.com", "pass12345")
        self.learner = User.objects.create_user("sl", "sl2@example.com", "pass12345")
        self.skill = Skill.objects.create(user=self.teacher, name="Guitar2", category="Music", skill_type="TEACH")
        self.session = Session.objects.create(learner=self.learner, teacher=self.teacher, skill=self.skill, status="completed", notes="notes fallback", room_name="skillbridge-x")
        from editor.models import SessionRecording
        self.recording = SessionRecording.objects.create(session=self.session, status="done", transcript="transcript hello", consent_learner=True)

    @patch("google.genai.Client")
    def test_prefers_transcript(self, mock_client):
        # Mock Gemini client to capture prompt
        mock_instance = mock_client.return_value
        mock_resp = type("obj", (), {"text": "summary output", "candidates": []})()
        mock_instance.models.generate_content.return_value = mock_resp
        from editor.ai import generate_session_summary
        # need GEMINI_API_KEY set for this test (ai now reads from settings)
        from django.conf import settings
        old = getattr(settings, "GEMINI_API_KEY", "")
        settings.GEMINI_API_KEY = "fake-key-for-test"
        try:
            result = generate_session_summary(self.session)
            self.assertEqual(result, "summary output")
            # check prompt used transcript, not notes
            call_kwargs = mock_instance.models.generate_content.call_args[1]
            contents = call_kwargs.get("contents", "")
            self.assertIn("transcript hello", str(contents))
            self.assertNotIn("notes fallback", str(contents))
        finally:
            settings.GEMINI_API_KEY = old

    @patch("google.genai.Client")
    def test_fallback_to_notes_when_no_transcript(self, mock_client):
        self.recording.transcript = ""
        self.recording.save(update_fields=["transcript"])
        mock_instance = mock_client.return_value
        mock_resp = type("obj", (), {"text": "summary from notes", "candidates": []})()
        mock_instance.models.generate_content.return_value = mock_resp
        from editor.ai import generate_session_summary
        from django.conf import settings
        old = getattr(settings, "GEMINI_API_KEY", "")
        settings.GEMINI_API_KEY = "fake-key-for-test"
        try:
            result = generate_session_summary(self.session)
            self.assertEqual(result, "summary from notes")
            call_kwargs = mock_instance.models.generate_content.call_args[1]
            contents = call_kwargs.get("contents", "")
            self.assertIn("notes fallback", str(contents))
        finally:
            settings.GEMINI_API_KEY = old

    def test_generate_summary_view_allows_transcript_without_notes(self):
        # notes empty but transcript exists -> should still generate
        self.session.notes = ""
        self.session.save(update_fields=["notes"])
        self.client.force_login(self.learner)
        with patch("editor.ai.generate_session_summary", return_value="summary from transcript") as mock_gen:
            resp = self.client.post(reverse("generate_summary", args=[self.session.pk]))
            self.assertEqual(resp.status_code, 302)
            # ensure helper was called (transcript path)
            self.assertTrue(mock_gen.called)
            self.session.refresh_from_db()
            self.assertEqual(self.session.ai_summary, "summary from transcript")


class RecommendationTests(TestCase):
    def setUp(self):
        # Clean slate for recommendations
        self.user = User.objects.create_user("rec_user", "rec@example.com", "pass12345")
        self.user.profile.learn_skills = "Spanish"
        self.user.profile.save()
        # Also add a LEARN skill to test union
        Skill.objects.create(user=self.user, name="Guitar", category="Music", skill_type="LEARN", proficiency="Beginner")

    def _create_teacher(self, username, skill_name, category="Languages", proficiency="Intermediate", is_public=True, allow_requests=True, avg_rating=0, rating_count=0):
        t = User.objects.create_user(username, f"{username}@example.com", "pass12345")
        # Ensure profile exists and set visibility/rating
        profile, _ = UserProfile.objects.get_or_create(user=t)
        profile.is_public = is_public
        profile.allow_requests = allow_requests
        profile.average_rating = avg_rating
        profile.rating_count = rating_count
        profile.save()
        skill = Skill.objects.create(user=t, name=skill_name, category=category, skill_type="TEACH", proficiency=proficiency)
        return t, skill

    def test_interest_ranking(self):
        # Spanish teacher should outrank unrelated
        t1, s1 = self._create_teacher("spanish_teacher", "Spanish Conversation", category="Languages", proficiency="Advanced", avg_rating=1, rating_count=0)
        t2, s2 = self._create_teacher("unrelated_teacher", "Basketball Coaching", category="Music", proficiency="Beginner", avg_rating=0)
        from editor.recommendations import recommend_teachers
        recs = recommend_teachers(self.user, limit=6)
        ids = [s.id for s in recs]
        self.assertIn(s1.id, ids)
        self.assertIn(s2.id, ids)
        # Spanish should be before unrelated due to +10 interest
        self.assertLess(ids.index(s1.id), ids.index(s2.id))

    def test_each_has_reason(self):
        self._create_teacher("t_a", "spanish basics", category="Languages")
        self._create_teacher("t_b", "photography", category="Design", avg_rating=4.5, rating_count=10)
        from editor.recommendations import recommend_teachers
        recs = recommend_teachers(self.user, limit=6)
        self.assertTrue(len(recs) > 0)
        for s in recs:
            self.assertTrue(hasattr(s, "reason"))
            self.assertTrue(isinstance(s.reason, str) and s.reason.strip() != "")

    def test_excludes_self_and_private_and_dedupes(self):
        # Self skill should be excluded
        Skill.objects.create(user=self.user, name="Spanish Conversation", category="Languages", skill_type="TEACH", proficiency="Advanced")
        # Private profile excluded
        self._create_teacher("private_teacher", "Spanish Private", category="Languages", is_public=False)
        # Not allow_requests excluded
        self._create_teacher("blocked_teacher", "Spanish Blocked", category="Languages", allow_requests=False)
        # Two skills same teacher -> dedupe to one
        t_multi, s_a = self._create_teacher("multi_teacher", "Spanish A", category="Languages")
        s_b = Skill.objects.create(user=t_multi, name="Spanish B", category="Languages", skill_type="TEACH", proficiency="Advanced")
        from editor.recommendations import recommend_teachers
        recs = recommend_teachers(self.user, limit=10)
        # No self
        for s in recs:
            self.assertNotEqual(s.user_id, self.user.id)
        # private/blocked not in results
        rec_ids = [s.id for s in recs]
        # Ensure private teacher's skill not present (we didn't keep reference but check via query)
        private_skills = Skill.objects.filter(user__username="private_teacher")
        for ps in private_skills:
            self.assertNotIn(ps.id, rec_ids)
        # dedupe: multi_teacher appears once
        counts = {}
        for s in recs:
            counts[s.user_id] = counts.get(s.user_id, 0) + 1
        for uid, cnt in counts.items():
            self.assertEqual(cnt, 1, f"teacher {uid} appears {cnt} times")
        # specifically multi_teacher once
        self.assertEqual(counts.get(t_multi.id, 0), 1)

    def test_cold_start_returns_top_rated(self):
        # Cold user: no learn_skills, no LEARN skills
        cold = User.objects.create_user("cold_user", "cold@example.com", "pass12345")
        cold.profile.learn_skills = ""
        cold.profile.save()
        # Ensure no LEARN skills for cold
        Skill.objects.filter(user=cold, skill_type="LEARN").delete()
        # Create teachers — use Skill rating to control _peer_skills ordering (cold fallback uses Skill.rating)
        t1, s1 = self._create_teacher("top_teacher", "Python", category="Programming", avg_rating=4.9, rating_count=15)
        t2, s2 = self._create_teacher("low_teacher", "Basketball", category="Music", avg_rating=1.0, rating_count=1)
        s1.rating = 5.0
        s1.save(update_fields=["rating"])
        s2.rating = 1.0
        s2.save(update_fields=["rating"])
        from editor.recommendations import recommend_teachers
        recs = recommend_teachers(cold, limit=6)
        self.assertTrue(len(recs) > 0)
        for s in recs:
            self.assertTrue(hasattr(s, "reason"))
            self.assertEqual(s.reason, "Top rated right now")
        # Should be ordered by Skill.rating desc via _peer_skills
        names = [s.name for s in recs]
        if "Python" in names and "Basketball" in names:
            self.assertLess(names.index("Python"), names.index("Basketball"))
