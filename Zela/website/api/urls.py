from django.urls import path
from . import views
from . import booking_config

app_name = 'website_api'

urlpatterns = [
    # Service endpoints
    path('services/', views.get_services, name='get_services'),
    path('property-typologies/', views.get_property_typologies, name='get_property_typologies'),
    path('calculate-price/', views.calculate_price, name='calculate_price'),
    
    # Worker endpoints
    path('workers/available/', views.get_available_workers, name='get_available_workers'),
    
    # Package endpoints
    path('packages/user/', views.get_user_packages, name='get_user_packages'),
    
    # Booking validation
    path('booking/validate/', views.validate_booking, name='validate_booking'),
    
    # Booking flow configuration
    path('booking/service-config/', booking_config.get_service_config, name='get_service_config'),
]