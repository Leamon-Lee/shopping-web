from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.domain.value_objects.order_values import CreationDate
from online_shopping.domain.value_objects.payment_values import (
    PaymentProvider,
    TransactionId,
)


class PaymentTransaction:
    def __init__(
        self,
        status: PaymentStatus,
        transaction_id: TransactionId | None = None,
        provider: PaymentProvider | None = None,
        created_on: CreationDate | None = None,
    ) -> None:
        self.__transaction_id = transaction_id
        self.__provider = provider
        self.__status = status
        self.__created_on = created_on

    @property
    def status(self) -> PaymentStatus:
        return self.__status
