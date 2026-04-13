import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.medical_followup.settings")

app = Celery("medical_followup")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
