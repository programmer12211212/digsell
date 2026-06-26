import time
import traceback

from django.core.management.base import BaseCommand
from django.db import transaction, DatabaseError, OperationalError

from apps.payments.models import HamyonPayment
from apps.payments.services import HamyonPaymentService


class Command(BaseCommand):
    help = (
        "Poll pending Hamyon payments and process their status.\n"
        "Runs continuously until interrupted. Compatible replacement for Celery-based polling."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=float,
            default=5.0,
            help="Polling interval in seconds (default: 5)",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run a single polling pass and exit",
        )

    def handle(self, *args, **options):
        interval = max(0.5, float(options.get("interval", 5.0)))
        run_once = options.get("once", False)

        service = HamyonPaymentService()

        self.stdout.write(self.style.SUCCESS(
            f"Starting Hamyon payment poller (interval={interval}s, once={run_once})"
        ))

        try:
            while True:
                pending_qs = HamyonPayment.objects.filter(status=HamyonPayment.Status.PENDING)
                count = pending_qs.count()
                if count:
                    self.stdout.write(f"Found {count} pending Hamyon payment(s)")

                for payment in pending_qs.iterator():
                    try:
                        # Try to obtain a DB-level lock for the single payment when supported.
                        try:
                            with transaction.atomic():
                                locked = None
                                try:
                                    locked = HamyonPayment.objects.select_for_update().get(pk=payment.pk)
                                except Exception:
                                    # DB may not support select_for_update (SQLite) or lock failed; fall back
                                    locked = HamyonPayment.objects.get(pk=payment.pk)

                                service.process_payment_status(locked)
                        except (DatabaseError, OperationalError):
                            # Fall back to non-locked processing
                            service.process_payment_status(payment)
                    except Exception:
                        self.stderr.write("Error processing payment id=%s:\n%s" % (getattr(payment, 'pk', 'unknown'), traceback.format_exc()))

                if run_once:
                    break

                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Poller interrupted by user. Exiting."))
