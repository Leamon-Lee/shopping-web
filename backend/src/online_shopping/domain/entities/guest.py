from online_shopping.domain.entities.customer import Customer


class Guest(Customer):
    # 注册新账户，后续应收集账户信息并生成正式会员账户。
    def register_account(self) -> bool:
        pass
