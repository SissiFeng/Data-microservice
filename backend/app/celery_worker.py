from celery import Celery
from app.core.config import settings

# Initialize Celery
celery_app = Celery(
    "tasks", # Default name for tasks module, can be anything
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks']  # Explicitly include the tasks module path
)

# Configure Celery
celery_app.conf.update(
    task_track_started=True,
    # Optional: Set result expiration time (e.g., 1 day)
    # result_expires=86400,
    # Optional: Configure task serializer (default is json)
    # task_serializer='json',
    # result_serializer='json',
    # accept_content=['json'],
)

# Optional: Autodiscover tasks if you have a different structure
# If your tasks are in app.tasks.example_task, and app.tasks is a package
# celery_app.autodiscover_tasks(['app.tasks'])
# The 'include' parameter in Celery constructor is often preferred for clarity.

# Example task (can be moved to app.tasks.py later)
@celery_app.task(name="example_task")
def example_task(x, y):
    return x + y

if __name__ == '__main__':
    # This allows running celery worker directly for development/testing
    # e.g., python -m app.celery_worker worker -l info
    celery_app.start()
