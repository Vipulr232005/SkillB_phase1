from django import forms
from allauth.account.forms import SignupForm

from .models import UserProfile


class SkillBridgeSignupForm(SignupForm):
    """Signup with unique username, age, and college (saved to UserProfile)."""

    age = forms.IntegerField(
        label="Age",
        min_value=13,
        max_value=100,
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Your age",
                "autocomplete": "bday-year",
                "min": "13",
                "max": "100",
            }
        ),
    )
    college = forms.CharField(
        label="College",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Your college or university",
                "autocomplete": "organization",
            }
        ),
    )

    def save(self, request):
        user = super().save(request)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.age = self.cleaned_data["age"]
        profile.college = self.cleaned_data["college"].strip()
        profile.save()
        return user
