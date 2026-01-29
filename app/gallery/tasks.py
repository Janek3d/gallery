"""
Celery tasks for the gallery app.

GPU task: process_picture_ai — runs YOLO (object detection → ai_tags) and
PaddleOCR (text extraction → ocr_text) on a picture. Route to 'gpu' queue.
"""
import io
import logging
from django.core.files.storage import default_storage

from config.celery import app

logger = logging.getLogger(__name__)


def _run_yolo(image_bytes):
    """Run YOLO object detection on image bytes. Returns list of detected class names (ai_tags)."""
    try:
        from ultralytics import YOLO
        import numpy as np
        from PIL import Image
    except ImportError:
        logger.debug("ultralytics not available, skipping YOLO")
        return []
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img_np = np.array(img)
        model = YOLO('yolov8n.pt')
        results = model.predict(source=img_np, verbose=False)
        tags = []
        for r in results:
            if r.boxes is not None and r.names:
                for cls_id in r.boxes.cls.int().tolist():
                    name = r.names.get(int(cls_id))
                    if name and name not in tags:
                        tags.append(name)
        return tags
    except Exception as e:
        logger.warning("YOLO inference failed: %s", e)
        return []


def _run_paddleocr(image_bytes):
    """Run PaddleOCR on image bytes. Returns extracted text string (ocr_text)."""
    try:
        from paddleocr import PaddleOCR
        import numpy as np
        from PIL import Image
    except ImportError as e:
        logger.debug("paddleocr/PIL not available, skipping OCR: %s", e)
        return ""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img_np = np.array(img)
        ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        result = ocr.ocr(img_np, cls=True)
        if not result or not result[0]:
            return ""
        lines = []
        for line in result[0]:
            if line and len(line) >= 2 and line[1]:
                lines.append(line[1][0])
        return "\n".join(lines).strip() if lines else ""
    except Exception as e:
        logger.warning("PaddleOCR failed: %s", e)
        return ""


@app.task(bind=True, queue='gpu')
def process_picture_ai(self, picture_id):
    """
    Extract objects (YOLO → ai_tags) and text (PaddleOCR → ocr_text) for a picture.
    Expects to run on GPU worker. Picture image is read from default_storage using
    picture.seaweedfs_file_id.
    """
    from .models import Picture

    try:
        picture = Picture.objects.get(pk=picture_id, deleted_at__isnull=True)
    except Picture.DoesNotExist:
        logger.warning("Picture %s not found or deleted, skipping AI processing", picture_id)
        return

    path = picture.seaweedfs_file_id
    if not path:
        logger.warning("Picture %s has no seaweedfs_file_id, skipping AI processing", picture_id)
        return

    try:
        with default_storage.open(path, 'rb') as f:
            image_bytes = f.read()
    except Exception as e:
        logger.warning("Could not open image for picture %s: %s", picture_id, e)
        return

    if not image_bytes:
        return

    ai_tags = _run_yolo(image_bytes)
    ocr_text = _run_paddleocr(image_bytes)

    update_fields = []
    if ai_tags is not None:
        picture.ai_tags = ai_tags
        update_fields.append('ai_tags')
    if ocr_text is not None:
        picture.ocr_text = ocr_text
        update_fields.append('ocr_text')

    if update_fields:
        picture.save(update_fields=update_fields)
        logger.info("Picture %s: ai_tags=%s, ocr_text length=%s", picture_id, len(ai_tags), len(ocr_text or ''))
