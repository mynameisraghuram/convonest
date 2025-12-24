from django.contrib import admin

from .models import Template, TemplateButtonConfig


class TemplateButtonConfigInline(admin.TabularInline):
    model = TemplateButtonConfig
    extra = 0


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "language",
        "category",
        "status",
        "quality_rating",
        "is_paused",
        "source",
        "created_at",
    )
    list_filter = ("category", "status", "is_paused", "language", "source")
    search_fields = ("name", "external_id", "group_key")
    inlines = [TemplateButtonConfigInline]


@admin.register(TemplateButtonConfig)
class TemplateButtonConfigAdmin(admin.ModelAdmin):
    list_display = ("template", "index", "button_type", "text")
    list_filter = ("button_type",)
    search_fields = ("template__name", "text")
