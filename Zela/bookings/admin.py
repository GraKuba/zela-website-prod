from django.contrib import admin
from django.utils.html import format_html
from .models import Booking, Rating


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Booking admin."""
    
    list_display = (
        'id', 'customer_display', 'provider_display', 'service_task', 
        'status', 'start_at', 'total_price_display', 'created_at'
    )
    list_filter = ('status', 'start_at', 'created_at', 'service_task__category')
    search_fields = (
        'customer__username', 'customer__email', 'worker__user__username', 
        'worker__user__email', 'service_task__name', 'address'
    )
    date_hierarchy = 'start_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('customer', 'worker', 'service_task', 'extras'),
        }),
        ('Schedule', {
            'fields': ('start_at', 'end_at', 'address'),
        }),
        ('Details', {
            'fields': ('notes', 'status', 'total_price'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('extras',)
    
    def customer_display(self, obj):
        """Display customer info."""
        name = obj.customer.get_full_name() or obj.customer.username
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            name, obj.customer.email
        )
    customer_display.short_description = 'Customer'
    
    def provider_display(self, obj):
        """Display provider info."""
        if not obj.worker:
            return format_html('<em>Not assigned</em>')
        
        name = obj.worker.user.get_full_name() or obj.worker.user.username
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            name, obj.worker.user.email
        )
    provider_display.short_description = 'Provider'
    
    def total_price_display(self, obj):
        """Display formatted total price."""
        return format_html('<strong>{}</strong>', obj.total_price_display)
    total_price_display.short_description = 'Total Price'
    
    actions = ['mark_accepted', 'mark_in_progress', 'mark_completed', 'mark_cancelled']
    
    def mark_accepted(self, request, queryset):
        """Mark bookings as accepted."""
        updated = queryset.filter(status='pending').update(status='accepted')
        self.message_user(request, f'{updated} bookings marked as accepted.')
    mark_accepted.short_description = 'Mark as accepted'
    
    def mark_in_progress(self, request, queryset):
        """Mark bookings as in progress."""
        updated = queryset.filter(status='accepted').update(status='in_progress')
        self.message_user(request, f'{updated} bookings marked as in progress.')
    mark_in_progress.short_description = 'Mark as in progress'
    
    def mark_completed(self, request, queryset):
        """Mark bookings as completed."""
        updated = queryset.filter(status='in_progress').update(status='completed')
        self.message_user(request, f'{updated} bookings marked as completed.')
    mark_completed.short_description = 'Mark as completed'
    
    def mark_cancelled(self, request, queryset):
        """Mark bookings as cancelled."""
        updated = queryset.exclude(status__in=['completed', 'cancelled']).update(status='cancelled')
        self.message_user(request, f'{updated} bookings marked as cancelled.')
    mark_cancelled.short_description = 'Mark as cancelled'


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Rating admin."""
    
    list_display = (
        'booking_display', 'score_display', 'customer_display', 
        'provider_display', 'created'
    )
    list_filter = ('score', 'created')
    search_fields = (
        'booking__customer__username', 'booking__worker__user__username',
        'comment'
    )
    ordering = ('-created',)
    
    fieldsets = (
        ('Rating Information', {
            'fields': ('booking', 'score', 'comment'),
        }),
        ('Timestamp', {
            'fields': ('created',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created',)
    
    def booking_display(self, obj):
        """Display booking info."""
        return format_html(
            'Booking #{} - {}',
            obj.booking.pk, obj.booking.service_task.name
        )
    booking_display.short_description = 'Booking'
    
    def score_display(self, obj):
        """Display rating with stars."""
        stars = "★" * obj.score + "☆" * (5 - obj.score)
        return format_html(
            '{} <span style="color: #666;">({}/5)</span>',
            stars, obj.score
        )
    score_display.short_description = 'Rating'
    
    def customer_display(self, obj):
        """Display customer info."""
        customer = obj.booking.customer
        name = customer.get_full_name() or customer.username
        return name
    customer_display.short_description = 'Customer'
    
    def provider_display(self, obj):
        """Display provider info."""
        if not obj.booking.worker:
            return 'No provider'
        
        provider = obj.booking.worker.user
        name = provider.get_full_name() or provider.username
        return name
    provider_display.short_description = 'Provider'
