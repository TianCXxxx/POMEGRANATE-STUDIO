from celery import Celery
from services.notifications.dependencies import get_notifications_service
app = Celery('notifications', broker='amqp://guest:guest@rabbitmq:5672/')
@app.task(name='notifications.on_order_created')
def handle_event(payload: dict):
    service = get_notifications_service()
    return service.execute(payload['reference'], 0)
