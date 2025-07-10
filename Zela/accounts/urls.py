from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('validate-password/', views.validate_password_strength, name='validate-password'),
    path('logout/', views.ZelaLogoutView.as_view(), name='logout'),
]