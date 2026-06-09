from shop import customer  # intentional circular import (demo)


def place_order(item: str) -> str:
    return customer.greet() + f" ordered {item}"
