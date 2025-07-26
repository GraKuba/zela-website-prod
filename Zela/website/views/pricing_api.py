from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from pricing.models import PricingConfig
from accounts.models import ProviderProfile
import json


@csrf_exempt
@require_http_methods(["POST"])
def calculate_booking_price(request):
    """
    Calculate booking price based on service details and location.
    
    Expected POST data:
    {
        "service_type": "indoor-cleaning",
        "duration": 3.5,
        "home_size": "medium-3-4-bedrooms",
        "extra_tasks": ["inside-fridge", "inside-oven"],
        "location": {
            "area": "Luanda Centro",
            "latitude": -8.8147,
            "longitude": 13.2302
        },
        "date": "2024-01-15",
        "time": "07:00"
    }
    """
    try:
        data = json.loads(request.body)
        
        # Get pricing configuration
        pricing_config = PricingConfig.get_instance()
        
        # Extract request data
        duration = float(data.get('duration', 3.5))
        home_size = data.get('home_size', 'medium-3-4-bedrooms')
        extra_tasks = data.get('extra_tasks', [])
        location = data.get('location', {})
        area_name = location.get('area', 'Luanda Centro')
        
        # Base hourly rate from config
        base_hourly_rate = pricing_config.hourly_clean_base
        
        # Calculate base cost
        base_cost = base_hourly_rate * duration
        
        # Apply home size multiplier
        size_multipliers = {
            'small-1-2-bedrooms': 0.8,
            'medium-3-4-bedrooms': 1.0,
            'large-5-plus-bedrooms': 1.3
        }
        size_multiplier = size_multipliers.get(home_size, 1.0)
        base_cost *= size_multiplier
        
        # Add extra tasks cost
        extra_task_cost = len(extra_tasks) * pricing_config.specialty_task_price
        
        # Get location surcharge from default service areas
        location_surcharge = 0
        default_areas = ProviderProfile().get_default_service_areas()
        
        for area in default_areas:
            if area['name'].lower() == area_name.lower():
                location_surcharge = area['surcharge'] * 100  # Convert to AOA (surcharge is in units)
                break
        
        # Calculate subtotal
        subtotal = base_cost + extra_task_cost + location_surcharge
        
        # Add booking fee
        booking_fee = pricing_config.booking_fee
        
        # Check for weekend/holiday multiplier (simplified for now)
        # In production, you'd check actual date against holidays
        import datetime
        if data.get('date'):
            try:
                booking_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d')
                if booking_date.weekday() >= 5:  # Saturday or Sunday
                    subtotal *= float(pricing_config.weekend_multiplier)
            except:
                pass
        
        # Calculate total
        total = subtotal + booking_fee
        
        # Ensure minimum booking amount
        if total < pricing_config.minimum_booking_amount:
            total = pricing_config.minimum_booking_amount
        
        # Prepare response
        response = {
            'status': 'success',
            'pricing': {
                'base_cost': round(base_cost),
                'extra_tasks_cost': round(extra_task_cost),
                'location_surcharge': round(location_surcharge),
                'booking_fee': round(booking_fee),
                'subtotal': round(subtotal),
                'total': round(total),
                'breakdown': {
                    'hourly_rate': base_hourly_rate,
                    'duration': duration,
                    'home_size_multiplier': size_multiplier,
                    'area': area_name,
                    'area_surcharge': location_surcharge
                }
            },
            'currency': 'AOA'
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@require_http_methods(["GET"])
def get_pricing_config(request):
    """Get current pricing configuration for the frontend."""
    try:
        pricing_config = PricingConfig.get_instance()
        
        # Get default service areas with surcharges
        default_areas = ProviderProfile().get_default_service_areas()
        
        response = {
            'status': 'success',
            'config': {
                'hourly_rate': pricing_config.hourly_clean_base,
                'specialty_task_price': pricing_config.specialty_task_price,
                'booking_fee': pricing_config.booking_fee,
                'minimum_booking': pricing_config.minimum_booking_amount,
                'weekend_multiplier': float(pricing_config.weekend_multiplier),
                'holiday_multiplier': float(pricing_config.holiday_multiplier),
                'service_areas': default_areas,
                'currency': 'AOA'
            }
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)