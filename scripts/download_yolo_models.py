#!/usr/bin/env python3
"""
Script to pre-download YOLO models during Docker build.
This ensures models are available in the image and don't need to be downloaded at runtime.
"""
import os
import sys
from pathlib import Path

try:
    from ultralytics import YOLO
    
    # Set cache directory (models are typically cached in ~/.ultralytics)
    # We'll use a directory in /app to ensure it's part of the image
    cache_dir = Path("/app/.ultralytics")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Set environment variable for ultralytics cache
    os.environ['ULTRALYTICS_CACHE_DIR'] = str(cache_dir)
    
    print("=" * 60)
    print("Downloading YOLO models during Docker build...")
    print("=" * 60)
    
    # List of models to download (you can customize this)
    models_to_download = [
        ('yolov8n.pt', 'YOLOv8n (nano) - smallest, fastest'),
        ('yolov8s.pt', 'YOLOv8s (small) - good balance'),
        ('yolov8m.pt', 'YOLOv8m (medium) - better accuracy'),
        # Uncomment if you need larger models:
        # ('yolov8l.pt', 'YOLOv8l (large) - high accuracy'),
        # ('yolov8x.pt', 'YOLOv8x (extra large) - best accuracy'),
    ]
    
    downloaded_models = []
    
    for model_name, description in models_to_download:
        try:
            print(f"\n[{len(downloaded_models) + 1}/{len(models_to_download)}] {description}")
            print(f"Downloading {model_name}...")
            model = YOLO(model_name)
            model_path = getattr(model, 'ckpt_path', model_name)
            print(f"✓ {model_name} downloaded successfully")
            print(f"  Location: {model_path}")
            downloaded_models.append(model_name)
        except Exception as e:
            print(f"✗ Failed to download {model_name}: {e}")
            # Continue with other models even if one fails
            continue
    
    print("\n" + "=" * 60)
    if downloaded_models:
        print(f"✓ Successfully downloaded {len(downloaded_models)} model(s):")
        for model in downloaded_models:
            print(f"  - {model}")
        print(f"\nModels cached in: {cache_dir}")
    else:
        print("✗ No models were downloaded successfully!")
        sys.exit(1)
    print("=" * 60)
    
except ImportError as e:
    print(f"✗ Error: ultralytics package not installed: {e}")
    print("Make sure requirements-celery.txt includes 'ultralytics'")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
