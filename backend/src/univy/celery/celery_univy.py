from celery import Celery
from univy.config import settings

app = Celery('celery_univy', broker=settings.CELERY_BROKER_URL, include=['univy.celery.tasks'])

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()
