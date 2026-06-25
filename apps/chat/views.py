from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.users.models import User
from .models import Conversation, Message


def _get_user_conversations(user):
    return Conversation.objects.filter(participants=user).prefetch_related(
        'participants', 'messages'
    ).order_by('-updated_at')


def _attach_recipients(conversations, user):
    for conv in conversations:
        conv.recipient = conv.get_recipient(user)
    return conversations


@login_required
def chat_list(request):
    conversations = _attach_recipients(list(_get_user_conversations(request.user)), request.user)
    return render(request, 'chat/chat_list.html', {'conversations': conversations})


@login_required
def chat_detail(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related('participants'),
        id=conversation_id,
        participants=request.user,
    )
    messages_qs = conversation.messages.select_related('sender').order_by('created_at')
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    recipient = conversation.get_recipient(request.user)
    conversations = _attach_recipients(list(_get_user_conversations(request.user)), request.user)
    return render(request, 'chat/chat_detail.html', {
        'conversation': conversation,
        'messages': messages_qs,
        'recipient': recipient,
        'conversations': conversations,
    })


@login_required
@require_POST
def send_message(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    text = request.POST.get('text', '').strip()
    if text:
        Message.objects.create(conversation=conversation, sender=request.user, text=text)
        conversation.save()
    if request.headers.get('HX-Request'):
        messages_qs = conversation.messages.select_related('sender').order_by('created_at')
        return render(request, 'chat/partials/message_list.html', {
            'messages': messages_qs,
            'conversation': conversation,
        })
    return redirect('chat:chat_detail', conversation_id=conversation_id)


@login_required
def get_messages(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    messages_qs = conversation.messages.select_related('sender').order_by('created_at')
    data = [{
        'id': m.id,
        'text': m.text,
        'sender': m.sender.username,
        'is_mine': m.sender == request.user,
        'created_at': m.created_at.strftime('%H:%M'),
    } for m in messages_qs]
    return JsonResponse({'messages': data})


@login_required
def poll_messages_html(request, conversation_id):
    """HTMX polling uchun HTML fragment."""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    messages_qs = conversation.messages.select_related('sender').order_by('created_at')
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    return render(request, 'chat/partials/message_list.html', {
        'messages': messages_qs,
        'conversation': conversation,
    })


@login_required
def start_chat(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return redirect('chat:chat_list')

    conversation = Conversation.objects.filter(participants=request.user).filter(
        participants=target_user
    ).first()

    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, target_user)

    return redirect('chat:chat_detail', conversation_id=conversation.id)
