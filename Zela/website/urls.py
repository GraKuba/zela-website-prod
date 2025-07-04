from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('pricing/', views.pricing, name='pricing'),
    path('services/', views.services, name='services'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),
    path('accessibility-statement/', views.accessibility_statement, name='accessibility_statement'),
    path('refund-policy/', views.refund_policy, name='refund_policy'),
]
