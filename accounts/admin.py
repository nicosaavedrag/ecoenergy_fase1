from django.contrib import admin
from .models import UserProfile, PasswordResetCode


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'organization', 'phone')
    list_filter = ('role', 'organization')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'organization__name')
    list_select_related = ('user', 'organization')


@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'expires_at', 'is_used', 'is_valid_display')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'code')
    readonly_fields = ('created_at',)

    @admin.display(boolean=True, description="¿Válido actualmente?")
    def is_valid_display(self, obj):
        return obj.is_valid()
