from decimal import Decimal, InvalidOperation


def format_uzs(value):
    """Format a numeric value as UZS with thousand separators."""
    if value is None:
        return "0 UZS"

    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return str(value)

    if amount == amount.to_integral():
        formatted = f"{amount:,.0f}"
    else:
        formatted = f"{amount:,.2f}"

    return f"{formatted} UZS"

def generate_otp():
    import random
    return "".join([str(random.randint(0, 9)) for _ in range(6)])

def send_otp_sms(phone_number, otp):
    """
    Placeholder for SMS Gateway integration (e.g., Eskiz.uz).
    """
    print(f"Sending OTP {otp} to {phone_number}")
    # Integration logic here
    return True
