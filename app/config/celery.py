"""
Celery configuration for the gallery project.

This project uses two separate Celery workers:
1. CPU worker (celery) - handles CPU-bound tasks, listens to 'cpu' queue
2. GPU worker (celery-gpu) - handles GPU-intensive tasks (YOLO, PaddleOCR), listens to 'gpu' queue

To route tasks to specific queues:

Option 1: Using task routing in settings.py
    CELERY_TASK_ROUTES = {
        'app.tasks.gpu_task': {'queue': 'gpu'},
        'app.tasks.cpu_task': {'queue': 'cpu'},
    }

Option 2: Using queue parameter when calling tasks
    from app.tasks import process_image_with_yolo
    process_image_with_yolo.apply_async(args=[image_id], queue='gpu')

Option 3: Using @app.task decorator
    @app.task(queue='gpu')
    def process_image_with_yolo(image_id):
        # GPU task code
        pass
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('gallery')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
