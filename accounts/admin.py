from django.contrib import admin

from accounts.models import User, LinkedChessAccount


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "is_staff", "date_joined")
    search_fields = ("username", "email")
    list_filter = ("is_staff", "is_active", "date_joined")


@admin.register(LinkedChessAccount)
class LinkedChessAccountAdmin(admin.ModelAdmin):
    list_display = ("platform", "platform_username", "user", "is_primary", "rating", "linked_at")
    list_filter = ("platform", "is_primary")
    search_fields = ("platform_username", "user__username")
