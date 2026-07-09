from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ShopId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Shop ID cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class ShopName:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Shop name cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class CartId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Cart ID cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class CartItemId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Cart item ID cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class RegionId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Region ID cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class CustomerEmail:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("Customer email must be a string.")
        value = self.value.strip().lower()
        if not re.fullmatch(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            raise ValueError("Customer email has invalid format.")
        object.__setattr__(self, "value", value)


@dataclass(frozen=True)
class LocaleCode:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Locale code cannot be empty.")
        object.__setattr__(self, "value", self.value.strip().lower())
