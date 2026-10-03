from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import CreditTransaction, Rating, Session, Skill, UserProfile, jitsi_url


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
        self.assertEqual(session.meet_url, jitsi_url(session.pk))

        resp = self.client.get(reverse("join_session", args=[session.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("meet.jit.si", resp["Location"])

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
        self.assertContains(resp, "AI Summary")
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
