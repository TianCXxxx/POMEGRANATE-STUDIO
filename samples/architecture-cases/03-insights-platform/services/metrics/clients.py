import httpx

class IdentityClient:
    def execute(self, reference: str, amount: float) -> dict:
        response = httpx.post('http://localhost:8301/identity/verify', json={'reference': reference, 'amount': amount}, timeout=5.0)
        response.raise_for_status()
        return response.json()

class CatalogClient:
    def execute(self, reference: str, amount: float) -> dict:
        response = httpx.post('http://localhost:8302/catalog/query', json={'reference': reference, 'amount': amount}, timeout=5.0)
        response.raise_for_status()
        return response.json()

