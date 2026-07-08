from online_shopping.domain.entities.electronic_bank_transfer import ElectronicBankTransfer
from online_shopping.domain.entities.payment import Payment
from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.domain.value_objects.payment_values import Amount


class ElectronicBankTransaction(Payment):
    # 创建电子银行转账交易，并将交易和转账账户信息关联起来。
    def __init__(
        self,
        electronic_bank_transfer: ElectronicBankTransfer,
        status: PaymentStatus = PaymentStatus.PENDING,
        amount: Amount | float | None = None,
    ):
        super().__init__(status=status, amount=amount)
        self.__electronic_bank_transfer = electronic_bank_transfer
