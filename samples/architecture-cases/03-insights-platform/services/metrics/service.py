from services.metrics.repository import MetricsRepository
from services.metrics.clients import IdentityClient
from services.metrics.clients import CatalogClient
from services.metrics.events import EventPublisher
from services.metrics.cache import MetricsCache
class MetricsService:
    def __init__(self, repository: MetricsRepository, IdentityClient: IdentityClient, CatalogClient: CatalogClient, publisher: EventPublisher, cache: MetricsCache):
        self.repository = repository
        self.identityClient = IdentityClient
        self.catalogClient = CatalogClient
        self.publisher = publisher
        self.cache = cache
    def execute(self, reference: str, amount: float) -> dict:
        self.identityClient.execute(reference, amount)
        self.catalogClient.execute(reference, amount)
        result = self.repository.save(reference, amount)
        self.cache.store(reference, result)
        self.publisher.publish('reports.on_metrics_requested', result)
        return result
