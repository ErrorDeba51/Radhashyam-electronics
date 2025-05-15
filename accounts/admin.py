# radhashyam/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile


class CustomUserAdmin(UserAdmin):

    actions = ['hard_delete_users']

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions['hard_delete_users'] = (
            self.hard_delete_users,
            'hard_delete_users',
            "Permanently delete selected users (immediate removal)"
        )
        return actions

    def hard_delete_users(self, request, queryset):
        """Bypass any deletion protections"""
        from cart.models import Cart
        Cart.objects.filter(user__in=queryset).delete()
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request, f"Permanently deleted {count} users with their carts")

    readonly_fields = ('last_login', 'date_joined')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('phone', 'pincode')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'phone', 'pincode', 'is_staff', 'date_joined')
    search_fields = ('email', 'phone', 'pincode')
    ordering = ('email',)
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    def delete_queryset(self, request, queryset):
        """Override default delete to force hard deletion"""
        self.hard_delete_users(request, queryset)


admin.site.register(UserProfile, CustomUserAdmin)
