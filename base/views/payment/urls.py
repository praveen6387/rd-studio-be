from django.urls import path

from .views import PaymentTransactionView

# api/base/payment/ ->
urlpatterns = [
    path("create-payment-transaction/", PaymentTransactionView.as_view(), name="create-payment-transaction"),
    path(
        "update-payment-transaction/<int:payment_id>/",
        PaymentTransactionView.as_view(),
        name="update-payment-transaction",
    ),
]
