import re


def check_is_valid_price(price) -> bool:
    price = str(price)
    if len(str(price)) == 0:
        return False

    try:
        if float(price) < 0:
            return False
    except ValueError:
        return False
    else:
        # Price can have 0 to 2 decimal places.
        if "." in price:
            decimal_points = len(price.split(".")[1])
            if decimal_points >= 3:
                return False

    return True


def check_is_valid_quantity(quantity) -> bool:
    quantity = str(quantity)
    if len(str(quantity)) == 0:
        return False

    try:
        _ = float(quantity)
    except ValueError:
        return False

    return True


def check_is_valid_email(userId) -> bool:
    userId = str(userId)
    if len(userId) == 0:
        return False

    # Source: https://stackoverflow.com/a/8022584
    if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", userId):
        return False

    return True


def check_is_valid_state_abbr(state: str) -> bool:
    if len(state) != 2:
        return False

    # Source: https://stackoverflow.com/a/65714104
    list_states = [
        "AL",
        "AK",
        "AS",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "DC",
        "FL",
        "GA",
        "GU",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "MP",
        "OH",
        "OK",
        "OR",
        "PA",
        "PR",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VI",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
    ]
    if state not in list_states:
        return False

    return True
