from django.contrib import admin
from django.utils.html import format_html
from .models import ServiceCategory, ServiceTask


class ServiceTaskInline(admin.TabularInline):
    """Inline admin for service tasks within categories."""
    model = ServiceTask
    extra = 1
    fields = ('name', 'price', 'duration_hours', 'is_addon', 'is_active', 'order')
    ordering = ('order', 'name')


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    """Service category admin."""
    
    list_display = ('name', 'slug', 'icon_display', 'task_count', 'is_active', 'order')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'icon'),
        }),
        ('Display Options', {
            'fields': ('order', 'is_active'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ServiceTaskInline]
    
    def icon_display(self, obj):
        """Display icon with name."""
        return format_html(
            '<i class="icon-{}" style="margin-right: 5px;"></i>{}',
            obj.icon, obj.icon
        )
    icon_display.short_description = 'Icon'
    
    def task_count(self, obj):
        """Display number of tasks in category."""
        return obj.tasks.count()
    task_count.short_description = 'Tasks'


@admin.register(ServiceTask)
class ServiceTaskAdmin(admin.ModelAdmin):
    """Service task admin."""
    
    list_display = (
        'name', 'category', 'price_display', 'duration_hours', 
        'is_addon', 'is_active', 'order'
    )
    list_filter = ('category', 'is_addon', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    ordering = ('category__order', 'order', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'description'),
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'duration_hours'),
        }),
        ('Options', {
            'fields': ('is_addon', 'is_active', 'order'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def price_display(self, obj):
        """Display formatted price."""
        return format_html(
            '<strong>AOA {:,}</strong>',
            obj.price
        )
    price_display.short_description = 'Price'
    
    actions = ['activate_tasks', 'deactivate_tasks', 'mark_as_addon', 'mark_as_main_service']
    
    def activate_tasks(self, request, queryset):
        """Activate selected tasks."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} tasks activated.')
    activate_tasks.short_description = 'Activate selected tasks'
    
    def deactivate_tasks(self, request, queryset):
        """Deactivate selected tasks."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} tasks deactivated.')
    deactivate_tasks.short_description = 'Deactivate selected tasks'
    
    def mark_as_addon(self, request, queryset):
        """Mark selected tasks as add-ons."""
        updated = queryset.update(is_addon=True)
        self.message_user(request, f'{updated} tasks marked as add-ons.')
    mark_as_addon.short_description = 'Mark as add-on services'
    
    def mark_as_main_service(self, request, queryset):
        """Mark selected tasks as main services."""
        updated = queryset.update(is_addon=False)
        self.message_user(request, f'{updated} tasks marked as main services.')
    mark_as_main_service.short_description = 'Mark as main services'
