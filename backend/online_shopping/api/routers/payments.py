from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_db
from online_shopping.api.schemas import PaymentCreate, PaymentOut
from online_shopping.models.order import Order
from online_shopping.models.payment import Payment
from online_shopping.domain.enums.payment_status import PaymentStatus

router = APIRouter()


@router.post("/process", response_model=PaymentOut)
async def process_payment(payload: PaymentCreate, db: AsyncSession = Depends(get_db)) -> PaymentOut:
    payment = Payment(
        status=PaymentStatus.COMPLETED.value,
        amount=payload.amount,
        currency=payload.currency,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return PaymentOut(
        status=PaymentStatus.COMPLETED,
        amount=float(payment.amount),
        currency=payment.currency,
    )
