from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("add-skill/", views.add_skill_view, name="add_skill"),
    path("profile/", views.profile_view, name="profile"),
    path("discover/", views.discover_view, name="discover"),
    path("u/<str:username>/", views.public_profile_view, name="public_profile"),
    path("sessions/", views.sessions_view, name="sessions"),
    path("sessions/request/", views.request_session_view, name="request_session"),
    path("sessions/<int:pk>/accept/", views.accept_session_view, name="accept_session"),
    path("sessions/<int:pk>/reject/", views.reject_session_view, name="reject_session"),
    path("sessions/<int:pk>/cancel/", views.cancel_session_view, name="cancel_session"),
    path("sessions/<int:pk>/join/", views.join_session_view, name="join_session"),
    path("sessions/<int:pk>/complete/", views.complete_session_view, name="complete_session"),
    path("sessions/<int:pk>/rate/", views.rate_session_view, name="rate_session"),
    path("credits/", views.credits_view, name="credits"),
]
