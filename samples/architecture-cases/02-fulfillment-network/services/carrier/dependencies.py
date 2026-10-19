from services.carrier.repository import CarrierRepository
from services.carrier.service import CarrierService
def get_carrier_service() -> CarrierService:
    return CarrierService(CarrierRepository())
