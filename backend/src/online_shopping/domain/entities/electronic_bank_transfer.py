from online_shopping.domain.value_objects.payment_values import AccountNumber, BankName, RoutingNumber


class ElectronicBankTransfer:
    # 创建电子银行转账支付方式，保存银行名、路由号和账户号。
    def __init__(self, bank_name: BankName, routing_number: RoutingNumber, account_number: AccountNumber):
        self.__bank_name = bank_name
        self.__routing_number = routing_number
        self.__account_number = account_number

    # 返回银行名称，后续可用于展示或支付网关提交。
    @property
    def bank_name(self) -> BankName:
        return self.__bank_name

    # 返回银行路由号码，后续可用于电子转账处理。
    @property
    def routing_number(self) -> RoutingNumber:
        return self.__routing_number

    # 返回银行账户号码，后续可用于电子转账处理。
    @property
    def account_number(self) -> AccountNumber:
        return self.__account_number
