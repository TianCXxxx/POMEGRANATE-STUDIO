from celery import Celery
from services.reports.dependencies import get_reports_service
app = Celery('reports', broker='amqp://guest:guest@rabbitmq:5672/')
@app.task(name='reports.on_metrics_requested')
def handle_event(payload: dict):
    service = get_reports_service()
    return service.execute(payload['reference'], 0)
