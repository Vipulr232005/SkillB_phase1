"""
Rule-based teacher recommendations (PRD 6.6 Phase 3a) — no AI/LLM, pure Python/ORM.
"""

from django.db.models import Q

from .models import Skill, Session

# Tune-able scoring constants (easy to change)
INTEREST_MATCH_SCORE = 10
CATEGORY_MATCH_SCORE = 4
# rating quality is computed dynamically: average_rating * (1 + min(count,20)/20 * 0.5)  -> 0..7.5
PROFICIENCY_SCORE = {
    "Advanced": 1.5,
    "Intermediate": 0.75,
    "Beginner": 0,
}
DUPLICATE_GUARD_PENALTY = -5
# tiny recency tiebreaker multiplier (so newer wins on equal scores)
RECENCY_FACTOR = 1e-10

OPEN_STATUSES = ("requested", "accepted")


def _interest_set_for_user(user):
    interests = set()
    # From UserProfile.learn_skills (comma-separated)
    try:
        profile = getattr(user, "profile", None)
        if profile and getattr(profile, "learn_skills", None):
            for part in profile.learn_skills.split(","):
                p = part.strip()
                if p:
                    interests.add(p.lower())
    except Exception:
        pass
    # From LEARN Skill rows
    try:
        for name in Skill.objects.filter(user=user, skill_type="LEARN").values_list("name", flat=True):
            n = (name or "").strip()
            if n:
                interests.add(n.lower())
    except Exception:
        pass
    # Remove empty
    interests.discard("")
    return interests


def _category_set_for_user(user):
    cats = set()
    try:
        for cat in Skill.objects.filter(user=user, skill_type="LEARN").values_list("category", flat=True):
            if cat:
                cats.add(cat)
    except Exception:
        pass
    return cats


def recommend_teachers(user, limit=6):
    """
    Return list of Skill objects (TEACH) personalized for user, each with `.reason`.
    Candidate pool: public TEACH skills, allow_requests=True, excluding user.
    Dedupe to one card per teacher (highest scoring). Cold-start fallback uses _peer_skills.
    Never crashes on empty data.
    """
    if user is None or getattr(user, "is_anonymous", False):
        return []

    # Build interest / category sets
    interests = _interest_set_for_user(user)
    categories = _category_set_for_user(user)

    # Cold start: no interests AND no LEARN skills/categories
    if not interests and not categories:
        # No signals — reuse existing top-rated ordering
        try:
            from .views import _peer_skills
            skills = _peer_skills(user)[:limit]
            for s in skills:
                s.reason = "Top rated right now"
            return skills
        except Exception:
            return []

    # Candidate pool
    try:
        qs = (
            Skill.objects.filter(
                skill_type="TEACH",
                user__profile__is_public=True,
                user__profile__allow_requests=True,
            )
            .exclude(user=user)
            .select_related("user", "user__profile")
        )
        candidates = list(qs)
    except Exception:
        return []

    if not candidates:
        return []

    # Pre-fetch open sessions for duplicate guard: (teacher_id, skill_id)
    open_pairs = set()
    try:
        for sess in Session.objects.filter(learner=user, status__in=OPEN_STATUSES).values("teacher_id", "skill_id"):
            open_pairs.add((sess["teacher_id"], sess["skill_id"]))
    except Exception:
        open_pairs = set()

    # Ensure profiles exist to avoid N+1 or missing
    # (select_related already, but ensure)
    scored = []
    for skill in candidates:
        # Normalize candidate name
        cand_name_lc = (skill.name or "").lower()

        # Interest match (either direction substring)
        interest_matched = None
        interest_score = 0
        for intr in interests:
            if intr and (intr in cand_name_lc or cand_name_lc in intr):
                interest_score = INTEREST_MATCH_SCORE
                interest_matched = intr
                # Keep the matched interest for reason; break on first match
                break

        # Category match
        category_score = CATEGORY_MATCH_SCORE if (skill.category in categories) else 0

        # Rating quality
        try:
            profile = skill.user.profile
        except Exception:
            profile = None
        avg = float(getattr(profile, "average_rating", 0) or 0)
        cnt = int(getattr(profile, "rating_count", 0) or 0)
        rating_score = avg * (1 + min(cnt, 20) / 20 * 0.5)

        # Proficiency
        prof_score = PROFICIENCY_SCORE.get(skill.proficiency, 0)

        # Duplicate guard
        duplicate = (skill.user_id, skill.id) in open_pairs
        duplicate_score = DUPLICATE_GUARD_PENALTY if duplicate else 0

        # Recency tiebreaker
        try:
            ts = skill.created_at.timestamp() if getattr(skill, "created_at", None) else 0
        except Exception:
            ts = 0
        recency_score = ts * RECENCY_FACTOR

        total = interest_score + category_score + rating_score + prof_score + duplicate_score + recency_score

        # Determine reason from top-contributing signal (priority: interest > category > rating > fallback)
        if interest_score:
            # Use candidate name for reason, but title-case the matched interest for readability if available
            # Spec: "Matches <skill name> you want to learn"
            # We'll show candidate skill name as the match
            reason = f"Matches {skill.name} you want to learn"
        elif category_score:
            reason = f"In {skill.category}, which you're into"
        elif rating_score >= 2:  # threshold to be considered "highly rated"
            reason = "Highly rated by learners"
        else:
            reason = "Suggested for you"

        # Attach reason and score for dedupe/sort
        skill.reason = reason
        # Store tuple for sorting/dedupe
        scored.append((skill, total, interest_score, category_score, rating_score, skill.user_id))

    # Dedupe to one card per teacher: keep highest total (tie break recency already in total)
    best_by_teacher = {}
    for skill, total, *_ in scored:
        tid = skill.user_id
        prev = best_by_teacher.get(tid)
        if prev is None or total > prev[1]:
            best_by_teacher[tid] = (skill, total)

    # Sort remaining by total desc, then rating, then recency
    sorted_skills = sorted(best_by_teacher.values(), key=lambda x: x[1], reverse=True)

    # Cold-start fallback already handled; but if after filtering we have no results, fallback to top-rated
    if not sorted_skills:
        try:
            from .views import _peer_skills
            skills = _peer_skills(user)[:limit]
            for s in skills:
                s.reason = "Top rated right now"
            return skills
        except Exception:
            return []

    result = [skill for skill, _ in sorted_skills[:limit]]
    # Ensure each has reason (already set)
    for s in result:
        if not getattr(s, "reason", None):
            s.reason = "Suggested for you"

    # Safety: ensure is_public/allow_requests already filtered; double-check exclude self/private
    # (already done via query) — just return
    return result
