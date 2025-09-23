from django.contrib import admin
from django.utils.html import format_html
from .models import (
    PropertyTypology, Worker, CleaningWorker, ElectricianWorker,
    ACTechnicianWorker, PestControlWorker, DogTrainerWorker,
    HandymanWorker, GardenerWorker, PlacementWorker, ServicePackage,
    WorkerService, WorkerServicePricing
)


@admin.register(PropertyTypology)
class PropertyTypologyAdmin(admin.ModelAdmin):
    """Admin for property typology."""
    list_display = ('name', 'typical_sqm', 'description')
    search_fields = ('name', 'description')
    ordering = ('name',)


class WorkerAdmin(admin.ModelAdmin):
    """Base admin for all worker models."""
    list_display = (
        'user', 'display_name', 'status', 'is_verified',
        'rating_display', 'jobs_completed', 'is_available'
    )
    list_filter = (
        'status', 'is_verified', 'background_check',
        'is_available', 'accepts_emergency', 'accepts_same_day'
    )
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'user__email', 'bio'
    )
    readonly_fields = (
        'rating_average', 'rating_count', 'jobs_completed',
        'jobs_cancelled', 'completion_rate', 'total_earnings',
        'created_at', 'updated_at', 'approved_at', 'last_active'
    )
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'bio', 'years_experience', 'languages')
        }),
        ('Verification', {
            'fields': (
                'status', 'is_verified', 'background_check',
                'id_document', 'proof_of_address'
            )
        }),
        ('Performance', {
            'fields': (
                'rating_average', 'rating_count', 'jobs_completed',
                'jobs_cancelled', 'completion_rate'
            ),
            'classes': ('collapse',)
        }),
        ('Financial', {
            'fields': ('total_earnings', 'current_balance'),
            'classes': ('collapse',)
        }),
        ('Availability', {
            'fields': (
                'is_available', 'accepts_emergency', 'accepts_same_day',
                'service_areas', 'max_travel_distance', 'working_hours'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'approved_at', 'last_active'),
            'classes': ('collapse',)
        }),
    )
    
    def display_name(self, obj):
        """Display worker type name."""
        return obj.__class__.__name__.replace('Worker', '')
    display_name.short_description = 'Type'
    
    def rating_display(self, obj):
        """Display formatted rating."""
        if obj.rating_count == 0:
            return '-'
        return format_html(
            '<span style="color: #f39c12;">{} ★</span> ({})',
            f"{obj.rating_average:.1f}", obj.rating_count
        )
    rating_display.short_description = 'Rating'
    
    actions = ['approve_workers', 'suspend_workers', 'mark_available', 'mark_unavailable']
    
    def approve_workers(self, request, queryset):
        """Approve selected workers."""
        from django.utils import timezone
        updated = queryset.update(status='approved', approved_at=timezone.now())
        self.message_user(request, f'{updated} workers approved.')
    approve_workers.short_description = 'Approve selected workers'
    
    def suspend_workers(self, request, queryset):
        """Suspend selected workers."""
        updated = queryset.update(status='suspended')
        self.message_user(request, f'{updated} workers suspended.')
    suspend_workers.short_description = 'Suspend selected workers'
    
    def mark_available(self, request, queryset):
        """Mark workers as available."""
        updated = queryset.update(is_available=True)
        self.message_user(request, f'{updated} workers marked as available.')
    mark_available.short_description = 'Mark as available'
    
    def mark_unavailable(self, request, queryset):
        """Mark workers as unavailable."""
        updated = queryset.update(is_available=False)
        self.message_user(request, f'{updated} workers marked as unavailable.')
    mark_unavailable.short_description = 'Mark as unavailable'


@admin.register(Worker)
class BaseWorkerAdmin(WorkerAdmin):
    """Admin for base Worker model."""
    pass


@admin.register(CleaningWorker)
class CleaningWorkerAdmin(WorkerAdmin):
    """Admin for cleaning workers."""
    fieldsets = WorkerAdmin.fieldsets + (
        ('Cleaning Specifics', {
            'fields': (
                'specializations', 'cleaning_types',
                'has_own_supplies', 'has_own_equipment',
                'certifications'
            )
        }),
    )


@admin.register(ElectricianWorker)
class ElectricianWorkerAdmin(WorkerAdmin):
    """Admin for electricians."""
    fieldsets = WorkerAdmin.fieldsets + (
        ('Electrician Specifics', {
            'fields': (
                'license_number', 'license_expiry',
                'voltage_certifications', 'specializations',
                'minimum_hours', 'typology_rates',
                'emergency_surcharge'
            )
        }),
    )
    list_display = WorkerAdmin.list_display + ('license_number', 'minimum_hours')


@admin.register(ACTechnicianWorker)
class ACTechnicianWorkerAdmin(WorkerAdmin):
    """Admin for AC technicians."""
    fieldsets = WorkerAdmin.fieldsets + (
        ('AC Technician Specifics', {
            'fields': (
                'hvac_certification', 'refrigerant_license',
                'brands_serviced', 'service_types',
                'unit_pricing', 'has_diagnostic_tools'
            )
        }),
    )
    list_display = WorkerAdmin.list_display + ('hvac_certification',)


@admin.register(PestControlWorker)
class PestControlWorkerAdmin(WorkerAdmin):
    """Admin for pest control workers."""
    fieldsets = WorkerAdmin.fieldsets + (
        ('Pest Control Specifics', {
            'fields': (
                'pest_control_license', 'chemical_certification',
                'service_types', 'chemicals_used',
                'eco_friendly_options', 'typology_pricing'
            )
        }),
    )
    list_display = WorkerAdmin.list_display + ('service_types', 'eco_friendly_options')


@admin.register(DogTrainerWorker)
class DogTrainerWorkerAdmin(WorkerAdmin):
    """Admin for dog trainers."""
    fieldsets = WorkerAdmin.fieldsets + (
        ('Dog Trainer Specifics', {
            'fields': (
                'certifications', 'training_methods',
                'specializations', 'breed_experience',
                'max_dogs_per_session', 'offers_group_classes',
                'package_offerings'
            )
        }),
    )
    list_display = WorkerAdmin.list_display + ('training_methods', 'offers_group_classes')


@admin.register(HandymanWorker)
class HandymanWorkerAdmin(WorkerAdmin):
    """Admin for handymen."""
    fieldsets = WorkerAdmin.fieldsets + (
        ('Handyman Specifics', {
            'fields': (
                'skills', 'tools_owned',
                'can_source_materials', 'project_portfolio',
                'hourly_rate'
            )
        }),
    )
    list_display = WorkerAdmin.list_display + ('hourly_rate', 'can_source_materials')


@admin.register(GardenerWorker)
class GardenerWorkerAdmin(WorkerAdmin):
    """Admin for gardeners."""
    fieldsets = WorkerAdmin.fieldsets + (
        ('Gardener Specifics', {
            'fields': (
                'services_offered', 'equipment_owned',
                'plant_knowledge', 'pesticide_license',
                'landscape_design'
            )
        }),
    )
    list_display = WorkerAdmin.list_display + ('landscape_design',)


@admin.register(PlacementWorker)
class PlacementWorkerAdmin(WorkerAdmin):
    """Admin for placement workers."""
    fieldsets = WorkerAdmin.fieldsets + (
        ('Placement Specifics', {
            'fields': (
                'placement_type', 'domestic_skills',
                'cooking_specialties', 'childcare_experience',
                'first_aid_certified', 'drivers_license',
                'minimum_contract_months', 'expected_salary',
                'placement_fee'
            )
        }),
    )
    list_display = WorkerAdmin.list_display + (
        'placement_type', 'childcare_experience', 'drivers_license'
    )


@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    """Admin for service packages."""
    list_display = (
        'package_name', 'customer', 'worker',
        'credits_display', 'status', 'purchase_date', 'expiry_date'
    )
    list_filter = ('status', 'package_type', 'purchase_date')
    search_fields = (
        'customer__username', 'customer__email',
        'worker__user__username', 'package_name'
    )
    readonly_fields = ('purchase_date',)
    
    fieldsets = (
        ('Package Information', {
            'fields': (
                'customer', 'worker', 'package_name',
                'package_type', 'amount_paid'
            )
        }),
        ('Credits', {
            'fields': ('total_credits', 'used_credits')
        }),
        ('Status', {
            'fields': ('status', 'purchase_date', 'expiry_date')
        }),
        ('Additional', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def credits_display(self, obj):
        """Display credits usage."""
        remaining = obj.remaining_credits
        color = 'green' if remaining > 0 else 'red'
        return format_html(
            '<span style="color: {};">{}/{}</span>',
            color, remaining, obj.total_credits
        )
    credits_display.short_description = 'Credits (Remaining/Total)'
    
    actions = ['mark_as_active', 'mark_as_expired']
    
    def mark_as_active(self, request, queryset):
        """Mark packages as active."""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} packages marked as active.')
    mark_as_active.short_description = 'Mark as active'
    
    def mark_as_expired(self, request, queryset):
        """Mark packages as expired."""
        updated = queryset.update(status='expired')
        self.message_user(request, f'{updated} packages marked as expired.')
    mark_as_expired.short_description = 'Mark as expired'


@admin.register(WorkerService)
class WorkerServiceAdmin(admin.ModelAdmin):
    """Admin for worker-service relationships."""
    list_display = (
        'worker', 'service_category', 'is_verified', 'priority', 'created_at'
    )
    list_filter = ('is_verified', 'service_category', 'created_at')
    search_fields = (
        'worker__user__username', 'worker__user__first_name', 'worker__user__last_name',
        'service_category__name'
    )
    list_editable = ('is_verified', 'priority')
    ordering = ('-priority', 'created_at')
    
    fieldsets = (
        ('Relationship', {
            'fields': ('worker', 'service_category')
        }),
        ('Configuration', {
            'fields': ('is_verified', 'priority')
        }),
    )
    
    actions = ['verify_services', 'unverify_services']
    
    def verify_services(self, request, queryset):
        """Verify selected worker services."""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} worker services verified.')
    verify_services.short_description = 'Verify selected services'
    
    def unverify_services(self, request, queryset):
        """Unverify selected worker services."""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} worker services unverified.')
    unverify_services.short_description = 'Unverify selected services'


@admin.register(WorkerServicePricing)
class WorkerServicePricingAdmin(admin.ModelAdmin):
    """Admin for worker service pricing."""
    list_display = (
        'worker_service', 'markup_percentage', 'minimum_price', 'is_active', 'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = (
        'worker_service__worker__user__username',
        'worker_service__service_category__name'
    )
    list_editable = ('markup_percentage', 'minimum_price', 'is_active')
    
    fieldsets = (
        ('Worker Service', {
            'fields': ('worker_service',)
        }),
        ('Pricing Configuration', {
            'fields': ('pricing_config', 'markup_percentage', 'minimum_price')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make created_at readonly."""
        readonly = ['created_at', 'updated_at']
        if obj:  # Editing existing object
            readonly.append('worker_service')
        return readonly
