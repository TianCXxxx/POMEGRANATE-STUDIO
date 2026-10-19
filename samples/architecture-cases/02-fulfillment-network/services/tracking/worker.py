from celery import Celery
from services.tracking.dependencies import get_tracking_service
app = Celery('tracking', broker='amqp://guest:guest@rabbitmq:5672/')
@app.task(name='tracking.on_dispatched')
def handle_event(payload: dict):
    service = get_tracking_service()
    return service.execute(payload['reference'], 0)
