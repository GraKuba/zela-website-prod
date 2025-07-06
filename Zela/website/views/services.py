from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.template.loader import render_to_string
from services.models import ServiceCategory, ServiceTask
from pricing.models import PricingConfig
from typing import Dict, Any


class ServiceCatalogueView(ListView):
    """Service catalogue listing all service categories."""
    
    model = ServiceCategory
    template_name = 'website/components/page-services/services.html'
    context_object_name = 'service_categories'
    
    def get_queryset(self):
        """Return active service categories ordered by priority."""
        return ServiceCategory.objects.filter(
            is_active=True
        ).prefetch_related('tasks').order_by('order', 'name')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for the services page."""
        context = super().get_context_data(**kwargs)
        
        # Get pricing configuration
        pricing = PricingConfig.get_instance()
        
        context.update({
            'title': 'Zela Services - Choose the Perfect Service',
            'meta_description': 'Browse our comprehensive range of home services in Angola. From cleaning to repairs, find the right service for your needs.',
            'pricing': pricing,
            'total_categories': self.get_queryset().count(),
        })
        
        return context


class ServiceDetailPartial(DetailView):
    """Service detail modal view (HTMX only)."""
    
    model = ServiceCategory
    template_name = 'website/fragments/service-detail-modal.html'
    context_object_name = 'service_category'
    
    def get_object(self):
        """Get service category by slug."""
        return get_object_or_404(
            ServiceCategory,
            slug=self.kwargs['slug'],
            is_active=True
        )
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for the service detail modal."""
        context = super().get_context_data(**kwargs)
        
        service_category = self.get_object()
        
        # Get all tasks for this category
        tasks = service_category.tasks.filter(is_active=True).order_by('order', 'name')
        
        # Separate main services from add-ons
        main_tasks = tasks.filter(is_addon=False)
        addon_tasks = tasks.filter(is_addon=True)
        
        # Get pricing configuration
        pricing = PricingConfig.get_instance()
        
        context.update({
            'main_tasks': main_tasks,
            'addon_tasks': addon_tasks,
            'pricing': pricing,
            'total_tasks': tasks.count(),
        })
        
        return context
    
    def get(self, request, *args, **kwargs):
        """Handle GET request for service detail modal."""
        # Only allow HTMX requests
        if not request.htmx:
            # Redirect to services page if not HTMX
            from django.shortcuts import redirect
            return redirect('services')
        
        return super().get(request, *args, **kwargs)


class ServiceTaskDetailPartial(DetailView):
    """Individual service task detail view (HTMX only)."""
    
    model = ServiceTask
    template_name = 'website/fragments/service-task-detail.html'
    context_object_name = 'service_task'
    
    def get_object(self):
        """Get service task by ID."""
        return get_object_or_404(
            ServiceTask,
            pk=self.kwargs['pk'],
            is_active=True
        )
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for the service task detail."""
        context = super().get_context_data(**kwargs)
        
        service_task = self.get_object()
        
        # Get related add-ons
        related_addons = ServiceTask.objects.filter(
            category=service_task.category,
            is_addon=True,
            is_active=True
        ).order_by('order', 'name')
        
        # Get pricing configuration
        pricing = PricingConfig.get_instance()
        
        context.update({
            'related_addons': related_addons,
            'pricing': pricing,
        })
        
        return context
    
    def get(self, request, *args, **kwargs):
        """Handle GET request for service task detail."""
        # Only allow HTMX requests
        if not request.htmx:
            from django.shortcuts import redirect
            return redirect('services')
        
        return super().get(request, *args, **kwargs)


class ServiceListView(ListView):
    """Complete service catalogue listing all services."""
    
    model = ServiceCategory
    template_name = 'website/components/page-services-list/page-services-list.html'
    context_object_name = 'service_categories'
    
    def get_queryset(self):
        """Return active service categories ordered by priority."""
        return ServiceCategory.objects.filter(
            is_active=True
        ).prefetch_related('tasks').order_by('order', 'name')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for the services list page."""
        context = super().get_context_data(**kwargs)
        
        # Get pricing configuration
        pricing = PricingConfig.get_instance()
        
        context.update({
            'title': 'Zela Services - Complete Service Catalogue',
            'meta_description': 'Browse our complete catalogue of home services in Angola. From on-demand cleaning to full-time placements, discover all the ways Zela can support your lifestyle.',
            'pricing': pricing,
            'total_categories': self.get_queryset().count(),
        })
        
        return context