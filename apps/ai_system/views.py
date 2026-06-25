from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .services import ai_chat_assistant


class AIAssistantView(LoginRequiredMixin, TemplateView):
    template_name = "ai_system/assistant.html"


@login_required
@require_POST
def ai_chat_view(request):
    message = request.POST.get('message', '').strip()
    if not message:
        return render(request, 'ai_system/partials/chat_exchange.html', {
            'user_message': '',
            'ai_reply': 'Iltimos, xabar yozing.',
        })
    reply = ai_chat_assistant(message) or (
        "AI xizmati hozircha mavjud emas. GROQ_API_KEY sozlang yoki keyinroq urinib ko'ring."
    )
    if request.headers.get('HX-Request'):
        return render(request, 'ai_system/partials/chat_exchange.html', {
            'user_message': message,
            'ai_reply': reply,
        })
    return JsonResponse({'reply': reply})


@login_required
@require_POST
def apply_ai_recommendation(request):
    product_id = request.POST.get('product_id')
    return JsonResponse({'status': 'ok', 'product_id': product_id})
