from celery import Celery
import os


BROKER = os.environ.get("CELERY_BROKER")
BACKEND = os.environ.get("CELERY_BACKEND")

app = Celery(__name__, broker=BROKER, backend=BACKEND)
