from online_shopping.domain.entities.payment import Payment
from online_shopping.domain.enums.payment_status import PaymentStatus


def test_payment_defaults_to_pending() -> None:
    assert Payment(1, 20.0, "CNY").status == PaymentStatus.PENDING
