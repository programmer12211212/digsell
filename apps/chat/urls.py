from django.urls import path
from .views import chat_list, chat_detail, send_message, get_messages, poll_messages_html, start_chat

app_name = "chat"

urlpatterns = [
    path("", chat_list, name="chat_list"),
    path("<int:conversation_id>/", chat_detail, name="chat_detail"),
    path("<int:conversation_id>/send/", send_message, name="send_message"),
    path("<int:conversation_id>/get-messages/", get_messages, name="get_messages"),
    path("<int:conversation_id>/poll/", poll_messages_html, name="poll_messages"),
    path("start/<int:user_id>/", start_chat, name="start_chat"),
]
