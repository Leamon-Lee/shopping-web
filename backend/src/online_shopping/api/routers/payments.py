from fastapi import APIRouter

from online_shopping.api import store
from online_shopping.api.schemas import PaymentCreate, PaymentOut
from online_shopping.domain.enums.payment_status import PaymentStatus

router = APIRouter()


@router.post("/process", response_model=PaymentOut)
def process_payment(payload: PaymentCreate) -> PaymentOut:
    payment = PaymentOut(
        status=PaymentStatus.PENDING,
        amount=payload.amount,
        currency=payload.currency,
    )
    return store.process_payment(payment)
