import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skillbridge_project.settings")

app = Celery("skillbridge_project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(["editor"])
