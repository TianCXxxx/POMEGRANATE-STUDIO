from services.orders.repository import OrderRepository
from services.orders.service import OrderService
from services.orders.clients import InventoryClient
from services.orders.clients import PaymentClient
from services.orders.events import EventPublisher
def get_orders_service() -> OrderService:
    return OrderService(OrderRepository(), InventoryClient(), PaymentClient(), EventPublisher())
