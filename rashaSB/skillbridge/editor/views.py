from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Skill


def home_view(request):
    if request.user.is_authenticated:
        # Fetch or create user profile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        user_teach_count = Skill.objects.filter(user=request.user, skill_type='TEACH').count()
        user_learn_count = Skill.objects.filter(user=request.user, skill_type='LEARN').count()

        # Fetch peer skills available to learn
        peer_skills = Skill.objects.filter(skill_type='TEACH').exclude(user=request.user).order_by('-rating', '-created_at')

        context = {
            'profile': profile,
            'user_teach_count': user_teach_count,
            'user_learn_count': user_learn_count,
            'peer_skills': peer_skills,
        }
        return render(request, "editor/dashboard.html", context)
    else:
        return render(request, "editor/landing.html")


@login_required
def add_skill_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category', 'Programming')
        skill_type = request.POST.get('skill_type', 'TEACH')
        proficiency = request.POST.get('proficiency', 'Intermediate')

        if name:
            Skill.objects.create(
                user=request.user,
                name=name,
                category=category,
                skill_type=skill_type,
                proficiency=proficiency,
            )
    return redirect('home')


def profile_view(request):
    return render(request, "editor/profile.html")
