from django.contrib import admin
from django.urls import include, path

# api/ ->
urlpatterns = [
    path("base/auth/", include("base.views.auth.urls")),
    path("base/operation/", include("base.views.operation.urls")),
]
