from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q
from decimal import Decimal
import json

from services.models import ServiceCategory, ServiceTask, PricingModel
from workers.models import (
    PropertyTypology, Worker, ServicePackage,
    ElectricianWorker, ACTechnicianWorker, PestControlWorker,
    DogTrainerWorker, CleaningWorker, HandymanWorker,
    GardenerWorker, PlacementWorker
)
from bookings.models import Booking


@require_http_methods(["GET"])
def get_services(request):
    """Get all active service categories with their tasks and pricing."""
    categories = ServiceCategory.objects.filter(is_active=True).order_by('order')
    
    services_data = []
    for category in categories:
        tasks = category.tasks.filter(is_active=True).order_by('order')
        
        tasks_data = []
        for task in tasks:
            task_data = {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'base_price': task.price,
                'pricing_model': task.get_pricing_model(),
                'pricing_config': task.pricing_config,
                'duration_hours': float(task.duration_hours),
                'is_addon': task.is_addon,
                'skill_requirements': task.skill_requirements,
                'equipment_requirements': task.equipment_requirements,
            }
            tasks_data.append(task_data)
        
        category_data = {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'icon': category.icon,
            'description': category.description,
            'worker_model_type': category.worker_model_type,
            'pricing_model': category.pricing_model,
            'booking_requirements': category.booking_requirements,
            'tasks': tasks_data
        }
        services_data.append(category_data)
    
    return JsonResponse({'services': services_data})


@require_http_methods(["GET"])
def get_property_typologies(request):
    """Get all property typology options."""
    typologies = PropertyTypology.objects.all().order_by('name')
    
    data = []
    for typology in typologies:
        data.append({
            'id': typology.id,
            'name': typology.name,
            'display_name': typology.get_name_display(),
            'description': typology.description,
            'typical_sqm': typology.typical_sqm
        })
    
    return JsonResponse({'typologies': data})


@require_http_methods(["POST"])
@csrf_exempt
def calculate_price(request):
    """Calculate price based on service configuration."""
    data = json.loads(request.body)
    
    service_task_id = data.get('service_task_id')
    property_typology = data.get('property_typology')
    unit_count = data.get('unit_count')
    hours = data.get('hours')
    package_id = data.get('package_id')
    
    task = get_object_or_404(ServiceTask, id=service_task_id)
    pricing_model = task.get_pricing_model()
    pricing_config = task.pricing_config or {}
    
    # Calculate base price
    price = Decimal(str(task.price))
    
    # Apply pricing model logic
    if pricing_model == PricingModel.TYPOLOGY_BASED:
        if property_typology and property_typology in pricing_config:
            price = Decimal(str(pricing_config[property_typology]))
    
    elif pricing_model == PricingModel.HOURLY_MINIMUM:
        min_hours = pricing_config.get('minimum_hours', 2)
        actual_hours = max(hours or min_hours, min_hours)
        
        if property_typology and 'typology_rates' in pricing_config:
            hourly_rate = pricing_config['typology_rates'].get(property_typology, task.price)
        else:
            hourly_rate = task.price
        
        price = Decimal(str(hourly_rate)) * Decimal(str(actual_hours))
        
        # Return both prepaid and potential additional
        return JsonResponse({
            'prepaid_amount': float(Decimal(str(hourly_rate)) * Decimal(str(min_hours))),
            'estimated_total': float(price),
            'hourly_rate': float(hourly_rate),
            'minimum_hours': min_hours,
            'actual_hours': actual_hours
        })
    
    elif pricing_model == PricingModel.PER_UNIT:
        if unit_count:
            base_price = Decimal(str(pricing_config.get('base_price', task.price)))
            
            # Apply volume discounts
            discounts = pricing_config.get('volume_discounts', {})
            discount_rate = 0
            
            if unit_count == 1:
                discount_rate = discounts.get('1', 0)
            elif 2 <= unit_count <= 3:
                discount_rate = discounts.get('2-3', 0)
            elif 4 <= unit_count <= 5:
                discount_rate = discounts.get('4-5', 0)
            elif unit_count >= 6:
                discount_rate = discounts.get('6+', 0)
            
            unit_price = base_price * (1 - Decimal(str(discount_rate)) / 100)
            price = unit_price * unit_count
    
    elif pricing_model == PricingModel.PACKAGE:
        # Check if using existing package
        if package_id and request.user.is_authenticated:
            package = ServicePackage.objects.filter(
                id=package_id,
                customer=request.user,
                status='active'
            ).first()
            
            if package and package.remaining_credits > 0:
                return JsonResponse({
                    'uses_package': True,
                    'package_id': package.id,
                    'credits_to_use': 1,
                    'remaining_credits': package.remaining_credits - 1,
                    'price': 0  # No additional payment needed
                })
        
        # Return package options if not using existing
        packages = pricing_config.get('packages', [])
        return JsonResponse({
            'package_options': packages,
            'requires_package_selection': True
        })
    
    # Add service fees
    service_fee = price * Decimal('0.05')  # 5% service fee
    booking_cover = Decimal('21.00')  # Fixed booking cover
    
    total = price + service_fee + booking_cover
    
    return JsonResponse({
        'base_price': float(price),
        'service_fee': float(service_fee),
        'booking_cover': float(booking_cover),
        'total': float(total)
    })


@require_http_methods(["GET"])
def get_available_workers(request):
    """Get available workers for a service category."""
    category_id = request.GET.get('category_id')
    date = request.GET.get('date')
    time = request.GET.get('time')
    
    category = get_object_or_404(ServiceCategory, id=category_id)
    
    # Get the appropriate worker model
    worker_model_map = {
        'CleaningWorker': CleaningWorker,
        'ElectricianWorker': ElectricianWorker,
        'ACTechnicianWorker': ACTechnicianWorker,
        'PestControlWorker': PestControlWorker,
        'DogTrainerWorker': DogTrainerWorker,
        'HandymanWorker': HandymanWorker,
        'GardenerWorker': GardenerWorker,
        'PlacementWorker': PlacementWorker,
    }
    
    WorkerModel = worker_model_map.get(category.worker_model_type, Worker)
    
    # Get available workers
    workers = WorkerModel.objects.filter(
        status='approved',
        is_available=True
    )
    
    # TODO: Filter by date/time availability
    # This would check working_hours and existing bookings
    
    workers_data = []
    for worker in workers:
        worker_data = {
            'id': worker.id,
            'name': worker.user.get_full_name() or worker.user.username,
            'bio': worker.bio,
            'rating': float(worker.rating_average),
            'rating_count': worker.rating_count,
            'jobs_completed': worker.jobs_completed,
            'years_experience': worker.years_experience,
            'languages': worker.languages,
            'accepts_emergency': worker.accepts_emergency,
            'profile_picture': worker.user.profile.profile_picture.url if hasattr(worker.user, 'profile') and worker.user.profile.profile_picture else None
        }
        
        # Add service-specific fields
        if isinstance(worker, ElectricianWorker):
            worker_data['minimum_hours'] = worker.minimum_hours
            worker_data['typology_rates'] = worker.typology_rates
            worker_data['specializations'] = worker.specializations
        elif isinstance(worker, ACTechnicianWorker):
            worker_data['brands_serviced'] = worker.brands_serviced
            worker_data['unit_pricing'] = worker.unit_pricing
        elif isinstance(worker, PestControlWorker):
            worker_data['service_types'] = worker.get_service_types_display()
            worker_data['eco_friendly'] = worker.eco_friendly_options
        elif isinstance(worker, DogTrainerWorker):
            worker_data['training_methods'] = worker.get_training_methods_display()
            worker_data['package_offerings'] = worker.package_offerings
        
        workers_data.append(worker_data)
    
    # Sort by rating and availability
    workers_data.sort(key=lambda x: (x['rating'], x['jobs_completed']), reverse=True)
    
    return JsonResponse({'workers': workers_data})


@require_http_methods(["GET"])
@login_required
def get_user_packages(request):
    """Get user's active service packages."""
    service_type = request.GET.get('service_type')
    
    packages = ServicePackage.objects.filter(
        customer=request.user,
        status='active'
    )
    
    if service_type:
        # Filter by service type (e.g., dog training)
        packages = packages.filter(package_type__contains=service_type)
    
    packages_data = []
    for package in packages:
        if package.is_active:
            packages_data.append({
                'id': package.id,
                'name': package.package_name,
                'type': package.package_type,
                'total_credits': package.total_credits,
                'remaining_credits': package.remaining_credits,
                'expiry_date': package.expiry_date.isoformat() if package.expiry_date else None,
                'worker': {
                    'id': package.worker.id,
                    'name': package.worker.user.get_full_name()
                } if package.worker else None
            })
    
    return JsonResponse({'packages': packages_data})


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def validate_booking(request):
    """Validate booking data before final submission."""
    data = json.loads(request.body)
    
    errors = []
    warnings = []
    
    # Validate required fields
    required_fields = ['service_task_id', 'address', 'date', 'time']
    for field in required_fields:
        if not data.get(field):
            errors.append(f'{field} is required')
    
    # Validate service-specific requirements
    if data.get('service_task_id'):
        task = ServiceTask.objects.get(id=data['service_task_id'])
        pricing_model = task.get_pricing_model()
        
        if pricing_model == PricingModel.TYPOLOGY_BASED:
            if not data.get('property_typology'):
                errors.append('Property type is required for this service')
        
        elif pricing_model == PricingModel.PER_UNIT:
            if not data.get('unit_count'):
                errors.append('Number of units is required for this service')
        
        elif pricing_model == PricingModel.HOURLY_MINIMUM:
            config = task.pricing_config or {}
            min_hours = config.get('minimum_hours', 2)
            if data.get('hours', 0) < min_hours:
                warnings.append(f'Minimum {min_hours} hours required for this service')
    
    # Validate worker availability
    if data.get('worker_id'):
        worker = Worker.objects.get(id=data['worker_id'])
        if not worker.is_active:
            errors.append('Selected worker is not available')
        
        # Check for conflicts
        existing_bookings = Booking.objects.filter(
            worker=worker,
            start_at__date=data['date'],
            status__in=['accepted', 'in_progress']
        )
        if existing_bookings.exists():
            warnings.append('Worker may have limited availability on selected date')
    
    # Validate package usage
    if data.get('package_id'):
        package = ServicePackage.objects.get(id=data['package_id'])
        if not package.is_active:
            errors.append('Selected package is not active')
        if package.remaining_credits <= 0:
            errors.append('No credits remaining in selected package')
    
    return JsonResponse({
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    })