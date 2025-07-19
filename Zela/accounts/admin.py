from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, ProviderProfile, Profile, PaymentMethod, Location


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
