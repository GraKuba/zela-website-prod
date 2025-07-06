from django.urls import path, include
from . import views
from .views.public import HomeView, ContactFormView
from .views.services import ServiceCatalogueView, ServiceDetailPartial, ServiceTaskDetailPartial, ServiceListView
from .views.blog import BlogIndexView, BlogPostView
from .views.help_center import HelpCenterView, HelpCenterSearch, HelpArticleView
from .views.auth import RegisterWizardView, SignInView, SignOutView
from .views.dashboard import (
    DashboardShellView, BookingListPartial, BookingUpdatePartial,
    ProfileUpdateView, RatingCreatePartial
)
from .views.providers import ProviderLandingView, ProviderApplicationWizard
from .views.booking import booking_flow, booking_screen, save_booking_data, process_payment

app_name = 'website'

urlpatterns = [
    # Marketing / Public pages
    path('', HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('services/', ServiceCatalogueView.as_view(), name='services'),
    path('services-list/', ServiceListView.as_view(), name='services-list'),
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
    path('register/', RegisterWizardView.as_view(), name='register'),
    path('sign-in/', SignInView.as_view(), name='sign-in'),
    path('sign-out/', SignOutView.as_view(), name='sign-out'),
    
    # Dashboard
    path('dashboard/', DashboardShellView.as_view(), name='dashboard'),
    path('dashboard/bookings/', BookingListPartial.as_view(), name='dashboard-bookings'),
    path('dashboard/booking/<int:pk>/update/', BookingUpdatePartial.as_view(), name='dashboard-booking-update'),
    path('dashboard/profile/', ProfileUpdateView.as_view(), name='dashboard-profile'),
    path('dashboard/booking/<int:booking_pk>/rate/', RatingCreatePartial.as_view(), name='dashboard-rating-create'),
    
    # Provider onboarding
    path('providers/', ProviderLandingView.as_view(), name='providers'),
    path('providers/apply/', ProviderApplicationWizard.as_view(), name='provider-apply'),
    
    # Booking Flow
    path('book/', booking_flow, name='booking-flow'),
    path('booking-flow/screen/<int:screen_number>/', booking_screen, name='booking-screen'),
    path('booking-flow/save/', save_booking_data, name='save-booking-data'),
    path('booking-flow/payment/', process_payment, name='process-payment'),
    
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
