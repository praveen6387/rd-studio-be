from django.urls import path

from .views import CreatePaymentTransactionView

# api/base/payment/ ->
urlpatterns = [
    path("create-payment-transaction/", CreatePaymentTransactionView.as_view(), name="create-payment-transaction"),
]
