from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from online_shopping.domain.entities.account import Account


class Guest:
    def register_account(self, account: Account) -> Account:
        return account
