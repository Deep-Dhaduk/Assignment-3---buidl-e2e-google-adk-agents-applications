def calculate_total(price_cents, quantity):
    if type(price_cents) is not int or price_cents < 0:
        raise ValueError("price_cents must be a non-negative integer")
    if type(quantity) is not int or quantity < 1:
        raise ValueError("quantity must be a positive integer")
    return price_cents * quantity


def average_price(prices):
    return sum(prices) / len(prices) if prices else 0
