# Option 1: Using queue parameter
from app.tasks import process_image_with_yolo
process_image_with_yolo.apply_async(args=[image_id], queue='gpu')

# Option 2: Using decorator
@app.task(queue='gpu')
def process_image_with_yolo(image_id):
    # Your GPU task code here
    pass

# Option 3: Configure in settings.py
CELERY_TASK_ROUTES = {
    'app.tasks.process_image_with_yolo': {'queue': 'gpu'},
    'app.tasks.process_image_with_paddleocr': {'queue': 'gpu'},
}