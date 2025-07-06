from django.contrib import admin
from django.utils.html import format_html
from .models import PricingConfig


@admin.register(PricingConfig)
class PricingConfigAdmin(admin.ModelAdmin):
    """Pricing configuration admin (singleton)."""
    
    list_display = (
        'hourly_clean_base_display', 'placement_fee_domestic_display', 
        'commission_rate_percentage', 'updated_at'
    )
    
    fieldsets = (
        ('Service Pricing', {
            'fields': (
                'hourly_clean_base', 'specialty_task_price', 'outdoor_min_price',
                'booking_fee', 'cancellation_fee', 'minimum_booking_amount'
            ),
        }),
        ('Placement Fees', {
            'fields': ('placement_fee_domestic', 'placement_fee_nanny'),
        }),
        ('Commission & Multipliers', {
            'fields': (
                'provider_commission_rate', 'weekend_multiplier', 'holiday_multiplier'
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        """Only allow one pricing config instance."""
        return not PricingConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Don't allow deletion of pricing config."""
        return False
    
    def hourly_clean_base_display(self, obj):
        """Display formatted hourly rate."""
        return format_html('<strong>AOA {:,}/hour</strong>', obj.hourly_clean_base)
    hourly_clean_base_display.short_description = 'Base Hourly Rate'
    
    def placement_fee_domestic_display(self, obj):
        """Display formatted placement fee."""
        return format_html('<strong>AOA {:,}</strong>', obj.placement_fee_domestic)
    placement_fee_domestic_display.short_description = 'Domestic Placement Fee'
    
    def commission_rate_percentage(self, obj):
        """Display commission rate as percentage."""
        return f"{obj.provider_commission_rate * 100:.1f}%"
    commission_rate_percentage.short_description = 'Commission Rate'
    
    def changelist_view(self, request, extra_context=None):
        """Customize changelist view for singleton."""
        extra_context = extra_context or {}
        extra_context['title'] = 'Pricing Configuration'
        return super().changelist_view(request, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Customize change view."""
        extra_context = extra_context or {}
        extra_context['title'] = 'Update Pricing Configuration'
        return super().change_view(request, object_id, form_url, extra_context)
