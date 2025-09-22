"""
Multi-Page Application (MPA) booking flow views.
Simplified architecture following industry standards.
"""
from django.views.generic import TemplateView, FormView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django import forms
from django.http import Http404
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import json
from typing import Dict, List, Optional

from services.models import ServiceCategory, ServiceTask
from workers.models import PropertyTypology, Worker, ServicePackage
from bookings.models import Booking


class BookingFlowMixin:
    """Base mixin for all booking flow views."""
    
    def dispatch(self, request, *args, **kwargs):
        """Initialize booking session if needed."""
        if 'booking_data' not in request.session:
            request.session['booking_data'] = {}
        return super().dispatch(request, *args, **kwargs)
    
    def get_booking_data(self) -> Dict:
        """Get booking data from session."""
        return self.request.session.get('booking_data', {})
    
    def save_booking_data(self, data: Dict) -> None:
        """Save booking data to session."""
        booking_data = self.get_booking_data()
        booking_data.update(data)
        self.request.session['booking_data'] = booking_data
        self.request.session.modified = True
    
    def clear_booking_data(self) -> None:
        """Clear all booking data from session."""
        self.request.session['booking_data'] = {}
        self.request.session.modified = True
    
    def get_service_slug(self) -> Optional[str]:
        """Get the current service slug from booking data."""
        booking_data = self.get_booking_data()
        return booking_data.get('service_slug')
    
    def get_service_category(self) -> Optional[ServiceCategory]:
        """Get the current service category."""
        service_slug = self.get_service_slug()
        if not service_slug:
            return None
        try:
            return ServiceCategory.objects.get(slug=service_slug, is_active=True)
        except ServiceCategory.DoesNotExist:
            return None
    
    def get_service_flow(self) -> List[str]:
        """Get the flow steps for the current service."""
        from website.services.booking_flows import get_service_flow
        service_slug = self.get_service_slug()
        if not service_slug:
            return []
        return get_service_flow(service_slug)
    
    def get_current_step(self) -> str:
        """Get the current step name based on the view."""
        return getattr(self, 'step_name', '')
    
    def get_next_step(self) -> Optional[str]:
        """Get the next step in the flow."""
        flow = self.get_service_flow()
        current = self.get_current_step()
        try:
            current_index = flow.index(current)
            if current_index < len(flow) - 1:
                return flow[current_index + 1]
        except (ValueError, IndexError):
            pass
        return None
    
    def get_previous_step(self) -> Optional[str]:
        """Get the previous step in the flow."""
        flow = self.get_service_flow()
        current = self.get_current_step()
        try:
            current_index = flow.index(current)
            if current_index > 0:
                return flow[current_index - 1]
        except (ValueError, IndexError):
            pass
        return None
    
    def get_next_url(self) -> str:
        """Get URL for the next step."""
        next_step = self.get_next_step()
        if next_step:
            return reverse(f'website:booking_mpa:{next_step}')
        return reverse('website:booking_mpa:confirmation')
    
    def get_previous_url(self) -> str:
        """Get URL for the previous step."""
        previous_step = self.get_previous_step()
        if previous_step:
            return reverse(f'website:booking_mpa:{previous_step}')
        return reverse('website:booking_mpa:service-select')
    
    def get_progress_percentage(self) -> int:
        """Calculate progress through the booking flow."""
        flow = self.get_service_flow()
        current = self.get_current_step()
        try:
            current_index = flow.index(current) + 1
            return int((current_index / len(flow)) * 100)
        except (ValueError, ZeroDivisionError):
            return 0
    
    def calculate_booking_price(self):
        """Calculate the price for the current booking."""
        from pricing.models import PricingConfig
        from accounts.models import ProviderProfile
        
        booking_data = self.get_booking_data()
        service_category = self.get_service_category()
        
        if not service_category:
            return 0
        
        # Get pricing configuration
        pricing_config = PricingConfig.get_instance()
        
        # Extract booking details
        duration_data = booking_data.get('duration', {})
        duration_hours = float(duration_data.get('hours', 3.5))
        property_data = booking_data.get('property', {})
        location_data = booking_data.get('address', {})
        schedule_data = booking_data.get('schedule', {})
        
        # Base hourly rate
        base_hourly_rate = pricing_config.hourly_clean_base
        
        # Calculate base cost
        base_cost = base_hourly_rate * duration_hours
        
        # Apply property size multiplier
        property_type = property_data.get('property_type', '')
        size_multipliers = {
            't0': 0.6,  # Studio
            't1': 0.7,  # 1 bedroom
            't2': 0.85, # 2 bedrooms
            't3': 1.0,  # 3 bedrooms
            't4': 1.15, # 4 bedrooms
            't5': 1.3,  # 5+ bedrooms
            'small': 0.8,
            'medium': 1.0,
            'large': 1.3,
        }
        size_multiplier = size_multipliers.get(property_type, 1.0)
        base_cost *= size_multiplier
        
        # Add extra tasks cost
        extra_tasks = duration_data.get('tasks', [])
        extra_task_cost = len(extra_tasks) * pricing_config.specialty_task_price
        
        # Get location surcharge
        location_surcharge = 0
        area_name = location_data.get('area', '')
        if area_name:
            default_areas = ProviderProfile().get_default_service_areas()
            for area in default_areas:
                if area['name'].lower() == area_name.lower():
                    location_surcharge = area['surcharge'] * 100
                    break
        
        # Calculate subtotal
        subtotal = base_cost + extra_task_cost + location_surcharge
        
        # Apply weekend multiplier if applicable
        import datetime
        booking_date = schedule_data.get('date')
        if booking_date:
            try:
                date_obj = datetime.datetime.strptime(booking_date, '%Y-%m-%d')
                if date_obj.weekday() >= 5:  # Weekend
                    subtotal *= float(pricing_config.weekend_multiplier)
            except:
                pass
        
        # Add booking fee
        booking_fee = pricing_config.booking_fee
        total = subtotal + booking_fee
        
        # Ensure minimum booking amount
        if total < pricing_config.minimum_booking_amount:
            total = pricing_config.minimum_booking_amount
        
        # Save calculated price to session
        self.save_booking_data({'total_price': round(total)})
        
        return round(total)
    
    def get_context_data(self, **kwargs):
        """Add common booking context to all views."""
        context = super().get_context_data(**kwargs)
        context.update({
            'booking_data': self.get_booking_data(),
            'service_category': self.get_service_category(),
            'current_step': self.get_current_step(),
            'next_url': self.get_next_url(),
            'previous_url': self.get_previous_url(),
            'progress': self.get_progress_percentage(),
            'service_flow': self.get_service_flow(),
        })
        return context
    
    def send_booking_confirmation_email(self, booking):
        """Send confirmation emails to customer and worker."""
        try:
            # Email to customer
            customer_context = {
                'booking': booking,
                'customer_name': booking.customer.get_full_name() or booking.customer.username,
                'service_name': booking.service_task.service_category.name,
                'booking_date': booking.start_at.strftime('%B %d, %Y'),
                'booking_time': booking.start_at.strftime('%I:%M %p'),
                'total_price': booking.total_price,
                'booking_reference': f'ZB{booking.id:06d}',
                'dashboard_url': self.request.build_absolute_uri(reverse('website:dashboard')),
            }
            
            # Render email templates
            customer_subject = f'Booking Confirmation - {customer_context["service_name"]}'
            customer_html = render_to_string('emails/booking_confirmation_customer.html', customer_context)
            customer_text = render_to_string('emails/booking_confirmation_customer.txt', customer_context)
            
            # Create and send customer email
            customer_email = EmailMultiAlternatives(
                subject=customer_subject,
                body=customer_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[booking.customer.email],
            )
            customer_email.attach_alternative(customer_html, "text/html")
            customer_email.send(fail_silently=False)
            
            # Email to worker if assigned
            if booking.worker:
                worker_context = {
                    'booking': booking,
                    'worker_name': booking.worker.user.get_full_name() or booking.worker.user.username,
                    'service_name': booking.service_task.service_category.name,
                    'booking_date': booking.start_at.strftime('%B %d, %Y'),
                    'booking_time': booking.start_at.strftime('%I:%M %p'),
                    'customer_name': customer_context['customer_name'],
                    'address': booking.address,
                    'booking_reference': customer_context['booking_reference'],
                    'dashboard_url': self.request.build_absolute_uri(reverse('website:dashboard')),  # Use same dashboard for now
                }
                
                worker_subject = f'New Booking Assignment - {worker_context["service_name"]}'
                worker_html = render_to_string('emails/booking_confirmation_worker.html', worker_context)
                worker_text = render_to_string('emails/booking_confirmation_worker.txt', worker_context)
                
                # Create and send worker email
                worker_email = EmailMultiAlternatives(
                    subject=worker_subject,
                    body=worker_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[booking.worker.user.email],
                )
                worker_email.attach_alternative(worker_html, "text/html")
                worker_email.send(fail_silently=False)
            
            return True
        except Exception as e:
            # Log the error but don't fail the booking
            print(f"Error sending confirmation email: {str(e)}")
            return False


# Service Selection View
class BookingServiceSelectView(BookingFlowMixin, TemplateView):
    """Service selection step."""
    template_name = 'website/booking_mpa/service_select.html'
    step_name = 'service-select'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all active service categories
        context['services'] = ServiceCategory.objects.filter(is_active=True)
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle service selection."""
        service_slug = request.POST.get('service')
        if service_slug:
            self.save_booking_data({'service_slug': service_slug})
            # Get the first step for this service
            flow = self.get_service_flow()
            if flow:
                return redirect(reverse(f'website:booking_mpa:{flow[0]}'))
        return redirect(self.get_next_url())


# Address Capture View
class BookingAddressForm(forms.Form):
    """Form for address capture."""
    street = forms.CharField(
        max_length=255, 
        label='Street Address',
        error_messages={'required': 'Street address is required'}
    )
    number = forms.CharField(
        max_length=50, 
        label='Number',
        error_messages={'required': 'Building number is required'}
    )
    complement = forms.CharField(max_length=100, required=False, label='Complement')
    district = forms.CharField(
        max_length=100, 
        label='District',
        error_messages={'required': 'District is required'}
    )
    city = forms.CharField(
        max_length=100, 
        label='City', 
        initial='Luanda',
        error_messages={'required': 'City is required'}
    )
    postal_code = forms.CharField(max_length=20, required=False, label='Postal Code')
    latitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    area = forms.CharField(max_length=100, required=False)
    full_address = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    def __init__(self, *args, **kwargs):
        initial_data = kwargs.pop('initial_data', {})
        super().__init__(*args, **kwargs)
        if initial_data:
            for field, value in initial_data.items():
                if field in self.fields:
                    self.fields[field].initial = value
    
    def clean_street(self):
        """Validate street address."""
        street = self.cleaned_data.get('street', '').strip()
        if len(street) < 3:
            raise forms.ValidationError('Please provide a valid street address')
        return street
    
    def clean(self):
        """Build full address and validate coordinates."""
        cleaned_data = super().clean()
        
        # Build full address
        street = cleaned_data.get('street', '')
        number = cleaned_data.get('number', '')
        district = cleaned_data.get('district', '')
        city = cleaned_data.get('city', '')
        
        if street and number and district and city:
            full_address = f"{street} {number}, {district}, {city}"
            cleaned_data['full_address'] = full_address
        
        # Validate coordinates or district
        if not cleaned_data.get('latitude') and not cleaned_data.get('district'):
            self.add_error('street', 'Please select your location on the map or provide a district')
        
        return cleaned_data


class BookingAddressView(BookingFlowMixin, FormView):
    """Address capture step."""
    template_name = 'website/booking_mpa/address.html'
    form_class = BookingAddressForm
    step_name = 'address'
    
    def get_context_data(self, **kwargs):
        """Add saved addresses to context."""
        context = super().get_context_data(**kwargs)
        
        # Get saved addresses if user is authenticated
        # TODO: Implement saved addresses when model is available
        if self.request.user.is_authenticated:
            # For now, return mock saved addresses for testing
            context['saved_addresses'] = [
                {
                    'id': 1,
                    'name': 'Home',
                    'full_address': 'Nieuwezijds Voorburgwal 320-2, Amsterdam, Noord-Holland, 1012 RV, AO',
                    'is_main': True
                },
                {
                    'id': 2,
                    'name': 'Home',  
                    'full_address': 'Ferdinand Bolstraat 1, Ferdinand Bolstraat 1, Amsterdam, Noord-Holland, 1072LL, AO',
                    'is_main': False
                }
            ] if self.request.user.is_authenticated else []
        
        return context
    
    def get_form_kwargs(self):
        """Add booking data to form initialization."""
        kwargs = super().get_form_kwargs()
        booking_data = self.get_booking_data()
        kwargs['initial_data'] = booking_data.get('address', {})
        return kwargs
    
    def form_valid(self, form):
        """Save address data and proceed."""
        address_data = form.cleaned_data
        self.save_booking_data({'address': address_data})
        return redirect(self.get_next_url())


# Property Typology View
class BookingPropertyForm(forms.Form):
    """Form for property selection."""
    property_type = forms.ModelChoiceField(
        queryset=PropertyTypology.objects.all(),
        widget=forms.RadioSelect,
        label='Property Type'
    )
    bedrooms = forms.IntegerField(min_value=0, max_value=10, required=False)
    bathrooms = forms.IntegerField(min_value=1, max_value=10, required=False)


class BookingPropertyView(BookingFlowMixin, FormView):
    """Property typology selection step."""
    template_name = 'website/booking_mpa/property.html'
    form_class = BookingPropertyForm
    step_name = 'property'
    
    def dispatch(self, request, *args, **kwargs):
        """Check if this step is needed for the service."""
        service_flow = self.get_service_flow()
        if 'property' not in service_flow:
            # Skip to next step
            return redirect(self.get_next_url())
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['property_types'] = PropertyTypology.objects.all()
        return context
    
    def form_valid(self, form):
        """Save property data and proceed."""
        property_data = {
            'property_type_id': form.cleaned_data['property_type'].id,
            'property_type_name': form.cleaned_data['property_type'].name,
            'bedrooms': form.cleaned_data.get('bedrooms'),
            'bathrooms': form.cleaned_data.get('bathrooms'),
        }
        self.save_booking_data({'property': property_data})
        return redirect(self.get_next_url())


# Service Configuration View (for electrician, pest control, etc.)
class BookingServiceConfigView(BookingFlowMixin, TemplateView):
    """Service-specific configuration step."""
    template_name = 'website/booking_mpa/service_config.html'
    step_name = 'service-config'
    
    def get_template_names(self):
        """Get service-specific template if exists."""
        service_slug = self.get_service_slug()
        if service_slug:
            specific_template = f'website/booking_mpa/service_config_{service_slug.replace("-", "_")}.html'
            # Check if specific template exists, otherwise use generic
            from django.template.loader import get_template
            try:
                get_template(specific_template)
                return [specific_template]
            except:
                pass
        return super().get_template_names()
    
    def dispatch(self, request, *args, **kwargs):
        """Check if this step is needed for the service."""
        service_flow = self.get_service_flow()
        if 'service-config' not in service_flow:
            return redirect(self.get_next_url())
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Handle service configuration."""
        config_data = {}
        for key, value in request.POST.items():
            if key not in ['csrfmiddlewaretoken']:
                config_data[key] = value
        self.save_booking_data({'service_config': config_data})
        return redirect(self.get_next_url())


# Schedule Selection View
class BookingScheduleForm(forms.Form):
    """Form for schedule selection."""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        error_messages={
            'required': 'Please select a date for your service',
            'invalid': 'Please enter a valid date'
        }
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        error_messages={
            'required': 'Please select a time for your service',
            'invalid': 'Please enter a valid time'
        }
    )
    urgency = forms.ChoiceField(
        choices=[
            ('normal', 'Normal'),
            ('urgent', 'Urgent (+20%)'),
            ('emergency', 'Emergency (+50%)'),
        ], 
        initial='normal', 
        required=False
    )
    
    def clean_date(self):
        """Validate that date is not in the past."""
        from datetime import date
        selected_date = self.cleaned_data.get('date')
        
        if selected_date and selected_date < date.today():
            raise forms.ValidationError('Please select a future date')
        
        # Check if date is too far in the future (e.g., max 90 days)
        from datetime import timedelta
        max_future_date = date.today() + timedelta(days=90)
        if selected_date > max_future_date:
            raise forms.ValidationError('Bookings can only be made up to 90 days in advance')
        
        return selected_date
    
    def clean_time(self):
        """Validate service time."""
        from datetime import time
        selected_time = self.cleaned_data.get('time')
        
        # Check if time is within service hours (e.g., 7 AM to 8 PM)
        if selected_time:
            if selected_time < time(7, 0):
                raise forms.ValidationError('Service starts from 7:00 AM')
            if selected_time > time(20, 0):
                raise forms.ValidationError('Latest service time is 8:00 PM')
        
        return selected_time
    
    def clean(self):
        """Additional validation for date and time combination."""
        from datetime import datetime, timedelta
        cleaned_data = super().clean()
        
        selected_date = cleaned_data.get('date')
        selected_time = cleaned_data.get('time')
        
        if selected_date and selected_time:
            # Combine date and time
            booking_datetime = datetime.combine(selected_date, selected_time)
            
            # Check if booking is at least 2 hours in the future
            min_booking_time = datetime.now() + timedelta(hours=2)
            if booking_datetime < min_booking_time:
                self.add_error('time', 'Bookings must be made at least 2 hours in advance')
        
        return cleaned_data


class BookingScheduleView(BookingFlowMixin, FormView):
    """Schedule selection step."""
    template_name = 'website/booking_mpa/schedule.html'
    form_class = BookingScheduleForm
    step_name = 'schedule'
    
    def form_valid(self, form):
        """Save schedule data and proceed."""
        schedule_data = form.cleaned_data
        # Convert time to string for session storage
        if schedule_data.get('time'):
            schedule_data['time'] = schedule_data['time'].strftime('%H:%M')
        if schedule_data.get('date'):
            schedule_data['date'] = schedule_data['date'].isoformat()
        self.save_booking_data({'schedule': schedule_data})
        return redirect(self.get_next_url())


# Duration Selection View
class BookingDurationView(BookingFlowMixin, TemplateView):
    """Duration selection step."""
    template_name = 'website/booking_mpa/duration.html'
    step_name = 'duration'
    
    def dispatch(self, request, *args, **kwargs):
        """Check if this step is needed for the service."""
        service_flow = self.get_service_flow()
        if 'duration' not in service_flow:
            return redirect(self.get_next_url())
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get service-specific duration limits
        service_category = self.get_service_category()
        if service_category:
            config = service_category.booking_requirements or {}
            context['min_duration'] = config.get('min_duration', 2)
            context['max_duration'] = config.get('max_duration', 8)
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle duration selection."""
        duration = request.POST.get('duration')
        tasks = request.POST.getlist('tasks')
        if duration:
            self.save_booking_data({
                'duration': float(duration),
                'tasks': tasks
            })
        return redirect(self.get_next_url())


# Worker Selection View
class BookingWorkerView(BookingFlowMixin, TemplateView):
    """Worker selection step."""
    template_name = 'website/booking_mpa/worker.html'
    step_name = 'worker'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get available workers for the service
        service_category = self.get_service_category()
        booking_data = self.get_booking_data()
        
        workers = Worker.objects.filter(is_active=True)
        if service_category:
            # Filter by service capability
            workers = workers.filter(
                services__in=[service_category]
            ).distinct()
        
        # Filter by location if available
        address = booking_data.get('address', {})
        if address.get('district'):
            # Filter workers by service areas
            workers = workers.filter(
                service_areas__name__icontains=address['district']
            ).distinct()
        
        # Check availability for scheduled date/time
        schedule = booking_data.get('schedule', {})
        booking_date = schedule.get('date')
        booking_time = schedule.get('time')
        
        if booking_date and booking_time:
            from datetime import datetime
            from django.db.models import Q
            
            # Parse the booking datetime
            booking_datetime_str = f"{booking_date} {booking_time}"
            booking_datetime = datetime.strptime(booking_datetime_str, '%Y-%m-%d %H:%M')
            
            # Filter out workers with conflicting bookings
            conflicting_bookings = Booking.objects.filter(
                Q(start_at__lte=booking_datetime) & Q(end_at__gt=booking_datetime),
                status__in=['accepted', 'in_progress']
            ).values_list('worker_id', flat=True)
            
            workers = workers.exclude(id__in=conflicting_bookings)
        
        # Order by rating and completions
        workers = workers.order_by('-average_rating', '-completed_bookings')
        
        context['workers'] = workers
        context['allow_any_worker'] = True  # Option for "Any available worker"
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle worker selection."""
        worker_id = request.POST.get('worker_id')
        if worker_id == 'any':
            self.save_booking_data({'worker_preference': 'any'})
        elif worker_id:
            self.save_booking_data({
                'worker_id': int(worker_id),
                'worker_preference': 'specific'
            })
        return redirect(self.get_next_url())


# Payment Method View
class BookingPaymentView(BookingFlowMixin, TemplateView):
    """Payment method selection step."""
    template_name = 'website/booking_mpa/payment.html'
    step_name = 'payment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_data = self.get_booking_data()
        
        # Calculate pricing using the mixin method
        total_price = self.calculate_booking_price()
        
        context['total_price'] = total_price
        context['payment_methods'] = [
            {'id': 'cash', 'name': 'Cash on Service', 'icon': 'cash'},
            {'id': 'transfer', 'name': 'Bank Transfer', 'icon': 'bank'},
            {'id': 'card', 'name': 'Credit/Debit Card', 'icon': 'card'},
        ]
        
        # Add pricing breakdown
        context['pricing_breakdown'] = {
            'subtotal': total_price * 0.9,  # Approximate
            'booking_fee': total_price * 0.1,  # Approximate
            'total': total_price
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle payment method selection."""
        payment_method = request.POST.get('payment_method')
        if payment_method:
            # Calculate and save the final price
            total_price = self.calculate_booking_price()
            self.save_booking_data({
                'payment_method': payment_method,
                'total_price': total_price
            })
        return redirect(self.get_next_url())


# Review Step
class BookingReviewView(BookingFlowMixin, TemplateView):
    """Review booking details before confirmation."""
    template_name = 'website/booking_mpa/review.html'
    step_name = 'review'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_data = self.get_booking_data()
        
        # Calculate price if not already done
        total_price = booking_data.get('total_price')
        if not total_price:
            total_price = self.calculate_booking_price()
        
        # Get worker details if selected
        worker = None
        worker_id = booking_data.get('worker_id')
        if worker_id:
            try:
                worker = Worker.objects.get(id=worker_id)
            except Worker.DoesNotExist:
                pass
        
        # Prepare summary data
        context['summary'] = {
            'service': self.get_service_category(),
            'address': booking_data.get('address', {}),
            'property': booking_data.get('property', {}),
            'schedule': booking_data.get('schedule', {}),
            'duration': booking_data.get('duration'),
            'worker': worker,
            'payment_method': booking_data.get('payment_method'),
            'total_price': total_price,
        }
        return context
    
    def post(self, request, *args, **kwargs):
        """Confirm and create the booking."""
        if request.POST.get('confirm'):
            # Create the actual booking
            booking = self.create_booking()
            if booking:
                self.save_booking_data({'booking_id': booking.id})
                return redirect(reverse('website:booking_mpa:confirmation'))
        return redirect(self.get_previous_url())
    
    def create_booking(self):
        """Create the booking in the database."""
        from django.utils.dateparse import parse_datetime
        from datetime import datetime, timedelta
        from website.services.payment_gateway import PaymentService
        
        booking_data = self.get_booking_data()
        
        try:
            # Get service category
            service_category = self.get_service_category()
            if not service_category:
                messages.error(self.request, 'Service not found')
                return None
            
            # Get the main service task
            service_task = ServiceTask.objects.filter(
                service_category=service_category,
                is_main_service=True
            ).first()
            
            if not service_task:
                messages.error(self.request, 'Service configuration not found')
                return None
            
            # Parse schedule data
            schedule_data = booking_data.get('schedule', {})
            start_date = schedule_data.get('date')
            start_time = schedule_data.get('time', '09:00')
            
            # Combine date and time
            start_datetime_str = f"{start_date} {start_time}"
            start_at = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M')
            
            # Calculate end time based on duration
            duration_hours = float(booking_data.get('duration', {}).get('hours', 2))
            end_at = start_at + timedelta(hours=duration_hours)
            
            # Get worker if selected
            worker = None
            worker_id = booking_data.get('worker_id')
            if worker_id:
                try:
                    worker = Worker.objects.get(id=worker_id)
                except Worker.DoesNotExist:
                    pass
            
            # Get property typology if provided
            property_typology = None
            property_data = booking_data.get('property', {})
            if property_data.get('property_type'):
                try:
                    property_typology = PropertyTypology.objects.get(
                        slug=property_data.get('property_type')
                    )
                except PropertyTypology.DoesNotExist:
                    pass
            
            # Create the booking
            booking = Booking.objects.create(
                customer=self.request.user,
                worker=worker,
                service_task=service_task,
                property_typology=property_typology,
                unit_count=booking_data.get('units'),
                start_at=start_at,
                end_at=end_at,
                address=booking_data.get('address', {}).get('full_address', ''),
                notes=booking_data.get('notes', ''),
                status='pending_confirmation',
                total_price=booking_data.get('total_price', 0),
                amount_prepaid=0,
                amount_pending=booking_data.get('total_price', 0)
            )
            
            # Add any extras/tasks
            tasks = booking_data.get('duration', {}).get('tasks', [])
            if tasks:
                extra_tasks = ServiceTask.objects.filter(
                    service_category=service_category,
                    slug__in=tasks,
                    is_main_service=False
                )
                booking.extras.set(extra_tasks)
            
            # BookingItem model doesn't exist in this codebase
            # This could be added later if needed
            
            # Process payment if not cash
            payment_method = booking_data.get('payment_method', 'cash')
            if payment_method != 'cash':
                success, payment_response = PaymentService.process_booking_payment(
                    booking, payment_method
                )
                if not success:
                    # If payment fails, cancel the booking
                    booking.status = 'payment_failed'
                    booking.save(update_fields=['status'])
                    messages.error(self.request, 'Payment processing failed. Please try again.')
                    return None
                
                # Save payment transaction ID
                if 'transaction_id' in payment_response:
                    booking.payment_transaction_id = payment_response['transaction_id']
                    booking.save(update_fields=['payment_transaction_id'])
            
            # Send confirmation emails
            self.send_booking_confirmation_email(booking)
            
            messages.success(self.request, 'Booking created successfully!')
            return booking
            
        except Exception as e:
            messages.error(self.request, f'Error creating booking: {str(e)}')
            return None


# Confirmation View
class BookingConfirmationView(BookingFlowMixin, TemplateView):
    """Booking confirmation step."""
    template_name = 'website/booking_mpa/confirmation.html'
    step_name = 'confirmation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_data = self.get_booking_data()
        booking_id = booking_data.get('booking_id')
        
        if booking_id:
            try:
                context['booking'] = Booking.objects.get(id=booking_id)
            except Booking.DoesNotExist:
                pass
        
        # Clear booking data after confirmation
        self.clear_booking_data()
        return context