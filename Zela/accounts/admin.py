from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, ProviderProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin with role-based organization."""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'locale'),
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'locale'),
        }),
    )
    
    def get_queryset(self, request):
        """Optimize query with related objects."""
        return super().get_queryset(request).select_related()


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    """Provider profile admin."""
    
    list_display = (
        'user_display', 'service_area', 'is_approved', 'rating_display', 
        'skills_count', 'created_at'
    )
    list_filter = ('is_approved', 'service_area', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'service_area')
    readonly_fields = ('created_at', 'updated_at', 'rating_average', 'rating_count')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Provider Information', {
            'fields': ('user', 'is_approved', 'bio', 'service_area'),
        }),
        ('Skills & Documents', {
            'fields': ('skills', 'id_document'),
        }),
        ('Ratings', {
            'fields': ('rating_average', 'rating_count'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def user_display(self, obj):
        """Display user with name and email."""
        name = obj.user.get_full_name() or obj.user.username
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            name, obj.user.email
        )
    user_display.short_description = 'Provider'
    
    def rating_display(self, obj):
        """Display rating with stars."""
        if obj.rating_count == 0:
            return "No ratings"
        
        stars = "★" * int(obj.rating_average) + "☆" * (5 - int(obj.rating_average))
        return format_html(
            '{} <small>({:.1f} avg, {} reviews)</small>',
            stars, obj.rating_average, obj.rating_count
        )
    rating_display.short_description = 'Rating'
    
    def skills_count(self, obj):
        """Display number of skills."""
        return len(obj.skills) if obj.skills else 0
    skills_count.short_description = 'Skills'
    
    actions = ['approve_providers', 'reject_providers']
    
    def approve_providers(self, request, queryset):
        """Approve selected providers."""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} providers approved.')
    approve_providers.short_description = 'Approve selected providers'
    
    def reject_providers(self, request, queryset):
        """Reject selected providers."""
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} providers rejected.')
    reject_providers.short_description = 'Reject selected providers'
