"""
Celery app configuration - OPTIONAL dependency.

This module is kept for backwards compatibility but Celery is NOT required.
The application uses asyncio background tasks by default which work without Redis.

To enable Celery (optional):
1. Install Redis
2. Set CELERY_BROKER_URL=redis://localhost:6379/0
3. Run: celery -A app.celery_app worker --loglevel=info
"""
import os

# Celery is disabled by default - using asyncio background tasks instead
CELERY_ENABLED = False
celery_app = None

# Only try to initialize Celery if explicitly requested via env var
if os.environ.get("ENABLE_CELERY", "").lower() == "true":
    try:
        from celery import Celery
        
        CELERY_BROKER = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
        CELERY_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", CELERY_BROKER)
        
        celery_app = Celery("gagan", broker=CELERY_BROKER, backend=CELERY_BACKEND)
        celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
        )
        CELERY_ENABLED = True
        print("✅ Celery enabled with broker:", CELERY_BROKER)
    except Exception as e:
        print(f"⚠️ Celery initialization failed: {e}")
        CELERY_ENABLED = False
        celery_app = None
