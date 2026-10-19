import httpx

class InventoryClient:
    def execute(self, reference: str, amount: float) -> dict:
        response = httpx.post('http://localhost:8101/inventory/reserve', json={'reference': reference, 'amount': amount}, timeout=5.0)
        response.raise_for_status()
        return response.json()

class PaymentClient:
    def execute(self, reference: str, amount: float) -> dict:
        response = httpx.post('http://localhost:8102/payments/charge', json={'reference': reference, 'amount': amount}, timeout=5.0)
        response.raise_for_status()
        return response.json()
