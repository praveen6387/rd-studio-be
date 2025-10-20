import uuid
from ast import mod
from email.policy import default
from enum import unique

from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (0, "customer"),
        (1, "admin"),
        (3, "super admin"),
        (2, "operation"),
    )
    gender_choices = (
        (0, "male"),
        (1, "female"),
        (2, "other"),
    )

    # Override username to use email
    username = models.CharField(max_length=150, unique=True, default="")
    email = models.EmailField(unique=True)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    phone = models.CharField(max_length=20, unique=True)
    role = models.IntegerField(choices=USER_TYPE_CHOICES, default=0)
    profile_picture = models.CharField(max_length=128, null=True)
    gender = models.CharField(max_length=50, choices=gender_choices, null=True)
    date_of_birth = models.DateField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def save(self, *args, **kwargs):
        # Set is_staff based on role
        self.is_staff = self.role in [1, 3]  # admin or super admin
        super().save(*args, **kwargs)

    class Meta:
        db_table = "users"


class UserAddress(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    first_address = models.CharField(max_length=128, null=True)
    second_address = models.CharField(max_length=128, null=True)
    city = models.CharField(max_length=50, null=True)
    state = models.CharField(max_length=50, null=True)
    zip_code = models.CharField(max_length=10, null=True)
    country = models.CharField(max_length=50, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["user", "is_primary"]
        db_table = "user_addresses"


class UserEvents(models.Model):
    USER_EVENT_STATUS_CHOICES = (
        (0, "pending"),
        (1, "approved"),
        (2, "rejected"),
    )

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_functionalities")

    title = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)

    function_start_date = models.DateField(null=True, blank=True)
    function_end_date = models.DateField(null=True, blank=True)

    status = models.IntegerField(choices=USER_EVENT_STATUS_CHOICES, default=0)

    city = models.CharField(max_length=20, null=True, blank=True)
    state = models.CharField(max_length=20, null=True, blank=True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    country = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "user_events"
        verbose_name_plural = "User Functionalities"


class MediaLibrary(models.Model):
    MEDIA_TYPE_CHOICES = (
        (0, "Image"),
        (1, "Video"),
        (2, "Flipbook"),
    )

    id = models.AutoField(primary_key=True)
    media_unique_id = models.CharField(max_length=200, unique=True)
    user_functionality = models.ForeignKey(
        UserEvents, on_delete=models.CASCADE, related_name="media_libraries", default=None, null=True
    )
    media_type = models.IntegerField(choices=MEDIA_TYPE_CHOICES)

    media_title = models.CharField(max_length=200, null=True, blank=True)
    media_description = models.TextField(null=True, blank=True)

    is_favorite = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "media_libraries"
        verbose_name_plural = "Media Libraries"


class MediaLibraryItem(models.Model):

    id = models.AutoField(primary_key=True)
    media_library = models.ForeignKey(MediaLibrary, on_delete=models.CASCADE, related_name="media_library_items")

    # File storage - increased length for longer URLs
    media_url = models.URLField(max_length=500)

    # Content
    media_item_title = models.CharField(max_length=200, null=True, blank=True)
    media_item_description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "media_library_items"
        ordering = ["-id"]
