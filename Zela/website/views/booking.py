from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def booking_flow(request):
    """Main booking flow view."""
    service_type = request.GET.get('service', 'indoor-cleaning')
    context = {
        'service_type': service_type,
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
    """HTMX endpoint for saving booking data (mock implementation)."""
    # In a real app, this would save to database/session
    # For now, just return success
    return JsonResponse({'status': 'success'})


@csrf_exempt  
@require_http_methods(["POST"])
def process_payment(request):
    """Mock payment processing endpoint."""
    # In a real app, this would integrate with payment providers
    return JsonResponse({
        'status': 'success',
        'booking_id': 'BK123456',
        'message': 'Payment processed successfully'
    }) 