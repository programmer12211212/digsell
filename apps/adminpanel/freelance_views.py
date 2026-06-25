from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Avg

from apps.freelance.models import (
    FreelancerProfile,
    FreelanceProject,
    Proposal,
    FreelanceEscrowTransaction,
    FreelanceAuditLog,
    FreelanceDispute,
    PlatformCommission,
)
from apps.freelance.services.escrow import approve_escrow_payment, reject_escrow_payment
from apps.freelance.services.escrow import EscrowError
from apps.freelance.services.audit import log_audit
from .permissions import staff_required
from .utils import log_admin_action


@staff_required
def freelance_dashboard(request):
    stats = {
        "total_projects": FreelanceProject.objects.count(),
        "open_projects": FreelanceProject.objects.filter(status=FreelanceProject.Status.OPEN).count(),
        "in_progress": FreelanceProject.objects.filter(status=FreelanceProject.Status.IN_PROGRESS).count(),
        "total_freelancers": FreelancerProfile.objects.count(),
        "pending_escrow": FreelanceEscrowTransaction.objects.filter(
            status=FreelanceEscrowTransaction.Status.PENDING
        ).count(),
        "gmv": FreelanceEscrowTransaction.objects.filter(
            status=FreelanceEscrowTransaction.Status.RELEASED
        ).aggregate(t=Sum("amount"))["t"] or Decimal("0"),
        "avg_bid": Proposal.objects.aggregate(a=Avg("bid_amount"))["a"] or Decimal("0"),
        "fill_rate": _fill_rate(),
    }
    pending_escrow = FreelanceEscrowTransaction.objects.filter(
        status=FreelanceEscrowTransaction.Status.PENDING
    ).select_related("project", "payer", "milestone")[:20]
    disputes = FreelanceDispute.objects.filter(
        status=FreelanceDispute.Status.OPEN
    ).select_related("project", "opened_by")[:10]
    flagged = Proposal.objects.filter(is_flagged_spam=True).select_related("project", "freelancer")[:10]
    audit_logs = FreelanceAuditLog.objects.select_related("user")[:30]
    commissions = PlatformCommission.objects.all()
    return render(request, "adminpanel/freelance/dashboard.html", {
        "stats": stats,
        "pending_escrow": pending_escrow,
        "disputes": disputes,
        "flagged": flagged,
        "audit_logs": audit_logs,
        "commissions": commissions,
    })


def _fill_rate():
    total = FreelanceProject.objects.exclude(status=FreelanceProject.Status.OPEN).count()
    completed = FreelanceProject.objects.filter(status=FreelanceProject.Status.COMPLETED).count()
    if total == 0:
        return 0
    return round((completed / total) * 100, 1)


@staff_required
def freelancer_list(request):
    profiles = FreelancerProfile.objects.select_related("user").order_by("-created_at")
    return render(request, "adminpanel/freelance/freelancer_list.html", {"profiles": profiles})


@staff_required
@require_POST
def verify_freelancer(request, profile_id):
    profile = get_object_or_404(FreelancerProfile, id=profile_id)
    from django.utils import timezone
    profile.verified_at = timezone.now()
    profile.user.is_verified = True
    profile.user.save(update_fields=["is_verified"])
    profile.save(update_fields=["verified_at"])
    log_admin_action(request.user, "verify_freelancer", "FreelancerProfile", profile_id)
    messages.success(request, f"{profile.user.username} tasdiqlandi.")
    return redirect("adminpanel:freelance_freelancers")


@staff_required
@require_POST
def approve_escrow(request, tx_id):
    tx = get_object_or_404(FreelanceEscrowTransaction, id=tx_id)
    try:
        approve_escrow_payment(tx, request.user, request)
        log_admin_action(request.user, "approve_escrow", "FreelanceEscrowTransaction", tx_id)
        messages.success(request, "Escrow to'lov tasdiqlandi.")
    except EscrowError as e:
        messages.error(request, str(e))
    return redirect("adminpanel:freelance_dashboard")


@staff_required
@require_POST
def reject_escrow(request, tx_id):
    tx = get_object_or_404(FreelanceEscrowTransaction, id=tx_id)
    note = request.POST.get("note", "")
    reject_escrow_payment(tx, request.user, note, request)
    log_admin_action(request.user, "reject_escrow", "FreelanceEscrowTransaction", tx_id)
    messages.warning(request, "Escrow to'lov rad etildi.")
    return redirect("adminpanel:freelance_dashboard")


@staff_required
@require_POST
def resolve_dispute(request, dispute_id):
    dispute = get_object_or_404(FreelanceDispute, id=dispute_id)
    resolution = request.POST.get("resolution", "")
    from django.utils import timezone
    dispute.status = FreelanceDispute.Status.RESOLVED
    dispute.resolution = resolution
    dispute.resolved_by = request.user
    dispute.resolved_at = timezone.now()
    dispute.save()
    dispute.project.status = FreelanceProject.Status.IN_PROGRESS
    dispute.project.save(update_fields=["status"])
    messages.success(request, "Nizo hal qilindi.")
    return redirect("adminpanel:freelance_dashboard")


@staff_required
@require_POST
def save_commission(request):
    pct = request.POST.get("percentage", "10")
    PlatformCommission.objects.filter(is_active=True).update(is_active=False)
    PlatformCommission.objects.create(name="Default", percentage=Decimal(pct), is_active=True)
    messages.success(request, "Komissiya yangilandi.")
    return redirect("adminpanel:freelance_dashboard")
