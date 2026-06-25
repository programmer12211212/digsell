from django.urls import path
from .views import (
    DashboardView, PurchasesListView, HomeView,
    order_tracking, download_purchase, download_digital_product, wallet_history,
    profile_view, referrals_view,
)

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("profile/", profile_view, name="profile"),
    path("referrals/", referrals_view, name="referrals"),
    path("wallet/history/", wallet_history, name="wallet_history"),
    path("purchases/", PurchasesListView.as_view(), name="purchases"),
    path("purchases/track/<uuid:order_id>/", order_tracking, name="order_tracking"),
    path("purchases/download/<uuid:order_id>/", download_purchase, name="download_purchase"),
    path("downloads/<int:product_id>/", download_digital_product, name="download_digital"),
]
