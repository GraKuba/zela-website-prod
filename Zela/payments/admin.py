from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, Payout, RecentTransaction, ProviderWallet, EarningsHistory, PayoutRequest


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


@admin.register(ProviderWallet)
class ProviderWalletAdmin(admin.ModelAdmin):
    """Provider Wallet admin."""
    
    list_display = (
        'provider_display', 'available_balance_display', 'pending_balance_display',
        'total_balance_display', 'last_payout_date', 'updated_at'
    )
    list_filter = ('created_at', 'updated_at', 'last_payout_date')
    search_fields = ('provider__username', 'provider__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)
    
    fieldsets = (
        ('Provider', {
            'fields': ('provider',),
        }),
        ('Balances', {
            'fields': ('available_balance', 'pending_balance', 'total_withdrawn'),
        }),
        ('Payout Information', {
            'fields': ('last_payout_date',),
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
    
    def available_balance_display(self, obj):
        """Display formatted available balance."""
        return format_html('<strong>R$ {:,.2f}</strong>', obj.available_balance)
    available_balance_display.short_description = 'Available'
    
    def pending_balance_display(self, obj):
        """Display formatted pending balance."""
        return format_html('<strong>R$ {:,.2f}</strong>', obj.pending_balance)
    pending_balance_display.short_description = 'Pending'
    
    def total_balance_display(self, obj):
        """Display formatted total balance."""
        return format_html('<strong>R$ {:,.2f}</strong>', obj.total_balance)
    total_balance_display.short_description = 'Total'


@admin.register(EarningsHistory)
class EarningsHistoryAdmin(admin.ModelAdmin):
    """Earnings History admin."""
    
    list_display = (
        'provider_display', 'date', 'jobs_count', 'gross_amount_display',
        'commission_amount_display', 'tips_amount_display', 'net_amount_display'
    )
    list_filter = ('date', 'created_at')
    search_fields = ('provider__username', 'provider__email')
    readonly_fields = ('net_amount', 'created_at', 'updated_at')
    ordering = ('-date',)
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Provider & Date', {
            'fields': ('provider', 'date', 'jobs_count'),
        }),
        ('Earnings', {
            'fields': ('gross_amount', 'commission_amount', 'tips_amount', 'net_amount'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def provider_display(self, obj):
        """Display provider info."""
        name = obj.provider.get_full_name() or obj.provider.username
        return format_html('<strong>{}</strong>', name)
    provider_display.short_description = 'Provider'
    
    def gross_amount_display(self, obj):
        """Display formatted gross amount."""
        return format_html('R$ {:,.2f}', obj.gross_amount)
    gross_amount_display.short_description = 'Gross'
    
    def commission_amount_display(self, obj):
        """Display formatted commission amount."""
        return format_html('<span style="color: red">-R$ {:,.2f}</span>', obj.commission_amount)
    commission_amount_display.short_description = 'Commission'
    
    def tips_amount_display(self, obj):
        """Display formatted tips amount."""
        return format_html('<span style="color: green">+R$ {:,.2f}</span>', obj.tips_amount)
    tips_amount_display.short_description = 'Tips'
    
    def net_amount_display(self, obj):
        """Display formatted net amount."""
        return format_html('<strong>R$ {:,.2f}</strong>', obj.net_amount)
    net_amount_display.short_description = 'Net'


@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    """Payout Request admin."""
    
    list_display = (
        'reference', 'provider_display', 'payout_type', 'amount_display',
        'fee_amount_display', 'net_amount_display', 'status', 'requested_at'
    )
    list_filter = ('payout_type', 'status', 'requested_at', 'processed_at')
    search_fields = ('reference', 'provider__username', 'provider__email', 'bank_reference')
    readonly_fields = ('reference', 'net_amount', 'requested_at', 'processed_at', 'completed_at')
    ordering = ('-requested_at',)
    
    fieldsets = (
        ('Request Information', {
            'fields': ('provider', 'reference', 'payout_type'),
        }),
        ('Amounts', {
            'fields': ('amount', 'fee_amount', 'net_amount'),
        }),
        ('Status', {
            'fields': ('status', 'bank_reference'),
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'processed_at', 'completed_at'),
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
    
    def amount_display(self, obj):
        """Display formatted amount."""
        return format_html('<strong>R$ {:,.2f}</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def fee_amount_display(self, obj):
        """Display formatted fee amount."""
        if obj.fee_amount > 0:
            return format_html('<span style="color: red">-R$ {:,.2f}</span>', obj.fee_amount)
        return 'R$ 0.00'
    fee_amount_display.short_description = 'Fee'
    
    def net_amount_display(self, obj):
        """Display formatted net amount."""
        return format_html('<strong style="color: green">R$ {:,.2f}</strong>', obj.net_amount)
    net_amount_display.short_description = 'Net Amount'
