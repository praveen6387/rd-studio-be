from django.urls import path

from .views import CurrentUserView, LoginView, UserView

# api/base/auth/ ->
urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("user/", UserView.as_view(), name="user"),
    path("current-user/", CurrentUserView.as_view(), name="current-user"),
]
