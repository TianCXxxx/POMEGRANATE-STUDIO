from services.fulfillment.repository import FulfillmentRepository
from services.fulfillment.clients import WarehouseClient
from services.fulfillment.clients import CarrierClient
from services.fulfillment.events import EventPublisher
class FulfillmentService:
    def __init__(self, repository: FulfillmentRepository, WarehouseClient: WarehouseClient, CarrierClient: CarrierClient, publisher: EventPublisher):
        self.repository = repository
        self.warehouseClient = WarehouseClient
        self.carrierClient = CarrierClient
        self.publisher = publisher
    def execute(self, reference: str, amount: float) -> dict:
        self.warehouseClient.execute(reference, amount)
        self.carrierClient.execute(reference, amount)
        result = self.repository.save(reference, amount)
        self.publisher.publish('tracking.on_dispatched', result)
        return result
