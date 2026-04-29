from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PasswordResetRequest


# ✅ Custom User Admin
class CustomUserAdmin(UserAdmin):
    model = User

    # 🔹 Show in list view
    list_display = ('username', 'employee_code', 'role', 'is_approved', 'is_staff')
    list_filter = ('role', 'is_approved', 'is_staff')

    # 🔹 Field layout in admin form
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('employee_code', 'phone', 'role', 'is_approved')
        }),
    )

    # 🔹 Fields while creating user
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('employee_code', 'phone', 'role', 'is_approved')
        }),
    )

    search_fields = ('username', 'employee_code', 'phone')
    ordering = ('username',)

class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at', 'approved_at')
    list_filter = ('status',)
    search_fields = ('user__username',)
    readonly_fields = ('token', 'created_at')

admin.site.register(PasswordResetRequest, PasswordResetRequestAdmin)

admin.site.register(User, CustomUserAdmin)
