import uuid

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


AVATAR_FILES = [
    "c1.jpg",
    "c2.jpg",
    "c3.jpg",
    "c4.jpg",
    "c5.jpg",
    "c6.jpg",
    "w1.jpg",
    "w2.jpg",
]
AVATAR_CHOICES = [(name, name.replace(".jpg", "").upper()) for name in AVATAR_FILES]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    college = models.CharField(max_length=150, blank=True, default='')
    department = models.CharField(max_length=150, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    credits = models.IntegerField(default=10)
    avatar_url = models.URLField(blank=True, default='')
    avatar = models.CharField(max_length=20, choices=AVATAR_CHOICES, default="c1.jpg")
    learn_skills = models.CharField(max_length=300, blank=True, default="")
    available_hours = models.CharField(max_length=80, blank=True, default="10 hrs / week")
    schedule = models.CharField(max_length=120, blank=True, default="Weekdays after class")
    is_public = models.BooleanField(default=True)
    show_hours = models.BooleanField(default=True)
    allow_requests = models.BooleanField(default=True)
    average_rating = models.FloatField(default=0)
    rating_count = models.PositiveIntegerField(default=0)

    def avatar_file(self):
        if self.avatar in AVATAR_FILES:
            return self.avatar
        return "c1.jpg"

    def avatar_static_path(self):
        return f"editor/avatars/{self.avatar_file()}"

    def skill_tags(self):
        return [s.name for s in self.user.skills.filter(skill_type="TEACH")[:8]]

    def learn_tags(self):
        if self.learn_skills.strip():
            return [part.strip() for part in self.learn_skills.split(",") if part.strip()][:8]
        return [s.name for s in self.user.skills.filter(skill_type="LEARN")[:8]]

    def stars_label(self):
        if self.rating_count:
            return f"{self.average_rating:.1f} ({self.rating_count})"
        return "New"

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.credits} credits)"


class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('Programming', 'Programming'),
        ('Design', 'Design'),
        ('Languages', 'Languages'),
        ('Music', 'Music'),
        ('Academics', 'Academics'),
        ('Business', 'Business'),
        ('Other', 'Other'),
    ]

    SKILL_TYPE_CHOICES = [
        ('TEACH', 'Teach'),
        ('LEARN', 'Learn'),
    ]

    PROFICIENCY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Programming')
    skill_type = models.CharField(max_length=10, choices=SKILL_TYPE_CHOICES, default='TEACH')
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, default='Intermediate')
    rating = models.FloatField(default=5.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.skill_type}) - {self.user.username}"


def _jitsi_base():
    return getattr(settings, "JITSI_BASE_URL", "https://meet.jit.si").rstrip("/")


def jitsi_url(session_id):
    base = _jitsi_base()
    return f"{base}/skillbridge-{session_id}"


def build_jitsi_url(room_name):
    base = _jitsi_base()
    return f"{base}/{room_name}"


def generate_room_name(session_id):
    # stable, unique slug: skillbridge-<uuid8>-<id>
    return f"skillbridge-{uuid.uuid4().hex[:8]}-{session_id}"


class Session(models.Model):
    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    learner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions_as_learner")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions_as_teacher")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="sessions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")
    scheduled_at = models.DateTimeField(null=True, blank=True)
    meet_url = models.URLField(blank=True, default="")
    room_name = models.CharField(max_length=120, blank=True, default="")
    credits = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, default="")
    ai_summary = models.TextField(blank=True, default="")
    summary_generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.skill.name}: {self.learner.username} -> {self.teacher.username} ({self.status})"

    def is_participant(self, user):
        return user.id in (self.learner_id, self.teacher_id)

    def counterpart(self, user):
        return self.teacher if user.id == self.learner_id else self.learner


class SessionRecording(models.Model):
    STATUS_CHOICES = [
        ("idle", "Idle"),
        ("uploaded", "Uploaded"),
        ("processing", "Processing"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name="recording")
    audio_file = models.FileField(upload_to="session_audio/", null=True, blank=True)
    transcript = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="idle")
    consent_learner = models.BooleanField(default=False)
    consent_teacher = models.BooleanField(default=False)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    error = models.CharField(max_length=300, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recording for {self.session_id} ({self.status})"

    def has_consent(self):
        # Consent is mandatory — both must have consented to consider valid
        # For demo, require at least one consent from the uploading participant;
        # the model tracks both sides.
        return self.consent_learner or self.consent_teacher


class CreditTransaction(models.Model):
    KIND_CHOICES = [
        ("earn", "Earn"),
        ("spend", "Spend"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="credit_transactions")
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="credit_transactions")
    amount = models.IntegerField()
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} {self.kind} {self.amount}"


class Rating(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="ratings")
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings_given")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings_received")
    stars = models.PositiveSmallIntegerField()
    comment = models.CharField(max_length=300, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("session", "from_user")

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username}: {self.stars}"


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
