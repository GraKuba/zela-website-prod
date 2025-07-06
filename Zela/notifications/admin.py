from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification admin."""
    
    list_display = (
        'user_display', 'title', 'notification_type', 'is_read', 
        'is_important', 'time_since_created', 'created_at'
    )
    list_filter = ('notification_type', 'is_read', 'is_important', 'created_at')
    search_fields = ('user__username', 'user__email', 'title', 'message')
    readonly_fields = ('created_at', 'read_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'title', 'message', 'notification_type'),
        }),
        ('Options', {
            'fields': ('link', 'is_important', 'expires_at'),
        }),
        ('Status', {
            'fields': ('is_read', 'read_at'),
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def user_display(self, obj):
        """Display user info."""
        name = obj.user.get_full_name() or obj.user.username
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            name, obj.user.email
        )
    user_display.short_description = 'User'
    
    def time_since_created(self, obj):
        """Display time since creation."""
        return obj.time_since_created
    time_since_created.short_description = 'Created'
    
    actions = ['mark_as_read', 'mark_as_unread', 'mark_as_important', 'mark_as_normal']
    
    def mark_as_read(self, request, queryset):
        """Mark notifications as read."""
        updated = 0
        for notification in queryset:
            if not notification.is_read:
                notification.mark_as_read()
                updated += 1
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark as read'
    
    def mark_as_unread(self, request, queryset):
        """Mark notifications as unread."""
        updated = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark as unread'
    
    def mark_as_important(self, request, queryset):
        """Mark notifications as important."""
        updated = queryset.update(is_important=True)
        self.message_user(request, f'{updated} notifications marked as important.')
    mark_as_important.short_description = 'Mark as important'
    
    def mark_as_normal(self, request, queryset):
        """Mark notifications as normal."""
        updated = queryset.update(is_important=False)
        self.message_user(request, f'{updated} notifications marked as normal.')
    mark_as_normal.short_description = 'Mark as normal'
