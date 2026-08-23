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
