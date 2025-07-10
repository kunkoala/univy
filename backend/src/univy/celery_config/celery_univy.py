from celery import Celery
from univy.config import settings

app = Celery(
    'univy',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['univy.document_pipeline.tasks']
)

# Worker Configuration
app.conf.update(
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,  # Store results persistently

    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Worker performance settings
    worker_prefetch_multiplier=1,  # Don't prefetch tasks
    task_acks_late=True,  # Acknowledge tasks after completion
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    worker_max_memory_per_child=200000,  # Restart worker after 200MB memory usage

    # Task execution settings
    task_track_started=True,  # Track when tasks start
    task_time_limit=30 * 60,  # 30 minutes hard time limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft time limit

    # Queue settings
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',

    # Redis specific settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# Task routing - route different tasks to different queues
app.conf.task_routes = {
    'univy.document_pipeline.tasks.pipeline_process_pdf': {'queue': 'pdf_processing'},
    'univy.document_pipeline.tasks.scan_for_new_files': {'queue': 'file_scanning'},
    'univy.document_pipeline.tasks.cleanup_all_task_directories': {'queue': 'maintenance'},
}

# Task annotations for specific task configurations
app.conf.task_annotations = {
    'univy.document_pipeline.tasks.pipeline_process_pdf': {
        'rate_limit': '3/m',  # Max 2 PDF parsing tasks per minute
        'time_limit': 1800,   # 30 minutes
        'soft_time_limit': 1500,  # 25 minutes
    },
    'univy.document_pipeline.tasks.scan_for_new_files': {
        'rate_limit': '10/m',  # Max 10 scans per minute
        'time_limit': 300,     # 5 minutes
    },
    'univy.document_pipeline.tasks.cleanup_all_task_directories': {
        'rate_limit': '1/m',   # Max 1 cleanup per minute
        'time_limit': 600,     # 10 minutes
    },
    'univy.rag.tasks.query_lightrag': {
        'rate_limit': '10/m',  # Max 10 queries per minute
        'time_limit': 300,     # 5 minutes
    },
    'univy.rag.tasks.clear_lightrag_cache': {
        'rate_limit': '1/m',   # Max 1 cache clear per minute
        'time_limit': 60,      # 1 minute
    },
}

# Worker pool settings
app.conf.worker_pool = 'prefork'  # Use prefork pool for CPU-intensive tasks
app.conf.worker_concurrency = 2   # Number of worker processes

if __name__ == '__main__':
    app.start()
