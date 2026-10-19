from services.payments.repository import PaymentRepository
from services.payments.service import PaymentService
def get_payments_service() -> PaymentService:
    return PaymentService(PaymentRepository())
