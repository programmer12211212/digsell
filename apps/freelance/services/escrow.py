from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.payments.models import EscrowAccount
from apps.freelance.models import FreelanceEscrowTransaction, Milestone
from apps.freelance.services.commission import calculate_commission
from apps.freelance.services.audit import log_audit
from apps.freelance.services.notifications import notify_escrow_pending, notify_escrow_released


class EscrowError(Exception):
    pass


@transaction.atomic
def create_escrow_payment(project, milestone, payer, amount, payment_method, screenshot=None, provider=None):
    payee = project.assigned_freelancer
    commission, _ = calculate_commission(Decimal(str(amount)))
    tx = FreelanceEscrowTransaction.objects.create(
        project=project,
        milestone=milestone,
        payer=payer,
        payee=payee,
        amount=amount,
        commission_amount=commission,
        payment_method=payment_method or "",
        screenshot=screenshot,
        provider=provider or FreelanceEscrowTransaction.Provider.MANUAL_SCREENSHOT,
        status=FreelanceEscrowTransaction.Status.PENDING,
    )
    if milestone:
        milestone.escrow_transaction = tx
        milestone.save(update_fields=["escrow_transaction"])
    notify_escrow_pending(tx)
    return tx


@transaction.atomic
def approve_escrow_payment(tx, admin_user, request=None):
    if tx.status != FreelanceEscrowTransaction.Status.PENDING:
        raise EscrowError("Tranzaksiya kutilmoqda holatda emas.")

    escrow, _ = EscrowAccount.objects.get_or_create(user=tx.payer)
    escrow.frozen_balance += tx.amount
    escrow.save(update_fields=["frozen_balance"])

    tx.status = FreelanceEscrowTransaction.Status.APPROVED
    tx.approved_by = admin_user
    tx.save(update_fields=["status", "approved_by", "updated_at"])

    if request:
        log_audit(
            admin_user, "escrow_approved", "FreelanceEscrowTransaction", tx.id,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
    return tx


@transaction.atomic
def reject_escrow_payment(tx, admin_user, note="", request=None):
    tx.status = FreelanceEscrowTransaction.Status.REJECTED
    tx.admin_note = note
    tx.approved_by = admin_user
    tx.save(update_fields=["status", "admin_note", "approved_by", "updated_at"])
    if request:
        log_audit(
            admin_user, "escrow_rejected", "FreelanceEscrowTransaction", tx.id,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
    return tx


@transaction.atomic
def release_escrow_to_freelancer(milestone, admin_user=None, request=None):
    tx = milestone.escrow_transaction
    if not tx or tx.status != FreelanceEscrowTransaction.Status.APPROVED:
        raise EscrowError("Escrow tasdiqlanmagan.")

    payee = milestone.project.assigned_freelancer
    if not payee:
        raise EscrowError("Freelancer tayinlanmagan.")

    commission, net = calculate_commission(tx.amount)
    payer_escrow, _ = EscrowAccount.objects.get_or_create(user=tx.payer)
    payee_escrow, _ = EscrowAccount.objects.get_or_create(user=payee)

    if payer_escrow.frozen_balance < tx.amount:
        raise EscrowError("Muzlatilgan balans yetarli emas.")

    payer_escrow.frozen_balance -= tx.amount
    payer_escrow.save(update_fields=["frozen_balance"])

    # Credit the freelancer's main Wallet
    from apps.users.models import Wallet
    payee_wallet, _ = Wallet.objects.get_or_create(user=payee)
    payee_wallet.add_funds(
        amount=net,
        reason=f"Loyiha yakunlandi: {milestone.project.title} (Milestone: {milestone.title})"
    )

    payee.total_earned = (payee.total_earned or 0) + net
    payee.save(update_fields=["total_earned"])

    tx.status = FreelanceEscrowTransaction.Status.RELEASED
    tx.commission_amount = commission
    tx.save(update_fields=["status", "commission_amount", "updated_at"])

    milestone.is_paid = True
    milestone.approved_at = timezone.now()
    milestone.save(update_fields=["is_paid", "approved_at"])

    notify_escrow_released(tx)
    if request and admin_user:
        log_audit(
            admin_user, "escrow_released", "FreelanceEscrowTransaction", tx.id,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
    return tx
