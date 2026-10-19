from celery import Celery
BROKER_URL = 'amqp://guest:guest@rabbitmq:5672/'
worker = Celery('orders', broker=BROKER_URL)
class EventPublisher:
    def publish(self, task: str, payload: dict) -> None:
        worker.send_task(task, args=[payload])
