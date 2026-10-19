from services.metrics.repository import MetricsRepository
from services.metrics.service import MetricsService
from services.metrics.clients import IdentityClient
from services.metrics.clients import CatalogClient
from services.metrics.events import EventPublisher
from services.metrics.cache import MetricsCache
def get_metrics_service() -> MetricsService:
    return MetricsService(MetricsRepository(), IdentityClient(), CatalogClient(), EventPublisher(), MetricsCache())
