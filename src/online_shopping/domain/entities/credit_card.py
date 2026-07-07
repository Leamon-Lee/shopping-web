from online_shopping.domain.value_objects.address import BillingAddress
from online_shopping.domain.value_objects.customer_values import Name
from online_shopping.domain.value_objects.payment_values import CardNumber, Code


class CreditCard:
    # 创建信用卡支付方式，保存持卡人、卡号、安全码和账单地址。
    def __init__(self, name_on_card: Name, card_number: CardNumber, code: Code, billing_address: BillingAddress):
        self.__name_on_card = name_on_card
        self.__card_number = card_number
        self.__code = code
        self.__billing_address = billing_address

