from services.fulfillment.repository import FulfillmentRepository
from services.fulfillment.service import FulfillmentService
from services.fulfillment.clients import WarehouseClient
from services.fulfillment.clients import CarrierClient
from services.fulfillment.events import EventPublisher
def get_fulfillment_service() -> FulfillmentService:
    return FulfillmentService(FulfillmentRepository(), WarehouseClient(), CarrierClient(), EventPublisher())
