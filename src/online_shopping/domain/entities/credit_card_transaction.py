from online_shopping.domain.entities.credit_card import CreditCard
from online_shopping.domain.entities.payment import Payment
from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.domain.value_objects.payment_values import Amount


class CreditCardTransaction(Payment):
    # 创建信用卡交易，并将交易和所使用的信用卡支付方式关联起来。
    def __init__(
        self,
        credit_card: CreditCard,
        status: PaymentStatus = PaymentStatus.PENDING,
        amount: Amount | float | None = None,
    ):
        super().__init__(status=status, amount=amount)
        self.__credit_card = credit_card
