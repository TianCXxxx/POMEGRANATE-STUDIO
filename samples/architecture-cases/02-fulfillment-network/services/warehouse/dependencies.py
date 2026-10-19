from services.warehouse.repository import WarehouseRepository
from services.warehouse.service import WarehouseService
def get_warehouse_service() -> WarehouseService:
    return WarehouseService(WarehouseRepository())
