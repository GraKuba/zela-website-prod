from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('validate-password/', views.validate_password_strength, name='validate-password'),
    path('logout/', views.ZelaLogoutView.as_view(), name='logout'),
    
    # Location management
    path('locations/', views.location_list, name='location-list'),
    path('locations/create/', views.location_create, name='location-create'),
    path('locations/<int:location_id>/edit/', views.location_edit, name='location-edit'),
    path('locations/<int:location_id>/delete/', views.location_delete, name='location-delete'),
    path('locations/<int:location_id>/set-main/', views.location_set_main, name='location-set-main'),
]