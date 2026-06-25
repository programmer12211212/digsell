from decimal import Decimal

from django.db import transaction

from apps.freelance.models import PlatformCommission


def get_active_commission_rate() -> Decimal:
    commission = PlatformCommission.objects.filter(is_active=True).first()
    if commission:
        return commission.percentage
    return Decimal("10.00")


def calculate_commission(amount: Decimal) -> tuple[Decimal, Decimal]:
    rate = get_active_commission_rate()
    commission = (amount * rate / Decimal("100")).quantize(Decimal("0.01"))
    net = amount - commission
    return commission, net
