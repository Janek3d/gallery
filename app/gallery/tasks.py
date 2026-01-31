"""
Celery tasks for the gallery app.

- GPU task: process_picture_ai — YOLO (ai_tags) + PaddleOCR (ocr_text). Route to 'gpu'.
- CPU task: extract_picture_exif — EXIF metadata (camera, location, etc.) as tags. Route to 'cpu'.
"""
import io
import logging
from datetime import datetime

from django.core.files.storage import default_storage
from django.utils import timezone

from config.celery import app

logger = logging.getLogger(__name__)

# EXIF tag IDs (Pillow / standard EXIF)
EXIF_MAKE = 271
EXIF_MODEL = 272
EXIF_DATETIME_ORIGINAL = 36867
EXIF_GPS_INFO = 34853


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
        ocr = PaddleOCR(use_textline_orientation=True, lang='en')
        result = ocr.predict(img_np)
        if not result or not result[0]:
            return ""
        lines = []
        for line in result[0]:
            if line and len(line) >= 2 and line[1]:
                lines.append(line[1][0])
        return "\n".join(lines).strip() if lines else ""
    except Exception as e:
        logger.warning("PaddleOCR failed: %s", e, exc_info=True)
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

    ai_tag_names = _run_yolo(image_bytes)
    ocr_text = _run_paddleocr(image_bytes)

    if ai_tag_names is not None:
        picture.set_ai_tags(ai_tag_names)
    if ocr_text is not None:
        picture.ocr_text = ocr_text
        picture.save(update_fields=['ocr_text'])
    logger.info("Picture %s: ai_tags=%s, ocr_text length=%s", picture_id, len(ai_tag_names or []), len(ocr_text or ''))


def _extract_exif_tags_and_metadata(image_bytes):
    """
    Extract EXIF-derived tag names and metadata from image bytes.
    Returns (tag_names_list, exif_data_dict, taken_at_datetime_or_None).
    Uses Pillow; no GPU. Tag names are lowercase for consistency (e.g. make:canon, model:eos r5, gps).
    """
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
    except ImportError:
        logger.debug("PIL not available for EXIF")
        return [], {}, None

    try:
        img = Image.open(io.BytesIO(image_bytes))
        exif = img.getexif() if hasattr(img, 'getexif') else None
        if not exif:
            return [], {}, None
    except Exception as e:
        logger.debug("Could not open image for EXIF: %s", e)
        return [], {}, None

    tag_names = []
    exif_data = {}
    taken_at = None

    # Make (271)
    make = exif.get(EXIF_MAKE)
    if make and isinstance(make, str):
        make_clean = make.strip().lower()
        if make_clean:
            tag_names.append(f"make:{make_clean}")
            exif_data['make'] = make

    # Model (272)
    model = exif.get(EXIF_MODEL)
    if model and isinstance(model, str):
        model_clean = model.strip().lower()
        if model_clean:
            tag_names.append(f"model:{model_clean}")
            exif_data['model'] = model

    # Camera as single tag (e.g. "canon eos r5")
    if make and model and isinstance(make, str) and isinstance(model, str):
        camera = f"{make} {model}".strip().lower()
        if camera and camera not in [t for t in tag_names if t.startswith("make:") or t.startswith("model:")]:
            tag_names.append(f"camera:{camera}")

    # DateTimeOriginal (36867) -> taken_at
    dt_orig = exif.get(EXIF_DATETIME_ORIGINAL)
    if dt_orig and isinstance(dt_orig, str):
        exif_data['datetime_original'] = dt_orig
        try:
            # EXIF format: "2024:01:15 14:30:00"
            taken_at = datetime.strptime(dt_orig, "%Y:%m:%d %H:%M:%S")
            taken_at = timezone.make_aware(taken_at) if timezone.is_naive(taken_at) else taken_at
        except (ValueError, TypeError):
            pass

    # GPS (34853) -> tag "gps" and store presence
    gps = exif.get(EXIF_GPS_INFO)
    if gps is not None:
        tag_names.append("gps")
        exif_data['has_gps'] = True

    return tag_names, exif_data, taken_at


@app.task(bind=True, queue='cpu')
def extract_picture_exif(self, picture_id):
    """
    Extract EXIF metadata from a picture and add as tags (camera, location/gps, etc.).
    Runs on CPU worker. Reads image from default_storage using picture.seaweedfs_file_id.
    """
    from .models import Picture

    try:
        picture = Picture.objects.get(pk=picture_id, deleted_at__isnull=True)
    except Picture.DoesNotExist:
        logger.warning("Picture %s not found or deleted, skipping EXIF extraction", picture_id)
        return

    path = picture.seaweedfs_file_id
    if not path:
        logger.warning("Picture %s has no seaweedfs_file_id, skipping EXIF extraction", picture_id)
        return

    try:
        with default_storage.open(path, 'rb') as f:
            image_bytes = f.read()
    except Exception as e:
        logger.warning("Could not open image for picture %s (EXIF): %s", picture_id, e)
        return

    if not image_bytes:
        return

    tag_names, exif_data, taken_at = _extract_exif_tags_and_metadata(image_bytes)

    if exif_data:
        picture.exif_data = {**(picture.exif_data or {}), **exif_data}
        picture.save(update_fields=['exif_data'])
    if taken_at is not None:
        picture.taken_at = taken_at
        picture.save(update_fields=['taken_at'])
    if tag_names:
        picture.set_exif_tags(tag_names)

    logger.info("Picture %s: exif_tags=%s", picture_id, len(tag_names))
