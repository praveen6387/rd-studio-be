from django.urls import path

from base.views.operation.view import ExternalMediaIdView, MediaView

# api/base/operation/ ->
urlpatterns = [
    path("media/", MediaView.as_view(), name="media"),
    path("media/external/<str:media_unique_id>/", ExternalMediaIdView.as_view(), name="external-media-id"),
]
