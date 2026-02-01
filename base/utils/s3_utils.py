import uuid
from io import BytesIO

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config as BotoCoreConfig
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, UnidentifiedImageError


def get_s3_client():
    """
    Create and return an S3 client.

    Can be reused by callers to avoid reconnecting for every file
    (e.g. create once before a loop and pass into upload helpers).
    """
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=BotoCoreConfig(
            max_pool_connections=50,
            retries={"max_attempts": 5, "mode": "adaptive"},
        ),
    )


def _compress_image(file, max_width=1920, target_size_kb=400, initial_quality=85, min_quality=20):
    """
    Compress an image file in-memory aiming for a maximum size.

    - Resizes to max_width (keeping aspect ratio) if wider than that
    - Converts to JPEG and iteratively reduces quality until <= target_size_kb (or min_quality)
    - Returns the original file if it's not an image or compression fails
    """
    target_bytes = target_size_kb * 1024

    # If the original file is already small enough, skip compression
    original_size = getattr(file, "size", None)
    if original_size is not None and original_size <= target_bytes:
        file.seek(0)
        return file

    try:
        # Ensure we're at the start of the file before reading
        file.seek(0)
        image = Image.open(file)
    except (UnidentifiedImageError, OSError):
        # Not an image – just return original file
        file.seek(0)
        return file

    # Convert to RGB for formats like JPEG that don't support alpha
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    # Resize if width is larger than max_width
    width, height = image.size
    if width > max_width:
        ratio = max_width / float(width)
        new_size = (max_width, int(height * ratio))
        image = image.resize(new_size, Image.LANCZOS)

    # Iteratively save to JPEG, reducing quality until under target size
    quality = initial_quality
    buffer = BytesIO()

    while True:
        buffer.seek(0)
        buffer.truncate(0)

        image.save(buffer, format="JPEG", optimize=True, quality=quality)
        size = buffer.tell()

        # Stop if under target size or we've hit minimum acceptable quality
        if size <= target_bytes or quality <= min_quality:
            break

        # Decrease quality and try again
        quality -= 5

    buffer.seek(0)

    # Build a new file name with .jpg extension
    original_name = getattr(file, "name", "image")
    base_name = original_name.rsplit(".", 1)[0]
    new_name = f"{base_name}.jpg"

    # Wrap back into an InMemoryUploadedFile so the rest of the code can treat it as an uploaded file
    compressed_file = InMemoryUploadedFile(
        buffer,
        field_name=getattr(file, "field_name", "file"),
        name=new_name,
        content_type="image/jpeg",
        size=buffer.getbuffer().nbytes,
        charset=getattr(file, "charset", None),
    )

    return compressed_file


def upload_file_to_s3(file, folder_name="media", s3_client=None):
    """
    Upload a file to S3 and return the URL.

    - If the file is an image, it is compressed in-memory before upload.
    - If `s3_client` is not provided, a new one is created internally.

    Args:
        file: The file object to upload
        folder_name: The folder name in S3 bucket
        s3_client: Optional existing boto3 S3 client to reuse

    Returns:
        str: The URL of the uploaded file
    """
    try:
        # Ensure we have an S3 client (re-use if provided)
        if s3_client is None:
            s3_client = get_s3_client()

        # Optionally compress images before upload
        file = _compress_image(file)

        # Generate unique filename
        file_extension = file.name.split(".")[-1] if "." in file.name else "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        s3_key = f"{folder_name}/{unique_filename}"

        # Configure high-performance transfer (multipart + concurrency)
        transfer_config = TransferConfig(
            multipart_threshold=5 * 1024 * 1024,  # 5MB
            multipart_chunksize=8 * 1024 * 1024,  # 8MB parts
            max_concurrency=10,
            use_threads=True,
        )

        # Upload using client with TransferConfig (multipart + concurrency)
        # Ensure buffer is at start
        try:
            file.seek(0)
        except Exception:
            pass
        s3_client.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": getattr(file, "content_type", "application/octet-stream")},
            Config=transfer_config,
        )

        # Return the URL
        file_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}"
        return file_url

    except ClientError as e:
        print(f"Error uploading file to S3: {e}")
        raise Exception(f"Failed to upload file: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise Exception(f"Failed to upload file: {str(e)}")


def delete_file_from_s3(file_url, s3_client=None):
    """
    Delete a file from S3 using its URL

    Args:
        file_url: The URL of the file to delete
        s3_client: Optional existing boto3 S3 client to reuse

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure we have an S3 client (re-use if provided)
        if s3_client is None:
            s3_client = get_s3_client()

        # Extract key from URL
        if settings.AWS_S3_CUSTOM_DOMAIN in file_url:
            s3_key = file_url.split(f"{settings.AWS_S3_CUSTOM_DOMAIN}/")[-1]
        else:
            return False

        # Delete file
        s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)

        return True

    except ClientError as e:
        print(f"Error deleting file from S3: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
