from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    college = models.CharField(max_length=150, blank=True, default='')
    department = models.CharField(max_length=150, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    credits = models.IntegerField(default=10)
    avatar_url = models.URLField(blank=True, default='')

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


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
