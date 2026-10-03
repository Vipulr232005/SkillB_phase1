from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from django.conf import settings

from .models import (
    AVATAR_FILES,
    CreditTransaction,
    Rating,
    Session,
    SessionRecording,
    Skill,
    UserProfile,
    build_jitsi_url,
    generate_room_name,
    jitsi_url,
)

OPEN_STATUSES = ("requested", "accepted")


def _peer_skills(user, query="", category=""):
    qs = (
        Skill.objects.filter(skill_type="TEACH", user__profile__is_public=True)
        .exclude(user=user)
        .select_related("user", "user__profile")
        .order_by("-rating", "-created_at")
    )
    if query:
        qs = qs.filter(
            Q(name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
        )
    if category:
        qs = qs.filter(category=category)
    skills = list(qs)
    for skill in skills:
        UserProfile.objects.get_or_create(user=skill.user)
    return skills


def _dash_context(request, open_edit=False):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return {
        "profile": profile,
        "user_teach_count": Skill.objects.filter(user=request.user, skill_type="TEACH").count(),
        "user_learn_count": Skill.objects.filter(user=request.user, skill_type="LEARN").count(),
        "peer_skills": _peer_skills(request.user),
        "open_edit_profile": open_edit,
    }


def _own_session(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if not session.is_participant(request.user):
        return None
    return session


def _recompute_rating(user):
    stats = Rating.objects.filter(to_user=user).aggregate(avg=Avg("stars"), n=Count("id"))
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.average_rating = round(stats["avg"] or 0, 2)
    profile.rating_count = stats["n"] or 0
    profile.save(update_fields=["average_rating", "rating_count"])


def home_view(request):
    if request.user.is_authenticated:
        return render(request, "editor/dashboard.html", _dash_context(request))
    return render(request, "editor/landing.html")


@login_required
def add_skill_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Skill.objects.create(
                user=request.user,
                name=name,
                category=request.POST.get("category", "Programming"),
                skill_type=request.POST.get("skill_type", "TEACH"),
                proficiency=request.POST.get("proficiency", "Intermediate"),
            )
            messages.success(request, "Skill saved.")
    return redirect("home")


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        action = request.POST.get("action", "profile")
        if action == "privacy":
            profile.is_public = request.POST.get("is_public") == "on"
            profile.show_hours = request.POST.get("show_hours") == "on"
            profile.allow_requests = request.POST.get("allow_requests") == "on"
            profile.save()
            messages.success(request, "Privacy settings saved.")
            return redirect("home")

        avatar = request.POST.get("avatar", profile.avatar)
        if avatar in AVATAR_FILES:
            profile.avatar = avatar
        profile.bio = request.POST.get("bio", "").strip()
        profile.learn_skills = request.POST.get("learn_skills", "").strip()
        profile.available_hours = request.POST.get("available_hours", "").strip()
        profile.schedule = request.POST.get("schedule", "").strip()
        profile.college = request.POST.get("college", profile.college).strip()
        profile.department = request.POST.get("department", profile.department).strip()
        first_name = request.POST.get("first_name", "").strip()
        if first_name:
            request.user.first_name = first_name
            request.user.save(update_fields=["first_name"])
        profile.save()
        messages.success(request, "Profile updated.")
        return redirect("home")

    return render(request, "editor/dashboard.html", _dash_context(request, open_edit=True))


@login_required
def discover_view(request):
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    return render(
        request,
        "editor/discover.html",
        {
            "peer_skills": _peer_skills(request.user, query, category),
            "query": query,
            "category": category,
            "categories": [c[0] for c in Skill.CATEGORY_CHOICES],
        },
    )


@login_required
def public_profile_view(request, username):
    peer = get_object_or_404(User, username=username)
    profile, _ = UserProfile.objects.get_or_create(user=peer)
    if not profile.is_public and peer != request.user:
        messages.error(request, "This profile is private.")
        return redirect("discover")
    return render(
        request,
        "editor/public_profile.html",
        {
            "peer": peer,
            "peer_profile": profile,
            "teach_skills": Skill.objects.filter(user=peer, skill_type="TEACH"),
        },
    )


@login_required
@require_POST
def request_session_view(request):
    skill = get_object_or_404(Skill, pk=request.POST.get("skill_id"), skill_type="TEACH")
    teacher = skill.user
    learner_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    teacher_profile, _ = UserProfile.objects.get_or_create(user=teacher)

    if teacher == request.user:
        messages.error(request, "You cannot request a session with yourself.")
        return redirect("discover")
    if not teacher_profile.allow_requests:
        messages.error(request, "This user is not accepting requests.")
        return redirect("public_profile", username=teacher.username)
    if learner_profile.credits < 1:
        messages.error(request, "You need at least 1 credit to request a session.")
        return redirect("credits")
    if Session.objects.filter(
        learner=request.user, teacher=teacher, skill=skill, status__in=OPEN_STATUSES
    ).exists():
        messages.info(request, "You already have an open request for this skill.")
        return redirect("sessions")

    Session.objects.create(learner=request.user, teacher=teacher, skill=skill)
    messages.success(request, "Request sent.")
    return redirect("sessions")


@login_required
def sessions_view(request):
    incoming = Session.objects.filter(teacher=request.user, status="requested").select_related("learner", "skill")
    sent = Session.objects.filter(learner=request.user, status="requested").select_related("teacher", "skill")
    upcoming = (
        Session.objects.filter(status="accepted")
        .filter(Q(learner=request.user) | Q(teacher=request.user))
        .select_related("learner", "teacher", "skill")
    )
    history = (
        Session.objects.filter(Q(learner=request.user) | Q(teacher=request.user))
        .filter(status__in=("completed", "rejected", "cancelled"))
        .select_related("learner", "teacher", "skill")
    )
    rated_ids = set(Rating.objects.filter(from_user=request.user).values_list("session_id", flat=True))
    # Attach transcript availability to history items for template (avoid N+1, keep existing history queryset)
    history = list(history)  # evaluate once
    if history:
        from .models import SessionRecording
        recs = {r.session_id: r for r in SessionRecording.objects.filter(session_id__in=[s.id for s in history])}
        for s in history:
            r = recs.get(s.id)
            s.has_transcript = bool(r and (r.transcript or "").strip())
            s.transcript_text = (r.transcript if r else "")
            s.recording_status = (r.status if r else "")
    return render(
        request,
        "editor/sessions.html",
        {
            "incoming": incoming,
            "sent": sent,
            "upcoming": upcoming,
            "history": history,
            "rated_ids": rated_ids,
        },
    )


@login_required
@require_POST
def accept_session_view(request, pk):
    session = get_object_or_404(Session, pk=pk, teacher=request.user, status="requested")
    raw = request.POST.get("scheduled_at", "").strip()
    if raw:
        try:
            parsed = datetime.fromisoformat(raw.replace(" ", "T"))
            session.scheduled_at = timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed
        except ValueError:
            session.scheduled_at = timezone.now()
    else:
        session.scheduled_at = timezone.now()
    session.status = "accepted"
    if not session.room_name:
        session.room_name = generate_room_name(session.pk)
    session.meet_url = build_jitsi_url(session.room_name)
    session.save(update_fields=["scheduled_at", "status", "room_name", "meet_url"])
    messages.success(request, "Session accepted. Jitsi room is ready.")
    return redirect("sessions")


@login_required
@require_POST
def reject_session_view(request, pk):
    session = get_object_or_404(Session, pk=pk, teacher=request.user, status="requested")
    session.status = "rejected"
    session.save(update_fields=["status"])
    messages.info(request, "Request rejected.")
    return redirect("sessions")


@login_required
@require_POST
def cancel_session_view(request, pk):
    session = _own_session(request, pk)
    if not session:
        messages.error(request, "That session is not yours.")
        return redirect("sessions")
    if session.status not in OPEN_STATUSES:
        messages.error(request, "This session cannot be cancelled.")
        return redirect("sessions")
    session.status = "cancelled"
    session.save(update_fields=["status"])
    messages.info(request, "Session cancelled. No credits moved.")
    return redirect("sessions")


@login_required
def join_session_view(request, pk):
    # Legacy direct join — now redirects to embedded room page
    session = _own_session(request, pk)
    if not session or session.status != "accepted":
        messages.error(request, "This session is not ready to join.")
        return redirect("sessions")
    if not session.room_name:
        session.room_name = generate_room_name(session.pk)
        session.meet_url = build_jitsi_url(session.room_name)
        session.save(update_fields=["room_name", "meet_url"])
    return redirect("room", pk=session.pk)


@login_required
def room_view(request, pk):
    session = _own_session(request, pk)
    if not session:
        messages.error(request, "That session is not yours.")
        return redirect("sessions")
    if session.status != "accepted":
        messages.error(request, "This room is only available for accepted sessions.")
        return redirect("sessions")
    if not session.room_name:
        session.room_name = generate_room_name(session.pk)
        session.meet_url = build_jitsi_url(session.room_name)
        session.save(update_fields=["room_name", "meet_url"])
    # Ensure a recording row exists for consent tracking
    recording, _ = SessionRecording.objects.get_or_create(session=session)
    jitsi_base = getattr(settings, "JITSI_BASE_URL", "https://meet.jit.si").rstrip("/")
    return render(
        request,
        "editor/room.html",
        {
            "session": session,
            "recording": recording,
            "jitsi_base_url": jitsi_base,
            "room_name": session.room_name,
        },
    )


@login_required
@require_POST
def upload_consent_view(request, pk):
    session = _own_session(request, pk)
    if not session:
        return redirect("sessions")
    recording, _ = SessionRecording.objects.get_or_create(session=session)
    is_learner = request.user.id == session.learner_id
    is_teacher = request.user.id == session.teacher_id
    consent = request.POST.get("consent") == "true"
    if is_learner:
        recording.consent_learner = consent
    if is_teacher:
        recording.consent_teacher = consent
    recording.save(update_fields=["consent_learner", "consent_teacher"])
    # For fetch() call from room.html expect JSON
    if request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
        from django.http import JsonResponse
        return JsonResponse({"ok": True, "consent_learner": recording.consent_learner, "consent_teacher": recording.consent_teacher})
    from django.http import JsonResponse
    return JsonResponse({"ok": True})


@login_required
@require_POST
def upload_audio_view(request, pk):
    session = _own_session(request, pk)
    if not session:
        from django.http import JsonResponse
        return JsonResponse({"ok": False, "error": "not your session"}, status=403)
    if session.status != "accepted" and session.status != "completed":
        from django.http import JsonResponse
        return JsonResponse({"ok": False, "error": "session not in recordable state"}, status=400)
    recording, _ = SessionRecording.objects.get_or_create(session=session)
    # Consent is mandatory — at least the uploader must have consented
    is_learner = request.user.id == session.learner_id
    is_teacher = request.user.id == session.teacher_id
    has_consent = (is_learner and recording.consent_learner) or (is_teacher and recording.consent_teacher)
    if not has_consent:
        from django.http import JsonResponse
        return JsonResponse({"ok": False, "error": "consent required before recording"}, status=400)
    audio = request.FILES.get("audio")
    if not audio:
        from django.http import JsonResponse
        return JsonResponse({"ok": False, "error": "no audio file"}, status=400)
    # Save via storage abstraction (local MEDIA_ROOT now, S3 later)
    recording.audio_file.save(f"{session.pk}_{audio.name}", audio, save=False)
    try:
        duration = request.POST.get("duration_seconds")
        if duration:
            recording.duration_seconds = int(float(duration))
    except Exception:
        pass
    recording.status = "uploaded"
    recording.error = ""
    recording.save()
    # Try to enqueue transcription task (Celery) — fall back to eager if broker not available
    try:
        from .tasks import transcribe_recording
        # Use delay if Celery is configured; if broker unavailable, it will be caught
        # Check for eager mode to run synchronously
        from django.conf import settings as _s
        if getattr(_s, "CELERY_TASK_ALWAYS_EAGER", False):
            transcribe_recording(recording.id)
        else:
            transcribe_recording.delay(recording.id)
    except Exception as exc:
        # Do not fail the upload if Celery is not running — transcript can be done via management command
        import logging
        logging.getLogger(__name__).warning("transcribe enqueue failed for %s: %s", recording.id, exc)
    from django.http import JsonResponse
    return JsonResponse({"ok": True, "status": recording.status, "audio_url": recording.audio_file.url if recording.audio_file else ""})


@login_required
@require_POST
def complete_session_view(request, pk):
    session = _own_session(request, pk)
    if not session:
        messages.error(request, "That session is not yours.")
        return redirect("sessions")
    if session.status != "accepted":
        messages.error(request, "Only accepted sessions can be completed.")
        return redirect("sessions")

    UserProfile.objects.get_or_create(user=session.learner)
    UserProfile.objects.get_or_create(user=session.teacher)

    with transaction.atomic():
        session = Session.objects.select_for_update().get(pk=session.pk)
        if session.status != "accepted":
            messages.error(request, "Only accepted sessions can be completed.")
            return redirect("sessions")
        learner_profile = UserProfile.objects.select_for_update().get(user=session.learner)
        teacher_profile = UserProfile.objects.select_for_update().get(user=session.teacher)
        cost = session.credits
        if learner_profile.credits < cost:
            messages.error(request, "Learner does not have enough credits to complete.")
            return redirect("sessions")
        session.status = "completed"
        session.completed_at = timezone.now()
        session.notes = request.POST.get("notes", "").strip()
        session.save(update_fields=["status", "completed_at", "notes"])
        learner_profile.credits -= cost
        teacher_profile.credits += cost
        learner_profile.save(update_fields=["credits"])
        teacher_profile.save(update_fields=["credits"])
        CreditTransaction.objects.create(user=session.learner, session=session, amount=-cost, kind="spend")
        CreditTransaction.objects.create(user=session.teacher, session=session, amount=cost, kind="earn")

    messages.success(request, "Session completed. Credits transferred.")
    return redirect("sessions")


@login_required
@require_POST
def rate_session_view(request, pk):
    session = _own_session(request, pk)
    if not session:
        messages.error(request, "That session is not yours.")
        return redirect("sessions")
    if session.status != "completed":
        messages.error(request, "You can only rate completed sessions.")
        return redirect("sessions")
    if Rating.objects.filter(session=session, from_user=request.user).exists():
        messages.info(request, "You already rated this session.")
        return redirect("sessions")

    try:
        stars = int(request.POST.get("stars", "0"))
    except ValueError:
        stars = 0
    if stars < 1 or stars > 5:
        messages.error(request, "Pick a rating from 1 to 5.")
        return redirect("sessions")

    Rating.objects.create(
        session=session,
        from_user=request.user,
        to_user=session.counterpart(request.user),
        stars=stars,
        comment=request.POST.get("comment", "").strip(),
    )
    _recompute_rating(session.counterpart(request.user))
    messages.success(request, "Rating saved.")
    return redirect("sessions")


@login_required
@require_POST
def generate_summary_view(request, pk):
    session = _own_session(request, pk)
    if not session:
        messages.error(request, "That session is not yours.")
        return redirect("sessions")
    if session.status != "completed":
        messages.error(request, "Only completed sessions can be summarized.")
        return redirect("sessions")
    # Allow transcript as source (Phase E) — notes-only path still works
    transcript = ""
    try:
        rec = session.recording
        transcript = (getattr(rec, "transcript", "") or "").strip()
    except Exception:
        transcript = ""
    notes = (session.notes or "").strip()
    if not transcript and not notes:
        messages.error(request, "Add notes or a transcript before generating a summary.")
        return redirect("sessions")
    # Lazy import to keep module import safe if key missing
    from .ai import generate_session_summary

    summary = generate_session_summary(session)
    if not summary:
        messages.warning(request, "Summary could not be generated. Check GEMINI_API_KEY or try again.")
        return redirect("sessions")
    session.ai_summary = summary
    session.summary_generated_at = timezone.now()
    session.save(update_fields=["ai_summary", "summary_generated_at"])
    messages.success(request, "Summary generated.")
    return redirect("sessions")


@login_required
def credits_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    ledger = CreditTransaction.objects.filter(user=request.user).select_related("session", "session__skill")
    return render(request, "editor/credits.html", {"profile": profile, "ledger": ledger})
