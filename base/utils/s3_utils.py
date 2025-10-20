import uuid

import boto3
from botocore.exceptions import ClientError
from django.conf import settings


def upload_file_to_s3(file, folder_name="media"):
    """
    Upload a file to S3 and return the URL

    Args:
        file: The file object to upload
        folder_name: The folder name in S3 bucket

    Returns:
        str: The URL of the uploaded file
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        # Generate unique filename
        file_extension = file.name.split(".")[-1] if "." in file.name else "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        s3_key = f"{folder_name}/{unique_filename}"

        # Upload file
        s3_client.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": file.content_type, "ACL": "public-read"},
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


def delete_file_from_s3(file_url):
    """
    Delete a file from S3 using its URL

    Args:
        file_url: The URL of the file to delete

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

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
