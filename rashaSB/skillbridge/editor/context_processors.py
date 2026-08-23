from .models import AVATAR_FILES, UserProfile


def bridge_profile(request):
    if not request.user.is_authenticated:
        return {"user_profile": None, "avatar_files": AVATAR_FILES}
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return {"user_profile": profile, "avatar_files": AVATAR_FILES}
