from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.domain.value_objects.payment_values import Amount


class Payment:
    # 创建支付实体，保存支付状态和金额，并兼容旧的测试调用方式。
    def __init__(
        self,
        status: PaymentStatus | int = PaymentStatus.PENDING,
        amount: Amount | float | None = None,
        currency: str | None = None,
    ):
        if not isinstance(status, PaymentStatus):
            status = PaymentStatus.PENDING
        self.__status = status
        self.__amount = amount
        self.__currency = currency

    # 返回支付金额，后续可用于支付网关提交和订单金额核对。
    @property
    def amount(self) -> Amount | float | None:
        return self.__amount

    # 返回支付状态，后续可用于订单状态流转。
    @property
    def status(self) -> PaymentStatus:
        return self.__status

    # 执行支付处理，后续应调用具体支付渠道并返回最终支付状态。
    def process_payment(self) -> PaymentStatus:
        pass
