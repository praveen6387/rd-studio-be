from django.urls import path

from .views import LoginView, UserView

# api/base/auth/ ->
urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("user/", UserView.as_view(), name="user"),
]
