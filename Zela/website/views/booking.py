from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.contrib.auth.decorators import login_required

from services.models import ServiceCategory, ServiceTask
from workers.models import PropertyTypology, ServicePackage


def booking_flow(request):
    """Main booking flow view with new model support."""
    service_slug = request.GET.get('service', 'indoor-cleaning')
    
    # Service slug mapping for URL convenience
    service_mapping = {
        'indoor': 'indoor-cleaning',
        'outdoor': 'outdoor-cleaning',
        'office': 'office-cleaning',
        'moving': 'moving',
        'express': 'express-cleaning',
        'laundry': 'laundry-ironing',
    }
    
    # Apply mapping if exists, otherwise use as-is
    db_slug = service_mapping.get(service_slug, service_slug)
    
    # Get service category from database
    try:
        service_category = ServiceCategory.objects.get(slug=db_slug, is_active=True)
        service_tasks = service_category.tasks.filter(is_active=True).order_by('order')
        
        # Prepare service data for frontend
        service_data = {
            'id': service_category.id,
            'name': service_category.name,
            'slug': service_category.slug,  # This will be the actual DB slug
            'icon': service_category.icon,
            'description': service_category.description,
            'worker_model_type': service_category.worker_model_type,
            'pricing_model': service_category.pricing_model,
            'booking_requirements': service_category.booking_requirements,
            'tasks': []
        }
        
        for task in service_tasks:
            task_data = {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'base_price': task.price,
                'pricing_model': task.get_pricing_model(),
                'pricing_config': task.pricing_config,
                'duration_hours': float(task.duration_hours),
                'is_addon': task.is_addon,
            }
            service_data['tasks'].append(task_data)
            
    except ServiceCategory.DoesNotExist:
        # Fallback to default service
        service_data = {
            'id': 0,
            'name': 'Limpeza Interna',
            'slug': 'indoor-cleaning',
            'description': 'Limpeza completa e profissional da sua casa',
            'pricing_model': 'fixed',
            'tasks': []
        }
    
    # Get property typologies
    property_typologies = PropertyTypology.objects.all().order_by('name')
    typologies_data = []
    for typology in property_typologies:
        typologies_data.append({
            'name': typology.name,
            'display_name': typology.get_name_display(),
            'description': typology.description,
            'typical_sqm': typology.typical_sqm
        })
    
    # Check for user's packages if authenticated
    user_packages = []
    if request.user.is_authenticated:
        packages = ServicePackage.objects.filter(
            customer=request.user,
            status='active'
        )
        for package in packages:
            if package.is_active:
                user_packages.append({
                    'id': package.id,
                    'name': package.package_name,
                    'type': package.package_type,
                    'remaining_credits': package.remaining_credits,
                    'total_credits': package.total_credits
                })
    
    # Get booking data from session if exists
    booking_data = request.session.get('booking_data', {})
    
    # Update booking data with service info
    booking_data['serviceCategory'] = service_data['id']
    booking_data['serviceCategoryData'] = service_data
    request.session['booking_data'] = booking_data
    
    context = {
        'service_data': json.dumps(service_data),
        'property_typologies': json.dumps(typologies_data),
        'user_packages': json.dumps(user_packages),
        'booking_data': json.dumps(booking_data),
    }
    return render(request, 'website/components/booking-flow.html', context)


def booking_screen(request, screen_number):
    """HTMX endpoint for loading individual booking screens."""
    
    # Handle generic screens with string identifiers
    if isinstance(screen_number, str):
        if screen_number == 'generic-duration':
            template = 'website/components/booking-flow/screens/generic/screen-generic-duration.html'
        elif screen_number == 'generic-units':
            template = 'website/components/booking-flow/screens/generic/screen-generic-units.html'
        elif screen_number == 'generic-selection':
            template = 'website/components/booking-flow/screens/generic/screen-generic-selection.html'
        else:
            # Try to convert to int for numeric screens
            try:
                screen_number = int(screen_number)
            except ValueError:
                return JsonResponse({'error': 'Invalid screen identifier'}, status=404)
    
    # Handle numeric screens
    if isinstance(screen_number, int):
        screen_templates = {
            1: 'website/components/booking-flow/screens/screen-1-address-capture.html',
            2: 'website/components/booking-flow/screens/screen-2-property-typology.html',  # New screen for property selection
            3: 'website/components/booking-flow/screens/screen-3-ac-units.html',  # AC unit configuration
            4: 'website/components/booking-flow/screens/screen-4-electrician-config.html',  # Electrician configuration
            5: 'website/components/booking-flow/screens/screen-5-pest-control-config.html',  # Pest control configuration  
            6: 'website/components/booking-flow/screens/screen-6-dog-trainer-packages.html',  # Dog trainer packages
            7: 'website/components/booking-flow/screens/screen-8-booking-details.html',  # Skip date bucket, go directly to booking details
            8: 'website/components/booking-flow/screens/screen-8-booking-details.html',
            9: 'website/components/booking-flow/screens/screen-9-worker-selection.html',  # Updated worker selection
            10: 'website/components/booking-flow/screens/screen-10-matchmaking.html',  # Worker matchmaking
            11: 'website/components/booking-flow/screens/screen-11-schedule-sessions.html',  # For package-based services
            12: 'website/components/booking-flow/screens/screen-12-cost-review.html',
            13: 'website/components/booking-flow/screens/screen-13-payment-method.html',
            14: 'website/components/booking-flow/screens/screen-14-select-card.html',
            # Legacy screens for backward compatibility
            21: 'website/components/booking-flow/screens/screen-2-map-address.html', 
            22: 'website/components/booking-flow/screens/screen-3-confirm-pin.html',
            23: 'website/components/booking-flow/screens/screen-4-frequency.html',
        }
        
        template = screen_templates.get(screen_number)
    
    if not template:
        return JsonResponse({'error': 'Screen not found'}, status=404)
    
    # Get booking data from session
    booking_data = request.session.get('booking_data', {})
    
    # Get configuration for generic screens if passed
    config = {}
    if request.GET.get('config'):
        try:
            import json
            config = json.loads(request.GET.get('config'))
        except:
            config = {}
    
    # Service info mapping - matches the frontend serviceInfo object
    service_info = {
        'indoor-cleaning': {
            'name': 'Limpeza Interior',
            'description': 'Obtenha 3,5 a 10 horas de limpeza completa e abrangente da sua casa.',
        },
        'outdoor-cleaning': {
            'name': 'Serviços Exteriores',
            'description': 'Limpeza e manutenção exterior profissional incluindo jardinagem, limpeza de piscinas e lavagem exterior.',
        },
        'office-cleaning': {
            'name': 'Limpeza de Escritórios',
            'description': 'Mantenha o seu espaço de trabalho impecável com os nossos serviços abrangentes de limpeza de escritórios.',
        },
        'moving': {
            'name': 'Limpeza de Mudança',
            'description': 'Serviços de limpeza profunda para mudanças de entrada e saída para garantir que o seu espaço esteja impecável.',
        },
        'express-cleaning': {
            'name': 'Limpeza Express',
            'description': 'Serviço de limpeza rápido e eficiente quando precisa com urgência - perfeito para necessidades de última hora.',
        },
        'laundry-ironing': {
            'name': 'Lavandaria e Engomadoria',
            'description': 'Serviços profissionais de lavandaria e engomadoria para manter as suas roupas frescas e sem rugas.',
        },
    }
    
    # Get the service type from booking data
    service_type = booking_data.get('serviceType', 'indoor-cleaning')
    current_service = service_info.get(service_type, service_info['indoor-cleaning'])
    
    # Format the booking data for the template  
    context = {
        'config': json.dumps(config) if config else '{}',
        'service_name': current_service['name'],
        'service_description': current_service['description'],
        'booking': {
            'service_type': booking_data.get('serviceType', 'indoor-cleaning'),
            'location': booking_data.get('location', {
                'unit_name': '',
                'street_address': '',
                'full_address': ''
            }),
            'frequency': booking_data.get('frequency', 'one-time'),
            'date': booking_data.get('date', ''),
            'time_window': booking_data.get('timeWindow', '07:00 - 07:30'),
            'details': booking_data.get('details', {
                'home_size': 'medium-3-4-bedrooms',
                'extra_tasks': [],
                'duration': 5.5,
                'start_time': '07:00',
                'notes': ''
            }),
            'pricing': booking_data.get('pricing', {
                'booking_cost': 710,
                'other_costs': {
                    'booking_cover': 21,
                    'service_fee': 39
                },
                'total': 770
            }),
            'payment': booking_data.get('payment', {
                'method': None,
                'use_sweep_cred': False,
                'card_id': None
            }),
            'selected_worker': booking_data.get('selectedWorker'),
            'tip': booking_data.get('tip', {
                'amount': 0,
                'selected_option': None
            })
        }
    }
    
    # Add worker data for screens that need it
    if screen_number == 12:  # Cost review screen
        # Get selected worker details
        worker_id = booking_data.get('selectedWorker')
        if worker_id:
            # For now, use mock worker data
            context['worker'] = {
                'id': worker_id,
                'name': 'Memory Mudede',  # This would come from DB
                'avatar': None
            }
    
    return render(request, template, context)


@csrf_exempt
@require_http_methods(["POST"])
def save_booking_data(request):
    """HTMX endpoint for saving booking data to session."""
    try:
        data = json.loads(request.body)
        
        # Initialize booking data in session if not exists
        if 'booking_data' not in request.session:
            request.session['booking_data'] = {}
        
        # Update session with new data
        request.session['booking_data'].update(data)
        request.session.modified = True
        
        return JsonResponse({'status': 'success', 'data': request.session['booking_data']})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_http_methods(["GET"])
def get_booking_data(request):
    """Get booking data from session."""
    booking_data = request.session.get('booking_data', {})
    return JsonResponse({'status': 'success', 'data': booking_data})


@csrf_exempt  
@require_http_methods(["POST"])
@login_required
def process_payment(request):
    """Process payment and create booking."""
    try:
        from bookings.models import Booking
        from services.models import ServiceTask, ServiceCategory
        from accounts.models import User
        from datetime import datetime, timedelta
        
        # Get booking data from session
        booking_data = request.session.get('booking_data', {})
        if not booking_data:
            return JsonResponse({'status': 'error', 'message': 'No booking data found'}, status=400)
        
        # Parse booking details
        details = booking_data.get('details', {})
        location = booking_data.get('location', {})
        frequency = booking_data.get('frequency', 'one-time')
        date_str = booking_data.get('date')
        time_window = booking_data.get('timeWindow', '07:00 - 07:30')
        start_time = details.get('startTime', '07:00')
        duration = details.get('duration', 3.5)
        
        # Convert date and time to datetime objects
        if not date_str:
            # Default to tomorrow if no date
            booking_date = datetime.now().date() + timedelta(days=1)
        else:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
        # Parse start time from either startTime or timeWindow
        if ':' in start_time and len(start_time.split(':')) == 2:
            start_hour = int(start_time.split(':')[0])
            start_minute = int(start_time.split(':')[1])
        else:
            # Parse from time window (e.g., "07:00 - 07:30")
            start_time_part = time_window.split(' - ')[0]
            start_hour = int(start_time_part.split(':')[0])
            start_minute = int(start_time_part.split(':')[1])
        
        start_datetime = datetime.combine(booking_date, datetime.min.time())
        start_datetime = start_datetime.replace(hour=start_hour, minute=start_minute)
        end_datetime = start_datetime + timedelta(hours=float(duration))
        
        # Get or create service based on service type
        service_type = booking_data.get('serviceType', 'indoor-cleaning')
        service_name_map = {
            'indoor-cleaning': 'Indoor Cleaning',
            'outdoor-cleaning': 'Outdoor Cleaning',
            'office-cleaning': 'Office Cleaning',
            'moving': 'Moving Cleaning',
            'express-cleaning': 'Express Cleaning',
            'laundry-ironing': 'Laundry & Ironing'
        }
        
        service_name = service_name_map.get(service_type, 'Indoor Cleaning')
        
        # Get main service task
        service_task = ServiceTask.objects.filter(name__icontains=service_name.split()[0]).first()
        if not service_task:
            # Create a default category and task if none exists
            category = ServiceCategory.objects.filter(name__icontains=service_name.split()[0]).first()
            if not category:
                category = ServiceCategory.objects.create(
                    name=service_name,
                    slug=service_type,
                    description=f'{service_name} service',
                    icon='home',  # Default icon
                    is_active=True
                )
            
            service_task = ServiceTask.objects.create(
                category=category,
                name=service_name,
                description=f'Comprehensive {service_name.lower()} service',
                price=129 * 5,  # Base price for average duration
                duration_hours=5.5  # Default duration
            )
        
        # Get selected worker if any
        worker = None
        worker_id = booking_data.get('selectedWorker')
        if worker_id:
            try:
                from workers.models import Worker
                # Worker ID might be a string like "memory-mudede" or an actual ID
                if isinstance(worker_id, str) and not worker_id.isdigit():
                    # It's a mock worker name, skip for now
                    worker = None
                else:
                    # Get the Worker object (not User object)
                    user = User.objects.get(id=int(worker_id), role='provider', is_active=True)
                    worker = Worker.objects.filter(user=user).first()
            except (User.DoesNotExist, ValueError):
                # Worker not found, will be assigned later
                pass
        
        # Calculate total price including tip
        pricing = booking_data.get('pricing', {})
        tip = booking_data.get('tip', {})
        base_total = pricing.get('total', 770)
        tip_amount = tip.get('amount', 0)
        total_price = base_total + tip_amount
        
        # Build full address
        full_address = location.get('streetAddress', '')
        if location.get('unitName'):
            full_address = f"{location['unitName']}, {full_address}"
        
        # Create the booking
        booking = Booking.objects.create(
            customer=request.user,
            worker=worker,  # May be None if not selected
            service_task=service_task,
            start_at=start_datetime,
            end_at=end_datetime,
            address=full_address,
            notes=details.get('notes', ''),
            total_price=total_price,
            status='pending_confirmation'  # As requested
        )
        
        # Store additional booking metadata
        booking_metadata = {
            'frequency': frequency,
            'home_size': details.get('homeSize', 'medium-3-4-bedrooms'),
            'extra_tasks': details.get('extraTasks', []),
            'time_window': time_window,
            'tip_amount': tip_amount,
            'location_coordinates': location.get('coordinates'),
            'payment_method': booking_data.get('payment', {}).get('method', 'credit-card')
        }
        
        # You might want to store this metadata in a separate model or as JSON field
        # For now, we'll include some key info in the notes
        if not booking.notes:
            booking.notes = f"Home size: {booking_metadata['home_size']}"
        if booking_metadata['extra_tasks']:
            booking.notes += f"\nExtra tasks: {', '.join(booking_metadata['extra_tasks'])}"
        if tip_amount > 0:
            booking.notes += f"\nTip included: R{tip_amount}"
        booking.save()
        
        # Clear booking data from session
        request.session.pop('booking_data', None)
        request.session.modified = True
        
        return JsonResponse({
            'status': 'success',
            'booking_id': booking.id,
            'message': 'Booking created successfully'
        })
        
    except Exception as e:
        import traceback
        print(f"Error creating booking: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_http_methods(["GET"])
def get_available_workers(request):
    """Get available workers for booking."""
    try:
        from accounts.models import User, ProviderProfile, Profile
        
        # Get all approved providers with profile
        workers = User.objects.filter(
            role='provider',
            is_active=True,
            provider__is_approved=True,
            provider__is_available=True
        ).select_related('provider', 'profile')
        
        # Build worker data
        workers_data = []
        for worker in workers[:10]:  # Limit to 10 workers for now
            provider_profile = worker.provider
            
            # Calculate recommendation rate from rating
            if provider_profile.rating_count > 0:
                # Convert 0-5 rating to percentage (e.g., 4.8 -> 96%)
                recommend_rate = int(provider_profile.rating_average * 20)
            else:
                recommend_rate = 95  # Default for new providers
            
            # Get avatar URL from profile if it exists
            avatar_url = None
            try:
                if hasattr(worker, 'profile') and worker.profile.profile_picture:
                    avatar_url = worker.profile.profile_picture.url
            except:
                pass
            
            workers_data.append({
                'id': worker.id,
                'name': worker.get_full_name() or worker.username,
                'avatar': avatar_url,
                'recommend_rate': recommend_rate,
                'jobs_completed': provider_profile.jobs_completed,
                'rating': float(provider_profile.rating_average),
                'rating_count': provider_profile.rating_count,
                'bio': provider_profile.bio,
                'skills': provider_profile.skills,
                'service_area': provider_profile.service_area,
                'accepts_same_day': provider_profile.accepts_same_day,
            })
        
        return JsonResponse({'status': 'success', 'workers': workers_data})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def get_user_addresses(request):
    """Get user's saved addresses from address book."""
    try:
        from accounts.models import Location
        
        # Get user's saved locations
        locations = request.user.locations.all().order_by('-is_main', '-created_at')
        
        # Build location data
        locations_data = []
        for location in locations:
            # Build full address if not set
            full_address = location.full_address
            if not full_address:
                parts = []
                if location.address_line_1:
                    parts.append(location.address_line_1)
                if location.address_line_2:
                    parts.append(location.address_line_2)
                if location.city:
                    parts.append(location.city)
                if location.province:
                    parts.append(location.province)
                if location.country:
                    parts.append(location.country)
                full_address = ', '.join(parts) if parts else location.name or 'Principal'
            
            locations_data.append({
                'id': location.id,
                'name': location.name,
                'address_line_1': location.address_line_1,
                'address_line_2': location.address_line_2,
                'city': location.city,
                'province': location.province,
                'postal_code': location.postal_code,
                'country': location.country,
                'is_main': location.is_main,
                'latitude': float(location.latitude) if location.latitude else None,
                'longitude': float(location.longitude) if location.longitude else None,
                'full_address': full_address,
            })
        
        return JsonResponse({'status': 'success', 'addresses': locations_data})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)