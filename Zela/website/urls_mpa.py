from django.urls import path
from .views.booking_mpa import (
    BookingServiceSelectView,
    BookingAddressView,
    BookingPropertyView,
    BookingServiceConfigView,
    BookingScheduleView,
    BookingDurationView,
    BookingWorkerView,
    BookingPaymentView,
    BookingConfirmationView,
    BookingReviewView,
)

app_name = 'booking_mpa'

urlpatterns = [
    # MPA Booking Flow URLs
    path('', BookingServiceSelectView.as_view(), name='service-select'),
    path('address/', BookingAddressView.as_view(), name='address'),
    path('property/', BookingPropertyView.as_view(), name='property'),
    path('service-config/', BookingServiceConfigView.as_view(), name='service-config'),
    path('schedule/', BookingScheduleView.as_view(), name='schedule'),
    path('duration/', BookingDurationView.as_view(), name='duration'),
    path('worker/', BookingWorkerView.as_view(), name='worker'),
    path('payment/', BookingPaymentView.as_view(), name='payment'),
    path('review/', BookingReviewView.as_view(), name='review'),
    path('confirmation/', BookingConfirmationView.as_view(), name='confirmation'),
]