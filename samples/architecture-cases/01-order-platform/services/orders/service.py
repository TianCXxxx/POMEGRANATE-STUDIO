from services.orders.repository import OrderRepository
from services.orders.clients import InventoryClient
from services.orders.clients import PaymentClient
from services.orders.events import EventPublisher
class OrderService:
    def __init__(self, repository: OrderRepository, InventoryClient: InventoryClient, PaymentClient: PaymentClient, publisher: EventPublisher):
        self.repository = repository
        self.inventoryClient = InventoryClient
        self.paymentClient = PaymentClient
        self.publisher = publisher
    def execute(self, reference: str, amount: float) -> dict:
        self.inventoryClient.execute(reference, amount)
        self.paymentClient.execute(reference, amount)
        result = self.repository.save(reference, amount)
        self.publisher.publish('notifications.on_order_created', result)
        return result
