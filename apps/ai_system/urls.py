from django.urls import path
from .views import AIAssistantView, apply_ai_recommendation, ai_chat_view

app_name = "ai_system"

urlpatterns = [
    path("assistant/", AIAssistantView.as_view(), name="assistant"),
    path("apply-recommendation/", apply_ai_recommendation, name="apply_recommendation"),
    path("chat/", ai_chat_view, name="chat"),
]
