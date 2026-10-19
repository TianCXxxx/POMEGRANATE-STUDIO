import httpx

class WarehouseClient:
    def execute(self, reference: str, amount: float) -> dict:
        response = httpx.post('http://localhost:8201/warehouse/allocate', json={'reference': reference, 'amount': amount}, timeout=5.0)
        response.raise_for_status()
        return response.json()

class CarrierClient:
    def execute(self, reference: str, amount: float) -> dict:
        response = httpx.post('http://localhost:8202/carrier/book', json={'reference': reference, 'amount': amount}, timeout=5.0)
        response.raise_for_status()
        return response.json()
