from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_current_user, get_db
from online_shopping.api.schemas import PaymentCreate, PaymentOut
from online_shopping.models.account import Account
from online_shopping.models.order import Order
from online_shopping.models.payment import Payment
from online_shopping.domain.enums.payment_status import PaymentStatus

router = APIRouter()


@router.post("/process", response_model=PaymentOut)
async def process_payment(
    payload: PaymentCreate,
    order_id: str | None = None,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentOut:
    """Process a payment for an order. Requires authentication."""
    payment = Payment(
        status=PaymentStatus.COMPLETED.value,
        amount=payload.amount,
        currency=payload.currency,
    )
    if order_id:
        # Verify order exists and belongs to user
        order_result = await db.execute(
            select(Order).where(
                Order.order_number == order_id,
                Order.account_id == current_user.id,
            )
        )
        order = order_result.scalars().first()
        if order:
            payment.order_id = order.id

    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return PaymentOut(
        status=PaymentStatus.COMPLETED,
        amount=float(payment.amount),
        currency=payment.currency,
    )
