from django.db import transaction
from django.utils import timezone

from apps.freelance.models import (
    FreelanceProject,
    Proposal,
    Milestone,
    FreelanceContract,
    FreelanceInvoice,
)
from apps.freelance.services.audit import log_audit
from apps.freelance.services.commission import calculate_commission
from apps.freelance.services.contract import generate_contract_html
from apps.freelance.services.notifications import (
    notify_proposal_accepted,
    notify_proposal_new,
    notify_proposal_rejected,
)
from apps.freelance.services.chat import get_or_create_project_conversation


class WorkflowError(Exception):
    pass


@transaction.atomic
def submit_proposal(project, freelancer, cover_letter, bid_amount, delivery_days, request=None):
    if project.client_id == freelancer.id:
        raise WorkflowError("O'z loyihangizga taklif yubora olmaysiz.")
    if project.status != FreelanceProject.Status.OPEN:
        raise WorkflowError("Loyiha ochiq emas.")
    if Proposal.objects.filter(project=project, freelancer=freelancer).exists():
        raise WorkflowError("Siz allaqachon taklif yuborgansiz.")

    proposal = Proposal.objects.create(
        project=project,
        freelancer=freelancer,
        cover_letter=cover_letter,
        bid_amount=bid_amount,
        delivery_days=delivery_days,
    )
    notify_proposal_new(project, proposal)
    if request:
        log_audit(
            freelancer, "proposal_created", "Proposal", proposal.id,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
    return proposal


@transaction.atomic
def accept_proposal(proposal, client, request=None):
    project = proposal.project
    if project.client_id != client.id:
        raise WorkflowError("Faqat loyiha egasi taklifni qabul qila oladi.")
    if proposal.status == Proposal.Status.ACCEPTED:
        raise WorkflowError("Taklif allaqachon qabul qilingan.")

    Proposal.objects.filter(project=project).exclude(pk=proposal.pk).update(
        status=Proposal.Status.REJECTED, is_accepted=False
    )
    proposal.status = Proposal.Status.ACCEPTED
    proposal.is_accepted = True
    proposal.save(update_fields=["status", "is_accepted", "updated_at"])

    project.assigned_freelancer = proposal.freelancer
    project.status = FreelanceProject.Status.IN_PROGRESS
    project.save(update_fields=["assigned_freelancer", "status", "updated_at"])

    if not project.milestones.exists():
        Milestone.objects.create(
            project=project,
            title="Asosiy bosqich",
            amount=proposal.bid_amount,
            order_index=0,
            due_date=project.deadline,
        )

    contract_html = generate_contract_html(project, proposal)
    FreelanceContract.objects.get_or_create(
        project=project,
        defaults={"content_html": contract_html},
    )

    commission, net = calculate_commission(proposal.bid_amount)
    FreelanceInvoice.objects.create(
        invoice_number=f"FL-{project.id}-{timezone.now().strftime('%Y%m%d%H%M')}",
        project=project,
        client=client,
        freelancer=proposal.freelancer,
        amount=proposal.bid_amount,
        commission=commission,
        status=FreelanceInvoice.Status.SENT,
    )

    get_or_create_project_conversation(project)
    notify_proposal_accepted(proposal)
    if request:
        log_audit(
            client, "proposal_accepted", "Proposal", proposal.id,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
    return proposal


@transaction.atomic
def reject_proposal(proposal, client, request=None):
    if proposal.project.client_id != client.id:
        raise WorkflowError("Faqat loyiha egasi rad eta oladi.")
    proposal.status = Proposal.Status.REJECTED
    proposal.is_accepted = False
    proposal.save(update_fields=["status", "is_accepted", "updated_at"])
    notify_proposal_rejected(proposal)
    if request:
        log_audit(
            client, "proposal_rejected", "Proposal", proposal.id,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
    return proposal


@transaction.atomic
def shortlist_proposal(proposal, client, request=None):
    if proposal.project.client_id != client.id:
        raise WorkflowError("Faqat loyiha egasi shortlist qila oladi.")
    proposal.status = Proposal.Status.SHORTLISTED
    proposal.save(update_fields=["status", "updated_at"])
    if request:
        log_audit(
            client, "proposal_shortlisted", "Proposal", proposal.id,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
    return proposal


@transaction.atomic
def cancel_project(project, user, request=None):
    if project.client_id != user.id:
        raise WorkflowError("Faqat loyiha egasi bekor qila oladi.")
    if project.status not in (FreelanceProject.Status.OPEN, FreelanceProject.Status.IN_PROGRESS):
        raise WorkflowError("Loyiha bekor qilinmaydi.")
    project.status = FreelanceProject.Status.CANCELLED
    project.save(update_fields=["status", "updated_at"])
    if request:
        log_audit(
            user, "project_cancelled", "FreelanceProject", project.id,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
    return project


@transaction.atomic
def complete_milestone(milestone, user, request=None):
    project = milestone.project
    if project.assigned_freelancer_id != user.id:
        raise WorkflowError("Faqat freelancer milestone tugatishi mumkin.")
    milestone.is_completed = True
    milestone.save(update_fields=["is_completed"])
    if request:
        log_audit(
            user, "milestone_completed", "Milestone", milestone.id,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
    return milestone


@transaction.atomic
def approve_milestone(milestone, client, request=None):
    project = milestone.project
    if project.client_id != client.id:
        raise WorkflowError("Faqat mijoz milestone tasdiqlashi mumkin.")
    if not milestone.is_completed:
        raise WorkflowError("Milestone hali tugallanmagan.")
    milestone.is_paid = True
    milestone.approved_at = timezone.now()
    milestone.save(update_fields=["is_paid", "approved_at"])

    total = project.milestones.count()
    done = project.milestones.filter(is_paid=True).count()
    project.progress_percent = int((done / total) * 100) if total else 100
    if done == total:
        project.status = FreelanceProject.Status.COMPLETED
    project.save(update_fields=["progress_percent", "status", "updated_at"])
    if request:
        log_audit(
            client, "milestone_approved", "Milestone", milestone.id,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
    return milestone
