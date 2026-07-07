from online_shopping.domain.value_objects.product_values import Price


def test_price_accepts_positive_number() -> None:
    assert Price(10).value == 10.0
