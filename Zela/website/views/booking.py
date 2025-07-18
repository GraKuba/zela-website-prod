from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.contrib.auth.decorators import login_required


def booking_flow(request):
    """Main booking flow view."""
    service_type = request.GET.get('service', 'indoor-cleaning')
    
    # Get booking data from session if exists
    booking_data = request.session.get('booking_data', {})
    
    context = {
        'service_type': service_type,
        'booking_data': json.dumps(booking_data),  # Pass as JSON for JavaScript
    }
    return render(request, 'website/components/booking-flow.html', context)


def booking_screen(request, screen_number):
    """HTMX endpoint for loading individual booking screens."""
    
    screen_templates = {
        1: 'website/components/booking-flow/screens/screen-1-address-capture.html',
        2: 'website/components/booking-flow/screens/screen-2-map-address.html', 
        3: 'website/components/booking-flow/screens/screen-3-confirm-pin.html',
        4: 'website/components/booking-flow/screens/screen-4-frequency.html',
        7: 'website/components/booking-flow/screens/screen-7-date-bucket.html',
        8: 'website/components/booking-flow/screens/screen-8-booking-details.html',
        12: 'website/components/booking-flow/screens/screen-12-cost-review.html',
        13: 'website/components/booking-flow/screens/screen-13-payment-method.html',
        14: 'website/components/booking-flow/screens/screen-14-select-card.html',
    }
    
    template = screen_templates.get(screen_number)
    if not template:
        return JsonResponse({'error': 'Screen not found'}, status=404)
    
    # Mock booking data that would normally come from session/database
    context = {
        'booking': {
            'service_type': 'indoor-cleaning',
            'location': {
                'unit_name': 'V&A Waterfront',
                'street_address': '98 Main Road, Mowbray, Cape Town, South Africa',
                'full_address': '98 Main Road, Mowbray, Cape Town, South Africa'
            },
            'frequency': 'one-time',
            'date': '2025-07-06',
            'time_window': '07:00 - 07:30',
            'details': {
                'home_size': 'medium-3-4-bedrooms',
                'extra_tasks': [],
                'duration': 5.5,
                'start_time': '07:00',
                'notes': ''
            },
            'pricing': {
                'booking_cost': 710,
                'other_costs': {
                    'booking_cover': 21,
                    'service_fee': 39
                },
                'total': 770
            },
            'payment': {
                'method': None,
                'use_sweep_cred': False,
                'card_id': None
            }
        }
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
        from services.models import ServiceTask
        from datetime import datetime, timedelta
        
        # Get booking data from session
        booking_data = request.session.get('booking_data', {})
        if not booking_data:
            return JsonResponse({'status': 'error', 'message': 'No booking data found'}, status=400)
        
        # Parse booking details
        details = booking_data.get('details', {})
        frequency = booking_data.get('frequency', 'one-time')
        date_str = booking_data.get('date')
        start_time = details.get('startTime', '07:00')
        duration = details.get('duration', 3.5)
        
        # Convert date and time to datetime objects
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_hour = int(start_time.split(':')[0])
        start_minute = int(start_time.split(':')[1])
        
        start_datetime = datetime.combine(booking_date, datetime.min.time())
        start_datetime = start_datetime.replace(hour=start_hour, minute=start_minute)
        end_datetime = start_datetime + timedelta(hours=float(duration))
        
        # Get main service task (Indoor Cleaning)
        # In a real app, this would be dynamic based on service type
        service_task = ServiceTask.objects.filter(name__icontains='cleaning').first()
        if not service_task:
            # Create a default service task if none exists
            from services.models import Service
            service = Service.objects.first()
            if not service:
                return JsonResponse({'status': 'error', 'message': 'No services configured'}, status=400)
            service_task = ServiceTask.objects.create(
                service=service,
                name='Indoor Cleaning',
                description='Comprehensive indoor cleaning service',
                base_price=710
            )
        
        # Create the booking
        booking = Booking.objects.create(
            customer=request.user,
            service_task=service_task,
            start_at=start_datetime,
            end_at=end_datetime,
            address=booking_data.get('location', {}).get('streetAddress', ''),
            notes=details.get('notes', ''),
            total_price=booking_data.get('pricing', {}).get('total', 770),
            status='pending'
        )
        
        # Add extra tasks if any
        extra_tasks = details.get('extraTasks', [])
        if extra_tasks:
            # In a real app, map extra task IDs to ServiceTask objects
            pass
        
        # Clear booking data from session
        request.session.pop('booking_data', None)
        request.session.modified = True
        
        return JsonResponse({
            'status': 'success',
            'booking_id': booking.id,
            'message': 'Booking created successfully'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_http_methods(["GET"])
def get_available_workers(request):
    """Get available workers for booking."""
    try:
        from accounts.models import User
        
        # Get all approved providers
        workers = User.objects.filter(
            role='provider',
            is_active=True,
            provider_profile__is_approved=True
        ).select_related('provider_profile')
        
        # Build worker data
        workers_data = []
        for worker in workers[:10]:  # Limit to 10 workers for now
            # Calculate mock statistics
            jobs_completed = 200 + (worker.id * 23) % 300  # Mock data
            recommend_rate = 95 + (worker.id % 5)  # 95-99%
            
            workers_data.append({
                'id': worker.id,
                'name': worker.get_full_name() or f"Worker {worker.id}",
                'avatar': None,  # Would use worker.provider_profile.avatar.url if we had avatars
                'recommend_rate': recommend_rate,
                'jobs_completed': jobs_completed,
                'experience_years': 2 + (worker.id % 3),  # 2-4 years
            })
        
        # If no real workers, return mock data
        if not workers_data:
            workers_data = [
                {
                    'id': 1,
                    'name': 'Memory Mudede',
                    'avatar': None,
                    'recommend_rate': 98,
                    'jobs_completed': 423,
                    'experience_years': 3,
                },
                {
                    'id': 2,
                    'name': 'Annah Havo',
                    'avatar': None,
                    'recommend_rate': 99,
                    'jobs_completed': 200,
                    'experience_years': 2,
                },
                {
                    'id': 3,
                    'name': 'Epiphaniah Matarirano',
                    'avatar': None,
                    'recommend_rate': 97,
                    'jobs_completed': 367,
                    'experience_years': 4,
                },
            ]
        
        return JsonResponse({'status': 'success', 'workers': workers_data})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400) 