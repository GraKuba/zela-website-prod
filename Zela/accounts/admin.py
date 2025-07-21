from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, ProviderProfile, Profile, PaymentMethod, Location, DistanceRequest, ProviderDocument, ProviderContract, UserSettings


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
        'user_display', 'service_area', 'is_approved', 'is_available',
        'rating_display', 'completion_rate_display', 'total_earnings_display',
        'skills_count', 'created_at'
    )
    list_filter = (
        'is_approved', 'is_available', 'accepts_same_day', 
        'include_traffic_time', 'avoid_tolls', 'prefer_main_roads',
        'service_area', 'created_at'
    )
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'service_area')
    readonly_fields = (
        'created_at', 'updated_at', 'rating_average', 'rating_count',
        'total_earnings', 'jobs_completed', 'jobs_total', 'completion_rate'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Provider Information', {
            'fields': ('user', 'is_approved', 'bio'),
        }),
        ('Availability', {
            'fields': ('is_available', 'accepts_same_day', 'working_hours'),
        }),
        ('Service Areas & Coverage', {
            'fields': (
                'service_area', 'service_areas', 'max_travel_distance',
                'preferred_radius'
            ),
        }),
        ('Travel Preferences', {
            'fields': (
                'include_traffic_time', 'avoid_tolls', 'prefer_main_roads'
            ),
        }),
        ('Skills & Documents', {
            'fields': ('skills', 'id_document'),
        }),
        ('Performance Statistics', {
            'fields': (
                'rating_average', 'rating_count', 'total_earnings',
                'jobs_completed', 'jobs_total', 'completion_rate'
            ),
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
            '{} <small>({} avg, {} reviews)</small>',
            stars, f'{obj.rating_average:.1f}', obj.rating_count
        )
    rating_display.short_description = 'Rating'
    
    def skills_count(self, obj):
        """Display number of skills."""
        return len(obj.skills) if obj.skills else 0
    skills_count.short_description = 'Skills'
    
    def completion_rate_display(self, obj):
        """Display completion rate."""
        return format_html('{}%', f'{obj.completion_rate:.1f}')
    completion_rate_display.short_description = 'Completion Rate'
    
    def total_earnings_display(self, obj):
        """Display total earnings with currency."""
        return format_html('Kz {}', f'{obj.total_earnings:,.2f}')
    total_earnings_display.short_description = 'Total Earnings'
    
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


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """User profile admin."""
    
    list_display = (
        'user_display', 'has_profile_picture', 'full_name', 
        'email_notifications', 'sms_notifications', 'newsletter', 
        'marketing_communications', 'created_at'
    )
    list_filter = ('email_notifications', 'sms_notifications', 'newsletter', 
                   'marketing_communications', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'first_name', 'last_name'),
        }),
        ('Profile Picture', {
            'fields': ('profile_picture',),
        }),
        ('Notification Preferences', {
            'fields': ('email_notifications', 'sms_notifications', 
                      'newsletter', 'marketing_communications'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def user_display(self, obj):
        """Display user with username and email."""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.user.username, obj.user.email
        )
    user_display.short_description = 'User'
    
    def has_profile_picture(self, obj):
        """Check if profile has a picture."""
        return bool(obj.profile_picture)
    has_profile_picture.boolean = True
    has_profile_picture.short_description = 'Has Picture'
    
    def full_name(self, obj):
        """Display full name from profile or user."""
        first = obj.first_name or obj.user.first_name
        last = obj.last_name or obj.user.last_name
        if first or last:
            return f"{first} {last}".strip()
        return "-"
    full_name.short_description = 'Full Name'


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Payment method admin."""
    
    list_display = (
        'user_display', 'kind', 'brand_display', 'last4_display', 
        'expiry_display', 'is_default', 'is_active', 'added_at'
    )
    list_filter = ('kind', 'brand', 'is_default', 'is_active', 'added_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 
                     'user__last_name', 'last4', 'provider_id')
    readonly_fields = ('added_at',)
    ordering = ('-added_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',),
        }),
        ('Payment Details', {
            'fields': ('kind', 'provider_id', 'brand', 'last4', 'is_default', 'is_active'),
        }),
        ('Card Details', {
            'fields': ('expiry_month', 'expiry_year'),
            'description': 'Only applicable for card payment methods',
        }),
        ('Metadata', {
            'fields': ('added_at',),
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
    user_display.short_description = 'User'
    
    def brand_display(self, obj):
        """Display card brand with icon."""
        if obj.brand:
            brand_icons = {
                'visa': '💳',
                'mastercard': '💳',
                'amex': '💳',
                'discover': '💳',
            }
            icon = brand_icons.get(obj.brand.lower(), '💳')
            return format_html('{} {}', icon, obj.brand.title())
        return '-'
    brand_display.short_description = 'Brand'
    
    def last4_display(self, obj):
        """Display masked card number."""
        if obj.last4:
            return f'•••• •••• •••• {obj.last4}'
        return '-'
    last4_display.short_description = 'Card Number'
    
    def expiry_display(self, obj):
        """Display card expiry date."""
        if obj.expiry_month and obj.expiry_year:
            return f'{obj.expiry_month:02d}/{obj.expiry_year % 100:02d}'
        return '-'
    expiry_display.short_description = 'Expires'
    
    def get_queryset(self, request):
        """Optimize query with related objects."""
        return super().get_queryset(request).select_related('user')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Location admin."""
    
    list_display = (
        'user_display', 'name', 'address_display', 'city', 'is_main', 'created_at'
    )
    list_filter = ('is_main', 'city', 'province', 'created_at')
    search_fields = ('user__username', 'user__email', 'name', 'address_line_1', 'city')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',),
        }),
        ('Location Details', {
            'fields': ('name', 'is_main'),
        }),
        ('Address', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'province', 'postal_code', 'country'),
        }),
        ('Coordinates', {
            'fields': ('latitude', 'longitude'),
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
    user_display.short_description = 'User'
    
    def address_display(self, obj):
        """Display short address."""
        address = obj.address_line_1
        if obj.address_line_2:
            address += f", {obj.address_line_2}"
        return address
    address_display.short_description = 'Address'
    
    def get_queryset(self, request):
        """Optimize query with related objects."""
        return super().get_queryset(request).select_related('user')
    
    actions = ['set_as_main_location']
    
    def set_as_main_location(self, request, queryset):
        """Set selected locations as main."""
        for location in queryset:
            location.is_main = True
            location.save()
        self.message_user(request, f'{queryset.count()} location(s) set as main.')
    set_as_main_location.short_description = 'Set as main location'


@admin.register(DistanceRequest)
class DistanceRequestAdmin(admin.ModelAdmin):
    """Distance request admin."""
    
    list_display = (
        'provider_display', 'route_display', 'distance_km', 
        'surcharge_display', 'service_name', 'status', 'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = (
        'provider__username', 'provider__email', 
        'from_location', 'to_location', 'service_name'
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Provider Information', {
            'fields': ('provider',),
        }),
        ('Request Details', {
            'fields': ('booking', 'from_location', 'to_location', 
                      'distance_km', 'surcharge_amount', 'service_name'),
        }),
        ('Status', {
            'fields': ('status',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def provider_display(self, obj):
        """Display provider with name."""
        name = obj.provider.get_full_name() or obj.provider.username
        return name
    provider_display.short_description = 'Provider'
    
    def route_display(self, obj):
        """Display route."""
        return f"{obj.from_location} → {obj.to_location}"
    route_display.short_description = 'Route'
    
    def surcharge_display(self, obj):
        """Display surcharge with currency."""
        return f"R$ {obj.surcharge_amount:.2f}"
    surcharge_display.short_description = 'Surcharge'
    
    def get_queryset(self, request):
        """Optimize query with related objects."""
        return super().get_queryset(request).select_related('provider', 'booking')


@admin.register(ProviderDocument)
class ProviderDocumentAdmin(admin.ModelAdmin):
    """Provider document admin."""
    
    list_display = (
        'provider_display', 'document_type', 'status', 'file_name',
        'is_required', 'uploaded_at', 'expiry_date', 'is_expired'
    )
    list_filter = ('status', 'document_type', 'is_required', 'uploaded_at', 'expiry_date')
    search_fields = (
        'provider__user__username', 'provider__user__email',
        'provider__user__first_name', 'provider__user__last_name',
        'file_name', 'rejection_reason'
    )
    readonly_fields = ('uploaded_at', 'verified_at', 'is_expired')
    ordering = ('-uploaded_at',)
    
    fieldsets = (
        ('Provider Information', {
            'fields': ('provider',),
        }),
        ('Document Details', {
            'fields': ('document_type', 'file', 'file_name', 'is_required'),
        }),
        ('Verification', {
            'fields': ('status', 'verified_by', 'verified_at', 'rejection_reason'),
        }),
        ('Validity', {
            'fields': ('expiry_date', 'is_expired'),
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',),
        }),
    )
    
    def provider_display(self, obj):
        """Display provider with name."""
        name = obj.provider.user.get_full_name() or obj.provider.user.username
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            name, obj.provider.user.email
        )
    provider_display.short_description = 'Provider'
    
    def get_queryset(self, request):
        """Optimize query with related objects."""
        return super().get_queryset(request).select_related(
            'provider__user', 'verified_by'
        )
    
    actions = ['verify_documents', 'reject_documents', 'mark_as_expired']
    
    def verify_documents(self, request, queryset):
        """Verify selected documents."""
        from django.utils import timezone
        updated = queryset.update(
            status='verified',
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(request, f'{updated} document(s) verified.')
    verify_documents.short_description = 'Verify selected documents'
    
    def reject_documents(self, request, queryset):
        """Reject selected documents."""
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} document(s) rejected.')
    reject_documents.short_description = 'Reject selected documents'
    
    def mark_as_expired(self, request, queryset):
        """Mark selected documents as expired."""
        updated = queryset.update(status='expired')
        self.message_user(request, f'{updated} document(s) marked as expired.')
    mark_as_expired.short_description = 'Mark as expired'


@admin.register(ProviderContract)
class ProviderContractAdmin(admin.ModelAdmin):
    """Provider contract admin."""
    
    list_display = (
        'provider_display', 'title', 'contract_type', 'version',
        'status', 'signed_at', 'expires_at', 'is_active'
    )
    list_filter = ('status', 'contract_type', 'created_at', 'signed_at', 'expires_at')
    search_fields = (
        'provider__user__username', 'provider__user__email',
        'provider__user__first_name', 'provider__user__last_name',
        'title'
    )
    readonly_fields = ('created_at', 'is_active')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Provider Information', {
            'fields': ('provider',),
        }),
        ('Contract Details', {
            'fields': ('contract_type', 'title', 'version', 'file'),
        }),
        ('Signature', {
            'fields': ('status', 'signed_at', 'ip_address'),
        }),
        ('Validity', {
            'fields': ('expires_at', 'is_active'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def provider_display(self, obj):
        """Display provider with name."""
        name = obj.provider.user.get_full_name() or obj.provider.user.username
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            name, obj.provider.user.email
        )
    provider_display.short_description = 'Provider'
    
    def get_queryset(self, request):
        """Optimize query with related objects."""
        return super().get_queryset(request).select_related('provider__user')
    
    actions = ['mark_as_signed', 'mark_as_acknowledged']
    
    def mark_as_signed(self, request, queryset):
        """Mark selected contracts as signed."""
        from django.utils import timezone
        updated = queryset.update(
            status='signed',
            signed_at=timezone.now()
        )
        self.message_user(request, f'{updated} contract(s) marked as signed.')
    mark_as_signed.short_description = 'Mark as signed'
    
    def mark_as_acknowledged(self, request, queryset):
        """Mark selected contracts as acknowledged."""
        from django.utils import timezone
        updated = queryset.update(
            status='acknowledged',
            signed_at=timezone.now()
        )
        self.message_user(request, f'{updated} contract(s) marked as acknowledged.')
    mark_as_acknowledged.short_description = 'Mark as acknowledged'


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    """User settings admin."""
    
    list_display = (
        'user_display', 'language', 'timezone', 'currency', 'theme', 
        'profile_visibility', 'created_at'
    )
    list_filter = (
        'language', 'currency', 'theme', 'profile_visibility',
        'job_alerts', 'payment_alerts', 'created_at'
    )
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',),
        }),
        ('Notification Settings', {
            'fields': (
                'job_alerts', 'payment_alerts', 'weekly_reports',
                'push_notifications', 'system_updates'
            ),
        }),
        ('Privacy Settings', {
            'fields': (
                'profile_visibility', 'share_location', 'share_statistics',
                'allow_reviews', 'data_collection'
            ),
        }),
        ('Work Preferences', {
            'fields': (
                'auto_accept_jobs', 'max_jobs_per_day', 'preferred_job_types',
                'minimum_job_value', 'travel_radius'
            ),
            'description': 'Only applicable for provider users',
        }),
        ('App Preferences', {
            'fields': ('language', 'timezone', 'currency', 'theme', 'map_view'),
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
    user_display.short_description = 'User'
    
    def get_queryset(self, request):
        """Optimize query with related objects."""
        return super().get_queryset(request).select_related('user')
