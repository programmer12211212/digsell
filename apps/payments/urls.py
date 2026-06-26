from django.urls import path
from .views import (
    WalletView,
    withdraw_funds,
    add_card,
    create_hamyon_payment,
    hamyon_payment_status,
    cancel_hamyon_payment,
    debug_hamyon_payment,
    test_mark_payment_success,
    wallet_balance_check,
    wallet_auto_topup,
)

app_name = "payments"

urlpatterns = [
    path("wallet/", WalletView.as_view(), name="wallet"),
    path("withdraw/", withdraw_funds, name="withdraw"),
    path("add-card/", add_card, name="add_card"),
    path("hamyon/create/", create_hamyon_payment, name="hamyon_create"),
    path("hamyon/<int:payment_id>/status/", hamyon_payment_status, name="hamyon_status"),
    path("hamyon/<int:payment_id>/cancel/", cancel_hamyon_payment, name="hamyon_cancel"),
    path("hamyon/debug/latest/", debug_hamyon_payment, name="hamyon_debug"),
    path("hamyon/<int:payment_id>/test-success/", test_mark_payment_success, name="hamyon_test_success"),
    path("wallet/check-balance/", wallet_balance_check, name="wallet_balance_check"),
    path("wallet/auto-topup/", wallet_auto_topup, name="wallet_auto_topup"),
]
