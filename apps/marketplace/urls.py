from django.urls import path
from .views import (
    ProductListView, product_detail, submit_review,
    create_order, payment_page, apply_coupon,
    cart_view, add_to_cart, remove_from_cart, update_cart_item,
    save_for_later, checkout_cart, wishlist_view, toggle_wishlist,
)

app_name = "marketplace"

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path("product/<slug:slug>/", product_detail, name="product_detail"),
    path("product/<int:product_id>/review/", submit_review, name="submit_review"),
    path("buy/<int:product_id>/", create_order, name="create_order"),
    path("order/pay/<uuid:order_id>/", payment_page, name="payment_page"),
    path("order/<uuid:order_id>/coupon/", apply_coupon, name="apply_coupon"),
    path("cart/", cart_view, name="cart"),
    path("cart/add/<int:product_id>/", add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:item_id>/", remove_from_cart, name="remove_from_cart"),
    path("cart/update/<int:item_id>/", update_cart_item, name="update_cart_item"),
    path("cart/save/<int:item_id>/", save_for_later, name="save_for_later"),
    path("cart/checkout/", checkout_cart, name="checkout_cart"),
    path("wishlist/", wishlist_view, name="wishlist"),
    path("wishlist/toggle/<int:product_id>/", toggle_wishlist, name="toggle_wishlist"),
]
