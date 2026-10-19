from services.inventory.repository import InventoryRepository
from services.inventory.service import InventoryService
def get_inventory_service() -> InventoryService:
    return InventoryService(InventoryRepository())
