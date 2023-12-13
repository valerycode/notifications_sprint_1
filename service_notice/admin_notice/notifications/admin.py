from django.contrib import admin

from .models import Notification, Template


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
