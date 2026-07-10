"""Payment service — orchestrates payment processing."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.models.payment import Payment


class PaymentService:
    """Orchestrates payment operations. Ready for real gateway integration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_payment(
        self,
        amount: float,
        currency: str = "CNY",
        order_id: str | None = None,
    ) -> Payment:
        """
        Process a payment for an order.

        TODO: Integrate with Stripe / Alipay / WeChat Pay gateway.
        Currently creates a completed payment record for demo purposes.
        """
        payment = Payment(
            status=PaymentStatus.COMPLETED.value,
            amount=amount,
            currency=currency,
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return payment
