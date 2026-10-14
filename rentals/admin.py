
from django.contrib import admin
from django.utils.html import format_html

from .models import Location, Property, PropertyImage


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "has_coordinates", "has_embedding", "updated_at")
    search_fields = ("name",)
    list_filter = ("created_at",)

    @admin.display(boolean=True, description="Coordinates")
    def has_coordinates(self, obj):
        return obj.point is not None

    @admin.display(boolean=True, description="Embedding")
    def has_embedding(self, obj):
        return obj.embedding is not None


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ("image", "preview", "caption", "is_primary")
    readonly_fields = ("preview",)

    @admin.display(description="Preview")
    def preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.image.url,
            )
        return "No image"


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "location",
        "price_per_night",
        "max_guests",
        "image_count",
        "created_at",
    )
    list_filter = ("location", "max_guests", "created_at")
    search_fields = ("title", "description", "address", "location__name")
    list_select_related = ("location",)
    inlines = (PropertyImageInline,)

    @admin.display(description="Images")
    def image_count(self, obj):
        return obj.images.count()


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("property", "caption", "is_primary", "uploaded_at")
    list_filter = ("is_primary", "uploaded_at")
    search_fields = ("property__title", "caption")
    list_select_related = ("property",)
