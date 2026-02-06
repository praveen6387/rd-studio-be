from rest_framework import serializers

from base.models import MediaLibrary, MediaLibraryItem


class MediaLibraryItemSerializer(serializers.ModelSerializer):
    media_library = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = MediaLibraryItem
        fields = [
            "id",
            "media_url",
            "media_item_title",
            "media_item_description",
            "page_type",
            "created_at",
            "is_active",
            "media_library",
        ]


class MediaLibrarySerializer(serializers.ModelSerializer):
    media_items = MediaLibraryItemSerializer(many=True, required=False, write_only=True)
    media_type = serializers.IntegerField(required=True)
    media_library_items = MediaLibraryItemSerializer(many=True, read_only=True)
    media_type_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MediaLibrary
        fields = [
            "id",
            "media_unique_id",
            "media_type",
            "media_type_name",
            "media_title",
            "media_description",
            "is_favorite",
            "created_at",
            "media_items",
            "media_library_items",
            "studio_name",
            "event_date",
            "created_by",
            "instagram_profile_url",
            "whatsapp_number",
        ]
        # read_only_fields = ["media_unique_id"]

    def get_media_type_name(self, obj):
        return obj.get_media_type_display()

    def validate_media_type(self, value):
        valid_types = [0, 1, 2]  # Image, Video, Flipbook
        if value not in valid_types:
            raise serializers.ValidationError("Invalid media type")
        return value

    def create(self, validated_data):
        # Extract media_items from validated_data
        media_items_data = validated_data.pop("media_items", [])

        # Create the MediaLibrary instance
        media_library = MediaLibrary.objects.create(**validated_data)

        # Create MediaLibraryItem instances in bulk
        media_items = [
            MediaLibraryItem(media_library=media_library, **media_item_data) for media_item_data in media_items_data
        ]
        MediaLibraryItem.objects.bulk_create(media_items)

        return media_library

    def update(self, instance, validated_data):
        # Pop media_items if provided. Using None allows us to distinguish between:
        # - not provided (None) → don't touch existing related items
        # - provided as [] → clear existing related items
        media_items_data = validated_data.pop("media_items", None)

        # Update primitive fields on the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # If media_items was provided in the payload, replace existing related items
        if media_items_data:
            MediaLibraryItem.objects.filter(media_library=instance).delete()
            media_items = [
                MediaLibraryItem(media_library=instance, **media_item_data) for media_item_data in media_items_data
            ]
            MediaLibraryItem.objects.bulk_create(media_items)

        return instance
