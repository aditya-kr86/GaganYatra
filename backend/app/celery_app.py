from celery import Celery
import os
import sys

# Configure Celery broker via environment variable
# Defaults: Redis for production, memory for development
# For Windows dev without Redis, use: export CELERY_BROKER_URL=memory://
CELERY_BROKER = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", CELERY_BROKER)

# Flag to indicate if Celery is available (for graceful fallback)
CELERY_ENABLED = True

try:
    celery_app = Celery("gagan", broker=CELERY_BROKER, backend=CELERY_BACKEND)
except Exception as e:
    # If broker connection fails, create a dummy Celery app
    # Real execution will use asyncio background tasks instead
    print(f"⚠️  Warning: Could not initialize Celery with {CELERY_BROKER}")
    print(f"  Error: {e}")
    print("  Falling back to asyncio background tasks for demand simulation.")
    print("  To use Celery, set CELERY_BROKER_URL environment variable.")
    print()
    
    CELERY_ENABLED = False
    celery_app = Celery("gagan")

# Configure pool based on OS (Windows has multiprocessing issues, use solo pool)
if CELERY_ENABLED:
    if sys.platform.startswith('win'):
        celery_app.conf.update(
            worker_pool='solo',  # single-process pool for Windows
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            task_always_eager=False,  # Run tasks asynchronously
        )
    else:
        celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json'
        )


@celery_app.task(name="gagan.run_demand_simulation")
def run_demand_simulation_task(within_hours: int = 720):
    """Run the demand simulation once using a DB session.

    This task imports DB session and simulator at runtime so Celery worker
    doesn't require importing the entire FastAPI app at module import time.
    """
    try:
        from app.config import SessionLocal
        from app.services.demand_simulator import run_demand_simulation_once

        db = SessionLocal()
        updated = run_demand_simulation_once(db, within_hours=within_hours)
        db.close()
        return {"updated": updated}
    except Exception as e:
        return {"error": str(e)}
