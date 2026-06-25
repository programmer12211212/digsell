from django.urls import path
from .views import mark_read, mark_all_read, notification_list

app_name = "notifications"

urlpatterns = [
    path("", notification_list, name="list"),
    path("mark-read/<int:notif_id>/", mark_read, name="mark_read"),
    path("mark-all-read/", mark_all_read, name="mark_all_read"),
]
