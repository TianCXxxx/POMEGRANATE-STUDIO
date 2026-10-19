from services.identity.repository import IdentityRepository
from services.identity.service import IdentityService
def get_identity_service() -> IdentityService:
    return IdentityService(IdentityRepository())
