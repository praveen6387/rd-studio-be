import uuid
from ast import mod
from email.policy import default
from enum import unique

from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (0, "Customer"),
        (1, "Studio"),
        (2, "Lab"),
        (3, "Admin"),
        (4, "Super Admin"),
    )
    GENDER_CHOICE = (
        (0, "Male"),
        (1, "Female"),
        (2, "Other"),
    )

    # Override username to use email
    username = models.CharField(max_length=150, unique=True, default="")
    email = models.EmailField(unique=True)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    phone = models.CharField(max_length=20, unique=True)
    role = models.IntegerField(choices=USER_TYPE_CHOICES, default=0)
    profile_picture = models.CharField(max_length=128, null=True)
    gender = models.IntegerField(choices=GENDER_CHOICE, null=True)
    date_of_birth = models.DateField(null=True)
    organization_name = models.CharField(max_length=100, null=True)

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

    studio_name = models.CharField(max_length=100, null=True, blank=True)
    event_date = models.DateField(null=True, blank=True)

    is_favorite = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="media_libraries_created_by", default=None, null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "media_libraries"
        verbose_name_plural = "Media Libraries"


class MediaLibraryItem(models.Model):

    PAGE_TYPE_CHOICES = (
        (0, "Front"),
        (1, "Middle"),
        (2, "Back"),
    )

    id = models.AutoField(primary_key=True)
    media_library = models.ForeignKey(MediaLibrary, on_delete=models.CASCADE, related_name="media_library_items")

    # File storage - increased length for longer URLs
    media_url = models.URLField(max_length=500)

    # Content
    media_item_title = models.CharField(max_length=200, null=True, blank=True)
    media_item_description = models.TextField(null=True, blank=True)

    page_type = models.IntegerField(choices=PAGE_TYPE_CHOICES, default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "media_library_items"
        ordering = ["id"]


class UserPaymentTransaction(models.Model):
    TRANSACTION_STATUS_CHOICES = (
        (0, "Pending"),
        (1, "Completed"),
        (2, "Failed"),
    )
    TRANSACTION_METHOD_CHOICES = (
        (0, "UPI"),
        (1, "Cash"),
        (2, "Bank Transfer"),
        (3, "Other"),
    )
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_payment_transactions")
    transaction_id = models.CharField(max_length=200, unique=True)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_active_from_date = models.DateField(null=True, blank=True)
    operation_count = models.IntegerField(default=0)
    transaction_status = models.IntegerField(choices=TRANSACTION_STATUS_CHOICES, default=0)
    transaction_method = models.IntegerField(choices=TRANSACTION_METHOD_CHOICES, default=0)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "user_payment_transactions"
        ordering = ["-id"]
