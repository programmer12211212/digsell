from django.urls import path
from .views import login_view, register_view, logout_view, toggle_follow
from .views import seller_apply

app_name = "users"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path("follow/<int:user_id>/", toggle_follow, name="toggle_follow"),
    path("seller/apply/", seller_apply, name="seller_apply"),
]
