from django.contrib import admin
from .models import CreditTransaction, Rating, Session, Skill, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "age", "credits", "college", "average_rating", "avatar")
    search_fields = ("user__username", "user__email", "college")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "category", "skill_type", "proficiency", "rating")
    list_filter = ("category", "skill_type", "proficiency")
    search_fields = ("name", "user__username")


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("skill", "learner", "teacher", "status", "scheduled_at", "credits")
    list_filter = ("status",)
    search_fields = ("learner__username", "teacher__username", "skill__name")


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "amount", "session", "created_at")
    list_filter = ("kind",)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "stars", "session", "created_at")
