import os
from celery import Celery

celery = Celery(__name__, include=['celery_int.transcription_task'])
service_name = os.environ.get("SERVICE_NAME", "stt")
broker_url = os.environ.get("CELERY_BROKER", "localhost:6379")
celery.conf.broker_url = "{}/0".format(broker_url)
celery.conf.result_backend = "{}/1".format(broker_url)
celery.conf.update(
    result_expires=3600,
    task_acks_late=True,
    task_track_started = True)

# Queues
celery.conf.update(
    {'task_routes': {
        'transcribe_task' : {'queue': service_name},}
    }
)