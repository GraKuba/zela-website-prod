from django.urls import path, include
from . import views
from .views.public import HomeView, ContactFormView
from .views.services import ServiceCatalogueView, ServiceDetailPartial, ServiceTaskDetailPartial, ServiceListView, ServicesPreviewView
from .views.blog import BlogIndexView, BlogPostView
from .views.help_center import HelpCenterView, HelpCenterSearch, HelpArticleView
from .views.auth import RegisterWizardView, SignInView, SignOutView
from .views.dashboard import (
    DashboardShellView, BookingListPartial, BookingUpdatePartial,
    ProfileUpdateView, RatingCreatePartial, AddPaymentMethodView,
    set_default_payment_method, update_provider_availability,
    update_provider_schedule, update_service_areas, upload_document,
    update_profile, ProviderRatingsPartial, update_settings,
    booking_details_modal, mark_notification_read, mark_all_notifications_read
)
from .views.providers import ProviderLandingView, ProviderApplicationWizard, ApplyWorkerView
from .views.booking import booking_flow, booking_screen, save_booking_data, get_booking_data, process_payment, get_available_workers, get_user_addresses
from .views.pricing_api import calculate_booking_price, get_pricing_config
from .views.api import get_payment_methods

app_name = 'website'

urlpatterns = [
    # Marketing / Public pages
    path('', HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('services/', ServiceCatalogueView.as_view(), name='services'),
    path('services-list/', ServiceListView.as_view(), name='services-list'),
    path('services-preview/', ServicesPreviewView.as_view(), name='services-preview'),
    path('service-detail/<slug:slug>/', ServiceDetailPartial.as_view(), name='service-detail'),
    path('service-task/<int:pk>/', ServiceTaskDetailPartial.as_view(), name='service-task-detail'),
    path('pricing/', views.PricingView.as_view(), name='pricing'),
    
    # Blog
    path('blog/', BlogIndexView.as_view(), name='blog'),
    path('blog-post/<slug:slug>/', BlogPostView.as_view(), name='blog-post'),
    
    # Contact
    path('contact/', ContactFormView.as_view(), name='contact'),
    
    # Help Center
    path('help-center/', HelpCenterView.as_view(), name='help-center'),
    path('help-center/search/', HelpCenterSearch.as_view(), name='help-center-search'),
    path('help-center/article/<slug:slug>/', HelpArticleView.as_view(), name='help-article'),
    
    # Authentication
    path('register/', lambda request: __import__('django.shortcuts').shortcuts.redirect('accounts:register'), name='register'),
    path('sign-in/', SignInView.as_view(), name='sign-in'),
    path('sign-out/', SignOutView.as_view(), name='sign-out'),
    
    # Dashboard
    path('dashboard/', DashboardShellView.as_view(), name='dashboard'),
    path('dashboard/bookings/', BookingListPartial.as_view(), name='dashboard-bookings'),
    path('dashboard/booking/<int:pk>/update/', BookingUpdatePartial.as_view(), name='dashboard-booking-update'),
    path('dashboard/profile/', ProfileUpdateView.as_view(), name='dashboard-profile'),
    path('dashboard/booking/<int:booking_pk>/rate/', RatingCreatePartial.as_view(), name='dashboard-rating-create'),
    path('dashboard/booking/<int:booking_id>/details/', booking_details_modal, name='booking-details-modal'),
    path('dashboard/ratings/', ProviderRatingsPartial.as_view(), name='dashboard-ratings'),
    path('dashboard/payment-method/add/', AddPaymentMethodView.as_view(), name='add-payment-method'),
    path('dashboard/payment-method/<int:pk>/set-default/', set_default_payment_method, name='set-default-payment'),
    
    # Provider availability endpoints
    path('dashboard/provider/availability/', update_provider_availability, name='update-provider-availability'),
    path('dashboard/provider/schedule/', update_provider_schedule, name='update-provider-schedule'),
    path('dashboard/provider/service-areas/', update_service_areas, name='update-service-areas'),
    
    # Profile and document management
    path('dashboard/upload-document/', upload_document, name='upload-document'),
    path('dashboard/update-profile/', update_profile, name='profile-update'),
    path('dashboard/settings/update/', update_settings, name='update-settings'),
    
    # Notification management
    path('dashboard/notification/<int:notification_id>/read/', mark_notification_read, name='mark-notification-read'),
    path('dashboard/notifications/mark-all-read/', mark_all_notifications_read, name='mark-all-notifications-read'),
    
    # Provider onboarding
    path('providers/', ProviderLandingView.as_view(), name='providers'),
    path('providers/apply/', ProviderApplicationWizard.as_view(), name='provider-apply'),
    path('apply-worker/', ApplyWorkerView.as_view(), name='apply-worker'),
    
    # Booking Flow (Original - keeping for backward compatibility)
    path('book/', booking_flow, name='booking-flow'),
    path('booking-flow/screen/<str:screen_number>/', booking_screen, name='booking-screen'),
    path('booking-flow/save-data/', save_booking_data, name='save-booking-data'),
    path('booking-flow/get-data/', get_booking_data, name='get-booking-data'),
    path('booking-flow/workers/', get_available_workers, name='get-available-workers'),
    path('booking-flow/addresses/', get_user_addresses, name='get-user-addresses'),
    path('booking-flow/payment/', process_payment, name='process-payment'),
    
    # MPA Booking Flow (New simplified architecture)
    path('book-mpa/', include('website.urls_mpa', namespace='booking_mpa')),
    
    # API endpoints
    path('api/payment-methods/', get_payment_methods, name='api-payment-methods'),
    path('api/pricing/calculate/', calculate_booking_price, name='api-calculate-pricing'),
    path('api/pricing/config/', get_pricing_config, name='api-pricing-config'),
    
    # New API endpoints for worker models
    path('api/', include('website.api.urls', namespace='api')),
    
    # Legal / Static pages (using CMS)
    path('privacy-policy/', views.FlatPageView.as_view(), {'slug': 'privacy-policy'}, name='privacy-policy'),
    path('terms-of-service/', views.FlatPageView.as_view(), {'slug': 'terms-of-service'}, name='terms-of-service'),
    path('cookie-policy/', views.FlatPageView.as_view(), {'slug': 'cookie-policy'}, name='cookie-policy'),
    path('accessibility-statement/', views.FlatPageView.as_view(), {'slug': 'accessibility-statement'}, name='accessibility-statement'),
    path('refund-policy/', views.FlatPageView.as_view(), {'slug': 'refund-policy'}, name='refund-policy'),
    
    # Generic CMS page handler
    path('page/<slug:slug>/', views.FlatPageView.as_view(), name='page'),
]

# Legacy URLs for backwards compatibility
legacy_patterns = [
    path('blog/', views.blog, name='blog-legacy'),
    path('blog-post/', views.blog_post, name='blog-post-legacy'),
    path('contact/', views.contact, name='contact-legacy'),
    path('pricing/', views.pricing, name='pricing-legacy'),
    path('services/', views.services, name='services-legacy'),
    path('register/', views.register, name='register-legacy'),
    path('sign-in/', views.sign_in, name='sign-in-legacy'),
    path('dashboard/', views.dashboard, name='dashboard-legacy'),
    path('privacy-policy/', views.privacy_policy, name='privacy-policy-legacy'),
    path('terms-of-service/', views.terms_of_service, name='terms-of-service-legacy'),
    path('cookie-policy/', views.cookie_policy, name='cookie-policy-legacy'),
    path('accessibility-statement/', views.accessibility_statement, name='accessibility-statement-legacy'),
    path('refund-policy/', views.refund_policy, name='refund-policy-legacy'),
    path('help-center/', views.help_center, name='help-center-legacy'),
]

# Add legacy patterns
urlpatterns += legacy_patterns
