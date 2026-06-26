"""Shared unique payment amount generation for wallet top-ups."""

import random
import string
from decimal import Decimal

from django.utils import timezone

from .models import HamyonPayment


class UniqueAmountGenerator:
    """Generate unique payment amounts and reference codes."""

    @staticmethod
    def generate_payment_code(length: int = 8) -> str:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        while HamyonPayment.objects.filter(payment_code=code).exists():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        return code

    @staticmethod
    def generate_unique_amount(
        base_amount: Decimal,
        min_variance: int = 1,
        max_variance: int = 99,
    ) -> tuple[Decimal, int]:
        variance = random.randint(min_variance, max_variance)
        unique_amount = base_amount + Decimal(variance)
        return unique_amount, variance

    @classmethod
    def generate_wallet_topup_amount(cls, requested_amount: Decimal, max_attempts: int = 50) -> tuple[Decimal, int, str]:
        """Return (actual_amount, variance, payment_code) with collision avoidance."""
        now = timezone.now()
        for _ in range(max_attempts):
            actual_amount, variance = cls.generate_unique_amount(requested_amount)
            collision = HamyonPayment.objects.filter(
                purpose=HamyonPayment.Purpose.WALLET_TOPUP,
                status=HamyonPayment.Status.PENDING,
                amount=actual_amount,
                expires_at__gt=now,
            ).exists()
            if not collision:
                return actual_amount, variance, cls.generate_payment_code()
        raise ValueError("Noyob to'lov summasini yaratib bo'lmadi. Iltimos, qayta urinib ko'ring.")
