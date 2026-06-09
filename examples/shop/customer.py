from shop import order  # intentional circular import (demo)


def greet() -> str:
    return "Customer"


def latest_order() -> str:
    return order.place_order("widget")
