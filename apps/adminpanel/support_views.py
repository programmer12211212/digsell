from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST

from apps.support.models import SupportTicket, TicketReply
from apps.notifications.models import Notification
from .permissions import staff_required


@staff_required
def ticket_list_admin(request):
    status = request.GET.get('status', '')
    tickets = SupportTicket.objects.select_related('user').order_by('-created_at')
    if status:
        tickets = tickets.filter(status=status)
    return render(request, 'adminpanel/support/ticket_list.html', {
        'tickets': tickets,
        'status_filter': status,
    })


@staff_required
def ticket_detail_admin(request, ticket_id):
    ticket = get_object_or_404(SupportTicket.objects.select_related('user'), id=ticket_id)
    replies = ticket.replies.select_related('author').all()
    # mark related notifications as read for this admin
    Notification.objects.filter(user=request.user, is_read=False, target_url=f'/support/{ticket.id}/').update(is_read=True)
    return render(request, 'adminpanel/support/ticket_detail.html', {
        'ticket': ticket,
        'replies': replies,
    })


@require_POST
@staff_required
def ticket_reply_admin(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    text = request.POST.get('message', '').strip()
    new_status = request.POST.get('status')
    if text:
        TicketReply.objects.create(
            ticket=ticket, author=request.user, message=text, is_staff_reply=True
        )
        # notify ticket owner about admin reply
        Notification.objects.create(
            user=ticket.user,
            notif_type=Notification.Type.SUPPORT_REPLY,
            title=f'Admin javobi: {ticket.subject} [#{ticket.id}]',
            message=f'Admin {request.user.username} sizning ticketingizga javob berdi.',
            target_url=f'/support/{ticket.id}/'
        )
    if new_status:
        ticket.status = new_status
        ticket.save()
        # notify ticket owner about status change
        Notification.objects.create(
            user=ticket.user,
            notif_type=Notification.Type.SUPPORT_REPLY,
            title=f'Ticket statusi yangilandi: {ticket.subject} [#{ticket.id}]',
            message=f'Sizning ticketingiz holati: {ticket.get_status_display()}',
            target_url=f'/support/{ticket.id}/'
        )
    messages.success(request, 'Javob yuborildi.')
    return redirect('adminpanel:ticket_detail', ticket_id=ticket.id)