from django.urls import path

from .views import CurrentUserView, LoginView, SocialLink, UserSignupView, UserView

# api/base/auth/ ->
urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("user/", UserView.as_view(), name="user"),
    path("signup/", UserSignupView.as_view(), name="signup"),
    path("current-user/", CurrentUserView.as_view(), name="current-user"),
    path("social-link/update/", SocialLink.as_view(), name="update-social-link"),
]
