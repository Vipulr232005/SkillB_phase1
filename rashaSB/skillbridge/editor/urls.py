from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("add-skill/", views.add_skill_view, name="add_skill"),
    path("profile/", views.profile_view, name="profile"),
]
