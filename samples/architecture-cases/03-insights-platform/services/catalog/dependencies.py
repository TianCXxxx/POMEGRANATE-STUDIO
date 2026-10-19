from services.catalog.repository import CatalogRepository
from services.catalog.service import CatalogService
def get_catalog_service() -> CatalogService:
    return CatalogService(CatalogRepository())
