from django.urls import reverse

from apps.notifications.models import Notification


def _create(user, notif_type, title, message, target_url=""):
    Notification.objects.create(
        user=user,
        notif_type=notif_type,
        title=title,
        message=message,
        target_url=target_url,
    )


def notify_proposal_new(project, proposal):
    url = reverse("freelance:manage_proposals", kwargs={"project_id": project.id})
    _create(
        project.client,
        Notification.Type.FREELANCE_PROPOSAL_NEW,
        "Yangi taklif",
        f"{proposal.freelancer.username} loyihangizga taklif yubordi.",
        url,
    )


def notify_proposal_accepted(proposal):
    url = reverse("freelance:freelancer_dashboard")
    _create(
        proposal.freelancer,
        Notification.Type.FREELANCE_PROPOSAL_ACCEPTED,
        "Taklif qabul qilindi",
        f"'{proposal.project.title}' loyihasi uchun taklifingiz qabul qilindi.",
        url,
    )


def notify_proposal_rejected(proposal):
    _create(
        proposal.freelancer,
        Notification.Type.FREELANCE_PROPOSAL_REJECTED,
        "Taklif rad etildi",
        f"'{proposal.project.title}' loyihasi uchun taklifingiz rad etildi.",
        reverse("freelance:freelancer_dashboard"),
    )


def notify_escrow_pending(tx):
    _create(
        tx.payer,
        Notification.Type.FREELANCE_PAYMENT_PENDING,
        "To'lov kutilmoqda",
        f"To'lovingiz admin tasdiqlanishini kutmoqda ({tx.amount} UZS).",
        reverse("freelance:client_dashboard"),
    )


def notify_escrow_released(tx):
    if tx.payee:
        _create(
            tx.payee,
            Notification.Type.FREELANCE_ESCROW_RELEASED,
            "To'lov o'tkazildi",
            f"{tx.amount} UZS miqdoridagi to'lov hisobingizga o'tkazildi.",
            reverse("freelance:freelancer_dashboard"),
        )


def notify_milestone_due(milestone):
    project = milestone.project
    if project.assigned_freelancer:
        _create(
            project.assigned_freelancer,
            Notification.Type.FREELANCE_MILESTONE_DUE,
            "Milestone muddati yaqinlashmoqda",
            f"'{milestone.title}' uchun muddat yaqinlashmoqda.",
            reverse("freelance:milestone_manage", kwargs={"project_id": project.id}),
        )
