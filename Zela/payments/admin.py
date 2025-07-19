from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, Payout, RecentTransaction


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payment admin."""
    
    list_display = (
        'reference', 'booking_id', 'customer_display', 'amount_display', 
        'gateway', 'status', 'created_at'
    )
    list_filter = ('gateway', 'status', 'created_at')
    search_fields = ('reference', 'booking__customer__username', 'booking__customer__email')
    readonly_fields = ('reference', 'created_at', 'updated_at', 'gateway_response')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('booking', 'provider', 'reference', 'amount'),
        }),
        ('Gateway Details', {
            'fields': ('gateway', 'status', 'gateway_response'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def booking_id(self, obj):
        """Display booking ID."""
        return f"#{obj.booking.pk}"
    booking_id.short_description = 'Booking'
    
    def customer_display(self, obj):
        """Display customer info."""
        customer = obj.booking.customer
        name = customer.get_full_name() or customer.username
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            name, customer.email
        )
    customer_display.short_description = 'Customer'
    
    def amount_display(self, obj):
        """Display formatted amount."""
        return format_html('<strong>AOA {:,}</strong>', obj.amount)
    amount_display.short_description = 'Amount'


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    """Payout admin."""
    
    list_display = (
        'provider_display', 'week_display', 'amount_display', 'net_amount_display',
        'status', 'is_disbursed', 'created_at'
    )
    list_filter = ('status', 'is_disbursed', 'week_start', 'created_at')
    search_fields = ('provider__username', 'provider__email', 'disbursement_reference')
    readonly_fields = ('week_end', 'commission_amount', 'net_amount', 'created_at', 'updated_at')
    ordering = ('-week_start',)
    
    fieldsets = (
        ('Payout Information', {
            'fields': ('provider', 'week_start', 'week_end', 'amount'),
        }),
        ('Commission', {
            'fields': ('commission_rate', 'commission_amount', 'net_amount'),
        }),
        ('Status', {
            'fields': ('status', 'is_disbursed', 'disbursement_reference', 'disbursed_at'),
        }),
        ('Notes', {
            'fields': ('notes',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def provider_display(self, obj):
        """Display provider info."""
        name = obj.provider.get_full_name() or obj.provider.username
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            name, obj.provider.email
        )
    provider_display.short_description = 'Provider'
    
    def week_display(self, obj):
        """Display week range."""
        return f"{obj.week_start} - {obj.week_end}"
    week_display.short_description = 'Week'
    
    def amount_display(self, obj):
        """Display formatted amount."""
        return format_html('<strong>AOA {:,}</strong>', obj.amount)
    amount_display.short_description = 'Gross Amount'
    
    def net_amount_display(self, obj):
        """Display formatted net amount."""
        return format_html('<strong>AOA {:,}</strong>', obj.net_amount)
    net_amount_display.short_description = 'Net Amount'


@admin.register(RecentTransaction)
class RecentTransactionAdmin(admin.ModelAdmin):
    """Recent Transaction admin."""
    
    list_display = (
        'reference', 'user_display', 'transaction_type', 'amount_display',
        'status', 'description', 'created_at'
    )
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('reference', 'user__username', 'user__email', 'description')
    readonly_fields = ('reference', 'created_at', 'updated_at', 'metadata')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('user', 'transaction_type', 'reference', 'amount', 'description'),
        }),
        ('Status', {
            'fields': ('status',),
        }),
        ('Related Records', {
            'fields': ('payment', 'payout'),
            'classes': ('collapse',),
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
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
    
    def amount_display(self, obj):
        """Display formatted amount with credit/debit indicator."""
        if obj.is_credit:
            color = 'green'
            prefix = '+'
        elif obj.is_debit:
            color = 'red'
            prefix = '-'
        else:
            color = 'black'
            prefix = ''
        
        return format_html(
            '<span style="color: {}"><strong>{}AOA {:,}</strong></span>',
            color, prefix, obj.amount
        )
    amount_display.short_description = 'Amount'
