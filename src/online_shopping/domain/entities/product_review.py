from online_shopping.domain.entities.product import Product
from online_shopping.domain.value_objects.product_values import Rating, ReviewContent


class ProductReview:
    # 创建商品评价，并关联评分、评价内容和被评价商品。
    def __init__(self, rating: Rating, review: ReviewContent, product: Product):
        self.__rating = rating
        self.__review = review
        self.__product = product

    # 返回评价分数，后续可用于商品评分统计。
    def get_rating(self) -> Rating:
        return self.__rating
