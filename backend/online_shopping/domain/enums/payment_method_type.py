from enum import Enum


class PaymentMethodType(str, Enum):
    CREDIT_CARD = "credit_card"
    ELECTRONIC_BANK_TRANSFER = "electronic_bank_transfer"

    CreditCard = CREDIT_CARD
    ElectronicBankTransfer = ELECTRONIC_BANK_TRANSFER
