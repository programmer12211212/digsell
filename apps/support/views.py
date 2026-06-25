from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import SupportTicket, TicketReply
from apps.notifications.models import Notification
from django.contrib.auth import get_user_model
from django.db.models import Q
User = get_user_model()


@login_required
def ticket_list(request):
    tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'support/ticket_list.html', {'tickets': tickets})


@login_required
def ticket_create(request):
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        priority = int(request.POST.get('priority', 1))
        if subject and message:
            ticket = SupportTicket.objects.create(
                user=request.user, subject=subject, message=message, priority=priority
            )
            # create admin notifications for new ticket
            admins = User.objects.filter(Q(is_staff=True) | Q(role__in=('ADMIN','SUPER_ADMIN')))
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    notif_type=Notification.Type.SUPPORT_NEW,
                    title=f'Yangi support ticket: {subject} [#{ticket.id}]',
                    message=f'Foydalanuvchi {request.user.username} yangi ticket yubordi: {subject}',
                    target_url=f'/support/{ticket.id}/'
                )
            messages.success(request, 'Murojaatingiz qabul qilindi.')
            return redirect('support:ticket_list')
        messages.error(request, 'Mavzu va xabar to\'ldirilishi shart.')
    return render(request, 'support/ticket_create.html')


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    replies = ticket.replies.select_related('author').all()
    # mark related notifications as read for this user
    from apps.notifications.models import Notification
    Notification.objects.filter(user=request.user, is_read=False, target_url=f'/support/{ticket.id}/').update(is_read=True)
    return render(request, 'support/ticket_detail.html', {'ticket': ticket, 'replies': replies})


@login_required
@require_POST
def ticket_reply(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    text = request.POST.get('message', '').strip()
    if text:
        TicketReply.objects.create(ticket=ticket, author=request.user, message=text)
        if ticket.status == SupportTicket.Status.RESOLVED:
            ticket.status = SupportTicket.Status.OPEN
            ticket.save()
        # notify admins about new reply
        admins = User.objects.filter(Q(is_staff=True) | Q(role__in=('ADMIN','SUPER_ADMIN')))
        for admin in admins:
            Notification.objects.create(
                user=admin,
                notif_type=Notification.Type.SUPPORT_NEW,
                title=f'Yangi ticket javobi: {ticket.subject} [#{ticket.id}]',
                message=f'Foydalanuvchi {request.user.username} ticketga javob berdi.',
                target_url=f'/support/{ticket.id}/'
            )
    return redirect('support:ticket_detail', ticket_id=ticket.id)
