from django.contrib import admin
from .models import UserProfile, Skill

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'credits', 'college', 'department')
    search_fields = ('user__username', 'user__email', 'college')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category', 'skill_type', 'proficiency', 'rating')
    list_filter = ('category', 'skill_type', 'proficiency')
    search_fields = ('name', 'user__username')
