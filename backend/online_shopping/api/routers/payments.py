from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_db, get_optional_user
from online_shopping.api.schemas import DemoPaymentPayload, PaymentOut
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.models.account import Account
from online_shopping.models.order import Order
from online_shopping.models.payment import Payment

router = APIRouter()

# Demo card numbers
DEMO_SUCCESS_CARD = "4242424242424242"
DEMO_FAILURE_CARD = "4000000000000002"


def _validate_card(card_number: str) -> bool:
    """Validate demo card number: only known test cards are accepted."""
    cleaned = card_number.replace(" ", "").replace("-", "")
    if cleaned == DEMO_SUCCESS_CARD:
        return True
    if cleaned == DEMO_FAILURE_CARD:
        return False
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid card number. Use 4242424242424242 (success) or 4000000000000002 (failure).",
    )


@router.post("/process", response_model=PaymentOut)
async def process_payment(
    payload: DemoPaymentPayload,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    x_cart_id: str | None = Header(None, alias="X-Cart-Id"),
) -> PaymentOut:
    """Process a demo payment with card number validation.

    Card numbers:
      - 4242424242424242 -> success (payment completed, order confirmed)
      - 4000000000000002 -> failure (payment failed, order unchanged)

    Supports both authenticated users and guest (anonymous) users.
    """
    # Validate card
    _validate_card(payload.card_number)
    cleaned = payload.card_number.replace(" ", "").replace("-", "")

    if not payload.order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="order_id is required.",
        )

    # Find the order
    order_result = await db.execute(
        select(Order).where(Order.order_number == payload.order_id)
    )
    order = order_result.scalars().first()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    # Authorization check
    if current_user:
        # Authenticated user: order must belong to them
        if order.account_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Order does not belong to you.",
            )
    else:
        # Guest: must provide matching order_access_token OR matching X-Cart-Id
        token = getattr(payload, "access_token", None)
        cart_matches = (
            order.cart_id is not None
            and x_cart_id is not None
            and str(order.cart_id) == x_cart_id
        )
        token_matches = (
            token is not None
            and order.order_access_token is not None
            and order.order_access_token == token
        )
        if not (cart_matches or token_matches):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Guest payment requires a valid access token or matching cart session.",
            )

    # Idempotency: prevent duplicate completed payments
    existing_completed = await db.execute(
        select(Payment).where(
            Payment.order_id == order.id,
            Payment.status == PaymentStatus.COMPLETED.value,
        )
    )
    if existing_completed.scalars().first() and cleaned == DEMO_SUCCESS_CARD:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order has already been paid.",
        )

    # Determine success/failure based on card number
    if cleaned == DEMO_SUCCESS_CARD:
        payment_status = PaymentStatus.COMPLETED
        order_status = OrderStatus.CONFIRMED
    else:
        payment_status = PaymentStatus.FAILED
        order_status = OrderStatus.CREATED  # unchanged

    # Create payment record
    payment = Payment(
        order_id=order.id,
        status=payment_status.value,
        amount=payload.amount if payload.amount > 0 else None,
        currency=payload.currency,
    )
    db.add(payment)

    # Update order status on success
    if payment_status == PaymentStatus.COMPLETED:
        order.status = order_status.value

    await db.commit()
    await db.refresh(payment)

    return PaymentOut(
        status=payment_status,
        amount=float(payment.amount) if payment.amount else None,
        currency=payment.currency,
    )
