import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

import requests
from django.db.models import Q
from django.core.files.uploadedfile import InMemoryUploadedFile
from base.views.auth.serializers import UserSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from base.models import MediaLibrary
from base.utils.s3_utils import get_s3_client, upload_file_to_s3
from base.views.operation.serializers import MediaLibrarySerializer


class MediaView(APIView):
    authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    # get all media
    def get(self, request, media_id=None):
        try:
            current_user = request.user
            has_single_media = False
            filter_kwargs = Q(is_active=True, created_by=current_user)
            if media_id:
                filter_kwargs &= Q(id=media_id)
                has_single_media = True

            media_libraries = (
                MediaLibrary.objects.filter(filter_kwargs).prefetch_related("media_library_items").order_by("-id")
            )
            if has_single_media:
                media_libraries = media_libraries.first()
            else:
                media_libraries = media_libraries.all()

            media_libraries = MediaLibrarySerializer(media_libraries, many=not has_single_media)
            return Response(
                {
                    "message": "media successfully retrieved", 
                    "user": UserSerializer(current_user).data,
                    "data": media_libraries.data
                }
            )
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)

    # save new media
    def post(self, request):
        try:
            # Get form data
            current_user = request.user
            media_type = request.data.get("media_type")
            media_items = request.FILES.getlist("media_items")
            event_date = request.data.get("event_date")
            created_by = current_user.id
            if current_user.role > 1:
                studio_name = request.data.get("studio_name", current_user.organization_name)
            else:
                studio_name = current_user.organization_name

            if not media_type:
                return Response({"message": "media_type is required"}, status=400)

            if not media_items:
                return Response({"message": "media_items are required"}, status=400)

            media_unique_id = "".join(random.choices(string.ascii_letters + string.digits, k=20))

            # Create S3 client once and reuse for all uploads in this request
            s3_client = get_s3_client()

            # Prepare files in-memory to ensure thread-safe parallel uploads
            prepared_items = []
            for idx, file in enumerate(media_items):
                original_name = file.name
                try:
                    page_type, file_name = original_name.split("_", 1)
                except ValueError:
                    page_type, file_name = "", original_name
                content_type = getattr(file, "content_type", "application/octet-stream")
                file.seek(0)
                data = file.read()
                prepared_items.append(
                    {
                        "index": idx,
                        "original_name": original_name,
                        "page_type": page_type,
                        "file_name": file_name,
                        "content_type": content_type,
                        "data": data,
                    }
                )

            def upload_worker(item):
                buffer = BytesIO(item["data"])
                upload_file = InMemoryUploadedFile(
                    buffer,
                    field_name="file",
                    name=item["original_name"],
                    content_type=item["content_type"],
                    size=len(item["data"]),
                    charset=None,
                )
                file_url = upload_file_to_s3(
                    upload_file,
                    folder_name=f"media_library/{media_unique_id}",
                    s3_client=s3_client,
                )
                return {
                    "index": item["index"],
                    "data": {
                        "media_url": file_url,
                        "media_item_title": item["file_name"],
                        "page_type": item["page_type"],
                        "media_item_description": f"Uploaded file: {item['file_name']}",
                    },
                }

            media_items_data = [None] * len(prepared_items)
            max_workers = min(12, max(1, len(prepared_items)))
            future_to_item = {}
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for item in prepared_items:
                    future = executor.submit(upload_worker, item)
                    future_to_item[future] = item
                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    try:
                        result = future.result()
                        media_items_data[result["index"]] = result["data"]
                    except Exception as e:
                        return Response({"message": f"Failed to upload file {item['file_name']}: {str(e)}"}, status=500)
            # Compact in rare case of missing entries (should not happen)
            media_items_data = [x for x in media_items_data if x is not None]

            # Prepare data for serializer
            serializer_data = {
                "media_type": int(media_type),
                "media_title": request.data.get("media_title", ""),
                "media_description": request.data.get("media_description", ""),
                "media_items": media_items_data,
                "media_unique_id": media_unique_id,
                "studio_name": studio_name,
                "event_date": event_date,
                "created_by": created_by,
            }

            # Create media library with items
            serializer = MediaLibrarySerializer(data=serializer_data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Media library created successfully",
                        "data": serializer.data,
                    },
                    status=201,
                )
            else:
                return Response({"message": "Media library creation failed", "errors": serializer.errors}, status=400)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)

    # update media
    def put(self, request, media_id):
        try:
            media_library = MediaLibrary.objects.get(id=media_id, is_active=True)
            media_items = request.FILES.getlist("media_items")
            media_unique_id = media_library.media_unique_id
            studio_name = request.data.get("studio_name", media_library.studio_name)
            event_date = request.data.get("event_date", media_library.event_date)
            # Create S3 client once and reuse for all uploads in this request
            s3_client = get_s3_client()

            # Upload files to S3 and prepare media items data
            media_items_data = []
            for file in media_items:
                try:
                    # Upload file to S3, reusing the same client
                    file_url = upload_file_to_s3(
                        file,
                        folder_name=f"media_library/{media_unique_id}",
                        s3_client=s3_client,
                    )
                    # Prepare media item data
                    media_item_data = {
                        "media_url": file_url,
                        "media_item_title": file.name,
                        "media_item_description": f"Uploaded file: {file.name}",
                    }
                    media_items_data.append(media_item_data)

                except Exception as e:
                    return Response({"message": f"Failed to upload file {file.name}: {str(e)}"}, status=500)

            # Prepare data for serializer
            serializer_data = {
                "media_type": int(media_library.media_type),
                "media_title": request.data.get("media_title", media_library.media_title),
                "media_description": request.data.get("media_description", media_library.media_description),
                "media_items": media_items_data,
                "media_unique_id": media_unique_id,
                "studio_name": studio_name,
                "event_date": event_date,
            }

            serializer = MediaLibrarySerializer(media_library, data=serializer_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Media library updated successfully",
                        "data": serializer.data,
                    },
                    status=200,
                )
            else:
                return Response({"message": "Media library update failed", "errors": serializer.errors}, status=400)
        except MediaLibrary.DoesNotExist:
            return Response({"message": "Media library not found"}, status=404)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)

    def delete(self, request, media_id):
        try:
            media_library = MediaLibrary.objects.get(id=media_id, is_active=True)
            media_library.is_active = False
            media_library.save()
            return Response({"message": "Media library deleted successfully"}, status=200)
        except MediaLibrary.DoesNotExist:
            return Response({"message": "Media library not found"}, status=404)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)


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
            media_libraries = MediaLibrarySerializer(media_library)
            return Response({"message": "media successfully retrieved", "data": media_libraries.data})
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)
