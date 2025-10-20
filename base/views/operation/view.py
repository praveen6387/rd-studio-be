import random
import string

import requests
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from base.models import MediaLibrary
from base.utils.s3_utils import upload_file_to_s3
from base.views.operation.serializers import MediaLibrarySerializer


class MediaView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # get all media
    def get(self, request):
        media_libraries = MediaLibrary.objects.prefetch_related("media_library_items").order_by("-id")
        media_libraries = MediaLibrarySerializer(media_libraries, many=True)
        return Response({"message": "media successfully retrieved", "data": media_libraries.data})

    # save new media
    def post(self, request):
        try:
            # Get form data
            media_type = request.data.get("media_type")
            media_items = request.FILES.getlist("media_items")

            if not media_type:
                return Response({"message": "media_type is required"}, status=400)

            if not media_items:
                return Response({"message": "media_items are required"}, status=400)

            base_url = "https://picsum.photos/2500/2500"

            # Upload files to S3 and prepare media items data
            media_items_data = []
            for file in media_items:
                try:
                    # Upload file to S3
                    # file_url = upload_file_to_s3(file, folder_name="media_library")
                    # file_url = "https://picsum.photos/200"

                    response = requests.get(base_url, allow_redirects=True)

                    # The final image URL after redirection
                    file_url = response.url

                    # Prepare media item data
                    media_item_data = {
                        "media_url": file_url,
                        "media_item_title": file.name,
                        "media_item_description": f"Uploaded file: {file.name}",
                    }
                    media_items_data.append(media_item_data)

                except Exception as e:
                    return Response({"message": f"Failed to upload file {file.name}: {str(e)}"}, status=500)

            media_unique_id = "".join(random.choices(string.ascii_letters + string.digits, k=20))

            # Prepare data for serializer
            serializer_data = {
                "media_type": int(media_type),
                "media_title": request.data.get("media_title", ""),
                "media_description": request.data.get("media_description", ""),
                "media_items": media_items_data,
                "media_unique_id": media_unique_id,
            }

            print("serializer_data", serializer_data)

            # Create media library with items
            serializer = MediaLibrarySerializer(data=serializer_data)
            if serializer.is_valid():
                media_library = serializer.save()
                return Response(
                    {
                        "message": "Media library created successfully",
                        "data": MediaLibrarySerializer(media_library).data,
                    },
                    status=201,
                )
            else:
                return Response({"message": "Media library creation failed", "errors": serializer.errors}, status=400)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)

    # update media
    def put(self, request):
        return Response("put method testing")

    def delete(self, request):
        return Response("delete method testing")


class ExternalMediaIdView(APIView):
    permission_classes = [AllowAny]

    # get all media
    def get(self, request, media_unique_id):
        try:
            if not media_unique_id:
                return Response({"message": "media_unique_id is required"}, status=400)

            media_library = (
                MediaLibrary.objects.filter(media_unique_id=media_unique_id)
                .prefetch_related("media_library_items")
                .first()
            )
            print("media_libraries", media_library)
            media_libraries = MediaLibrarySerializer(media_library)
            return Response({"message": "media successfully retrieved", "data": media_libraries.data})
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)
