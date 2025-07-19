from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, UpdateView, CreateView, FormView, View
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.contrib import messages
from django import forms
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from bookings.models import Booking, Rating
from payments.models import Payment, Payout, RecentTransaction
from notifications.models import Notification
from accounts.models import User, ProviderProfile, Profile, PaymentMethod
from datetime import datetime, timedelta
from typing import Dict, Any
import uuid


class DashboardShellView(LoginRequiredMixin, TemplateView):
    """Main dashboard shell that renders tabs with lazy loading."""
    
    template_name = 'website/components/dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for dashboard shell."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Initialize next_booking as None for both user types
        next_booking = None
        
        # Get basic user stats
        if user.role == 'customer':
            total_bookings = user.bookings.count()
            upcoming_bookings = user.bookings.filter(
                status__in=['pending', 'accepted', 'in_progress'],
                start_at__gt=timezone.now()
            ).count()
            
            # Get next booking
            next_booking = user.bookings.filter(
                status__in=['pending', 'accepted'],
                start_at__gt=timezone.now()
            ).order_by('start_at').first()
            
            dashboard_stats = {
                'total_bookings': total_bookings,
                'upcoming_bookings': upcoming_bookings,
                'completed_bookings': user.bookings.filter(status='completed').count(),
                'next_booking': next_booking,
            }
            
        else:  # provider
            total_jobs = user.jobs.count()
            upcoming_jobs = user.jobs.filter(
                status__in=['accepted', 'in_progress'],
                start_at__gt=timezone.now()
            ).count()
            
            # Get next job for provider (equivalent to next_booking for customer)
            next_booking = user.jobs.filter(
                status__in=['accepted', 'in_progress'],
                start_at__gt=timezone.now()
            ).order_by('start_at').first()
            
            # Get provider profile
            provider_profile = getattr(user, 'provider', None)
            
            dashboard_stats = {
                'total_jobs': total_jobs,
                'upcoming_jobs': upcoming_jobs,
                'completed_jobs': user.jobs.filter(status='completed').count(),
                'next_job': next_booking,  # Added next_job for providers
                'is_approved': provider_profile.is_approved if provider_profile else False,
                'rating_average': provider_profile.rating_average if provider_profile else 0,
                'rating_count': provider_profile.rating_count if provider_profile else 0,
            }
        
        # Get unread notifications
        unread_notifications = user.notifications.filter(is_read=False).count()
        
        # Get or create user profile
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Build dashboard_data for template compatibility
        dashboard_data = {
            'next_booking': {
                'date': next_booking.start_at.strftime('%B %d, %Y') if next_booking else '',
                'time': next_booking.start_at.strftime('%I:%M %p') if next_booking else '',
                'service': getattr(next_booking.service_task, 'name', '') if next_booking and hasattr(next_booking, 'service_task') else '',
                'address': getattr(next_booking, 'address', '') if next_booking else '',
                'provider': next_booking.provider.get_full_name() if next_booking and hasattr(next_booking, 'provider') and next_booking.provider else '',
                'customer': next_booking.customer.get_full_name() if next_booking and hasattr(next_booking, 'customer') and next_booking.customer else '',
                'countdown': ''  # You could implement countdown logic here
            },
            'wallet_balance': 0,  # Implement wallet balance logic
            'referral_credits': 0,  # Implement referral credits logic
            'total_bookings': dashboard_stats.get('total_bookings', dashboard_stats.get('total_jobs', 0)),
            'upcoming_bookings': dashboard_stats.get('upcoming_bookings', dashboard_stats.get('upcoming_jobs', 0)),
            'completed_bookings': dashboard_stats.get('completed_bookings', dashboard_stats.get('completed_jobs', 0)),
            'notifications_count': unread_notifications,
            'unread_messages': 0,  # Implement unread messages logic
        }
        
        # Fetch bookings for the bookings tab
        if user.role == 'customer':
            # Get bookings categorized by status
            all_bookings = user.bookings.select_related('provider', 'service_task').order_by('-start_at')
            
            upcoming_bookings_list = all_bookings.filter(
                status__in=['pending', 'accepted', 'in_progress'],
                start_at__gt=timezone.now()
            )
            
            # Recurring bookings would need a separate model or field to track
            # For now, we'll leave it empty
            recurring_bookings_list = []
            
            completed_bookings_list = all_bookings.filter(status='completed')
            
            cancelled_bookings_list = all_bookings.filter(status='cancelled')
            
        else:  # provider
            all_bookings = user.jobs.select_related('customer', 'service_task').order_by('-start_at')
            
            upcoming_bookings_list = all_bookings.filter(
                status__in=['accepted', 'in_progress'],
                start_at__gt=timezone.now()
            )
            
            recurring_bookings_list = []
            
            completed_bookings_list = all_bookings.filter(status='completed')
            
            cancelled_bookings_list = all_bookings.filter(status='cancelled')
        
        # Get profile completion percentage
        # Check both User and Profile fields
        user_fields = ['email', 'phone']
        profile_fields = ['first_name', 'last_name', 'profile_picture']
        
        completed_fields = 0
        # Check user fields
        for field in user_fields:
            if getattr(user, field):
                completed_fields += 1
        
        # Check profile fields
        for field in profile_fields:
            value = getattr(profile, field, None)
            if value and (field != 'profile_picture' or value.name):
                completed_fields += 1
        
        total_fields = len(user_fields) + len(profile_fields)
        profile_completion = int((completed_fields / total_fields) * 100) if total_fields > 0 else 0
        
        # Get notification preferences
        notification_preferences = {
            'email_notifications': profile.email_notifications,
            'sms_notifications': profile.sms_notifications,
            'newsletter': profile.newsletter,
            'marketing_communications': profile.marketing_communications,
        }
        
        # Get user's payment methods
        payment_methods = user.payment_methods.filter(is_active=True).order_by('-is_default', '-added_at')
        
        # Get user locations
        locations = user.locations.all().order_by('-is_main', '-created_at')
        
        context.update({
            'title': 'Dashboard - Zela',
            'dashboard_stats': dashboard_stats,
            'dashboard_data': dashboard_data,  # Added for template compatibility
            'unread_notifications': unread_notifications,
            'is_provider': user.role == 'provider',
            'profile': profile,
            'profile_completion': profile_completion,
            'notification_preferences': notification_preferences,
            'upcoming_bookings_list': upcoming_bookings_list,
            'recurring_bookings_list': recurring_bookings_list,
            'completed_bookings_list': completed_bookings_list,
            'cancelled_bookings_list': cancelled_bookings_list,
            'upcoming_bookings_count': upcoming_bookings_list.count(),
            'recurring_bookings_count': len(recurring_bookings_list),
            'completed_bookings_count': completed_bookings_list.count(),
            'cancelled_bookings_count': cancelled_bookings_list.count(),
            'payment_methods': payment_methods,
            'locations': locations,
        })
        
        return context


class BookingListPartial(LoginRequiredMixin, ListView):
    """Booking list partial with auto-refresh."""
    
    model = Booking
    template_name = 'website/components/dashboard/tabs/bookings.html'
    context_object_name = 'bookings'
    paginate_by = 10
    
    def get_queryset(self):
        """Return bookings for the current user."""
        user = self.request.user
        
        if user.role == 'customer':
            queryset = user.bookings.all()
        else:  # provider
            queryset = user.jobs.all()
        
        # Filter by status
        status = self.request.GET.get('status', '').strip()
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related('customer', 'provider', 'service_task').order_by('-created_at')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for bookings."""
        context = super().get_context_data(**kwargs)
        
        # Get status counts
        user = self.request.user
        if user.role == 'customer':
            base_query = user.bookings
        else:
            base_query = user.jobs
        
        status_counts = {
            'all': base_query.count(),
            'pending': base_query.filter(status='pending').count(),
            'accepted': base_query.filter(status='accepted').count(),
            'in_progress': base_query.filter(status='in_progress').count(),
            'completed': base_query.filter(status='completed').count(),
            'cancelled': base_query.filter(status='cancelled').count(),
        }
        
        context.update({
            'status_counts': status_counts,
            'selected_status': self.request.GET.get('status', ''),
        })
        
        return context


class BookingUpdatePartial(LoginRequiredMixin, UpdateView):
    """Booking update partial for reschedule/cancel."""
    
    model = Booking
    template_name = 'website/components/dashboard/booking-update-modal.html'
    fields = ['start_at', 'end_at', 'notes']
    
    def get_object(self):
        """Get booking ensuring user has permission."""
        booking = get_object_or_404(Booking, pk=self.kwargs['pk'])
        
        # Check permissions
        if self.request.user.role == 'customer':
            if booking.customer != self.request.user:
                raise PermissionError("You don't have permission to modify this booking.")
        else:  # provider
            if booking.provider != self.request.user:
                raise PermissionError("You don't have permission to modify this booking.")
        
        return booking
    
    def form_valid(self, form):
        """Handle valid booking update."""
        booking = form.save()
        
        # Create notification for the other party
        if self.request.user.role == 'customer':
            if booking.provider:
                Notification.objects.create(
                    user=booking.provider,
                    title="Booking Updated",
                    message=f"Booking #{booking.pk} has been updated by the customer.",
                    notification_type="booking",
                    link=f"/dashboard/bookings/?booking={booking.pk}"
                )
        else:  # provider
            Notification.objects.create(
                user=booking.customer,
                title="Booking Updated",
                message=f"Booking #{booking.pk} has been updated by your provider.",
                notification_type="booking",
                link=f"/dashboard/bookings/?booking={booking.pk}"
            )
        
        if self.request.htmx:
            return JsonResponse({
                'ok': 1,
                'message': 'Booking updated successfully.',
                'reload': True
            })
        
        messages.success(self.request, 'Booking updated successfully.')
        return redirect('website:dashboard-bookings')
    
    def form_invalid(self, form):
        """Handle invalid booking update."""
        if self.request.htmx:
            return JsonResponse({
                'ok': 0,
                'errors': form.errors,
                'message': 'Please check your form and try again.'
            })
        
        return super().form_invalid(form)


class ProfileUpdateForm(forms.Form):
    """Combined profile update form for User and Profile models."""
    
    # Profile model fields
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    # User model fields
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    # Profile picture
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*'
        })
    )
    
    # Notification preferences
    email_notifications = forms.BooleanField(required=False)
    sms_notifications = forms.BooleanField(required=False)
    newsletter = forms.BooleanField(required=False)
    marketing_communications = forms.BooleanField(required=False)


class ProfileUpdateView(LoginRequiredMixin, FormView):
    """Profile update view."""
    
    form_class = ProfileUpdateForm
    template_name = 'website/components/dashboard/tabs/profile.html'
    
    def get_form_kwargs(self):
        """Pass initial data to form."""
        kwargs = super().get_form_kwargs()
        user = self.request.user
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Set initial data from both models
        kwargs['initial'] = {
            'first_name': profile.first_name or user.first_name,
            'last_name': profile.last_name or user.last_name,
            'phone': user.phone,
            'email_notifications': profile.email_notifications,
            'sms_notifications': profile.sms_notifications,
            'newsletter': profile.newsletter,
            'marketing_communications': profile.marketing_communications,
        }
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Add context data for profile tab."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get or create user profile
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Get user's payment methods (currently we don't have a PaymentMethod model)
        # For now, we'll get unique payment gateways used in past payments
        payment_methods = []
        if user.role == 'customer':
            used_gateways = Payment.objects.filter(
                booking__customer=user,
                status='success'
            ).values_list('gateway', flat=True).distinct()
            
            for gateway in used_gateways:
                payment_methods.append({
                    'type': gateway.replace('_', ' ').title(),
                    'last_four': '****',  # We don't store card details
                    'icon': gateway,
                })
        
        # Get recent transactions from the new model
        recent_transactions = []
        transactions = RecentTransaction.objects.filter(
            user=user
        ).select_related('payment', 'payout').order_by('-created_at')[:10]
        
        for transaction in transactions:
            recent_transactions.append({
                'id': transaction.reference,
                'date': transaction.created_at,
                'description': transaction.description,
                'amount': transaction.amount,
                'amount_display': transaction.amount_display,
                'status': transaction.status,
                'status_display': transaction.get_status_display(),
                'type': transaction.transaction_type,
                'is_credit': transaction.is_credit,
                'is_debit': transaction.is_debit,
            })
        
        # Get profile completion percentage
        # Check both User and Profile fields
        user_fields = ['email', 'phone']
        profile_fields = ['first_name', 'last_name', 'profile_picture']
        
        completed_fields = 0
        # Check user fields
        for field in user_fields:
            if getattr(user, field):
                completed_fields += 1
        
        # Check profile fields
        for field in profile_fields:
            value = getattr(profile, field, None)
            if value and (field != 'profile_picture' or value.name):
                completed_fields += 1
        
        total_fields = len(user_fields) + len(profile_fields)
        profile_completion = int((completed_fields / total_fields) * 100) if total_fields > 0 else 0
        
        # Check if user has verified email (simplified check)
        email_verified = bool(user.email)
        
        # Get notification preferences from profile
        notification_preferences = {
            'email_notifications': profile.email_notifications,
            'sms_notifications': profile.sms_notifications,
            'newsletter': profile.newsletter,
            'marketing_communications': profile.marketing_communications,
        }
        
        context.update({
            'user': user,
            'profile': profile,
            'payment_methods': payment_methods,
            'recent_transactions': recent_transactions,
            'profile_completion': profile_completion,
            'email_verified': email_verified,
            'notification_preferences': notification_preferences,
            'has_company_info': False,  # We don't have a company model yet
        })
        
        return context
    
    def form_valid(self, form):
        """Handle valid profile update."""
        user = self.request.user
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Update Profile model fields
        profile.first_name = form.cleaned_data['first_name']
        profile.last_name = form.cleaned_data['last_name']
        
        # Handle profile picture upload
        if 'profile_picture' in self.request.FILES:
            profile.profile_picture = self.request.FILES['profile_picture']
        
        # Update notification preferences
        profile.email_notifications = form.cleaned_data['email_notifications']
        profile.sms_notifications = form.cleaned_data['sms_notifications']
        profile.newsletter = form.cleaned_data['newsletter']
        profile.marketing_communications = form.cleaned_data['marketing_communications']
        profile.save()
        
        # Update User model fields
        user.phone = form.cleaned_data['phone']
        user.save()
        
        if self.request.htmx:
            return JsonResponse({
                'ok': 1,
                'message': 'Profile updated successfully.'
            })
        
        messages.success(self.request, 'Profile updated successfully.')
        return redirect('website:dashboard')
    
    def form_invalid(self, form):
        """Handle invalid profile update."""
        if self.request.htmx:
            return JsonResponse({
                'ok': 0,
                'errors': form.errors,
                'message': 'Please check your form and try again.'
            })
        
        return super().form_invalid(form)


class RatingForm(forms.ModelForm):
    """Rating form."""
    
    class Meta:
        model = Rating
        fields = ['score', 'comment']
        widgets = {
            'score': forms.Select(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}
            ),
            'comment': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Share your experience...'
            }),
        }


class RatingCreatePartial(LoginRequiredMixin, CreateView):
    """Rating creation partial after job completion."""
    
    model = Rating
    form_class = RatingForm
    template_name = 'website/components/dashboard/rating-modal.html'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add booking context."""
        context = super().get_context_data(**kwargs)
        booking = get_object_or_404(Booking, pk=self.kwargs['booking_pk'])
        
        # Ensure user can rate this booking
        if booking.customer != self.request.user:
            raise PermissionError("You can only rate your own bookings.")
        
        if booking.status != 'completed':
            raise PermissionError("You can only rate completed bookings.")
        
        context['booking'] = booking
        return context
    
    def form_valid(self, form):
        """Handle valid rating creation."""
        booking = get_object_or_404(Booking, pk=self.kwargs['booking_pk'])
        
        # Set the booking
        form.instance.booking = booking
        rating = form.save()
        
        # Update provider's rating
        if booking.provider and hasattr(booking.provider, 'provider'):
            provider_profile = booking.provider.provider
            
            # Calculate new average
            ratings = Rating.objects.filter(booking__provider=booking.provider)
            avg_rating = ratings.aggregate(Avg('score'))['score__avg']
            
            provider_profile.rating_average = round(avg_rating, 2)
            provider_profile.rating_count = ratings.count()
            provider_profile.save()
            
            # Create notification for provider
            Notification.objects.create(
                user=booking.provider,
                title="New Rating Received",
                message=f"You received a {rating.score}-star rating for booking #{booking.pk}.",
                notification_type="rating",
                link=f"/dashboard/ratings/"
            )
        
        if self.request.htmx:
            return JsonResponse({
                'ok': 1,
                'message': 'Thank you for your rating!',
                'reload': True
            })
        
        messages.success(self.request, 'Thank you for your rating!')
        return redirect('website:dashboard-bookings')
    
    def form_invalid(self, form):
        """Handle invalid rating creation."""
        if self.request.htmx:
            return JsonResponse({
                'ok': 0,
                'errors': form.errors,
                'message': 'Please check your form and try again.'
            })
        
        return super().form_invalid(form)


class AddPaymentMethodView(LoginRequiredMixin, View):
    """Handle adding new payment methods."""
    
    def get(self, request):
        """Return the add payment method modal."""
        return render(request, 'website/components/dashboard/modals/add-payment-method.html')
    
    def post(self, request):
        """Create a new payment method."""
        user = request.user
        kind = request.POST.get('kind', 'card')
        
        try:
            if kind == 'card':
                # Extract card details
                card_number = request.POST.get('card_number', '').replace(' ', '')
                expiry = request.POST.get('expiry', '')
                cvv = request.POST.get('cvv', '')
                cardholder_name = request.POST.get('cardholder_name', '')
                
                # Basic validation
                if not all([card_number, expiry, cvv, cardholder_name]):
                    raise ValueError("All card fields are required")
                
                # Extract expiry month and year
                if '/' in expiry:
                    month, year = expiry.split('/')
                    expiry_month = int(month)
                    expiry_year = 2000 + int(year)  # Convert YY to YYYY
                else:
                    raise ValueError("Invalid expiry date format")
                
                # Detect card brand
                if card_number.startswith('4'):
                    brand = 'visa'
                elif card_number.startswith('5'):
                    brand = 'mastercard'
                elif card_number.startswith('3'):
                    brand = 'amex'
                else:
                    brand = 'other'
                
                # If this is the first payment method, set it as default
                is_first = not user.payment_methods.filter(is_active=True).exists()
                
                # Create payment method
                # In production, you would tokenize the card with your payment processor
                # For now, we'll generate a mock provider_id
                payment_method = PaymentMethod.objects.create(
                    user=user,
                    kind=kind,
                    provider_id=f"pm_{uuid.uuid4().hex[:16]}",  # Mock provider ID
                    brand=brand,
                    last4=card_number[-4:],
                    expiry_month=expiry_month,
                    expiry_year=expiry_year,
                    is_default=is_first,
                    is_active=True
                )
                
                # If this is not the first card but user wants it as default,
                # unset other defaults (this would be handled by a checkbox in the form)
                if request.POST.get('set_as_default') == 'true' and not is_first:
                    user.payment_methods.exclude(id=payment_method.id).update(is_default=False)
                    payment_method.is_default = True
                    payment_method.save()
                
            elif kind in ['paypal', 'apple']:
                # For PayPal and Apple Pay, we'd normally redirect to their auth flow
                # For now, create a mock payment method
                is_first = not user.payment_methods.filter(is_active=True).exists()
                
                payment_method = PaymentMethod.objects.create(
                    user=user,
                    kind=kind,
                    provider_id=f"{kind}_{uuid.uuid4().hex[:16]}",
                    is_default=is_first,
                    is_active=True
                )
            else:
                raise ValueError("Invalid payment method type")
            
            # Get all payment methods for the user to return updated list
            payment_methods = user.payment_methods.filter(is_active=True).order_by('-is_default', '-added_at')
            
            # Return updated payment methods list
            return render(request, 'website/components/dashboard/tabs/wallet-payment-methods.html', {
                'payment_methods': payment_methods
            })
            
        except Exception as e:
            # Return error response
            if request.htmx:
                return HttpResponse(
                    f'<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{str(e)}</div>',
                    status=400
                )
            messages.error(request, f"Error adding payment method: {str(e)}")
            return redirect('website:dashboard')


@login_required
@require_http_methods(["POST"])
def set_default_payment_method(request, pk):
    """Set a payment method as default."""
    try:
        payment_method = get_object_or_404(PaymentMethod, pk=pk, user=request.user, is_active=True)
        
        # Unset all other defaults
        request.user.payment_methods.exclude(id=payment_method.id).update(is_default=False)
        
        # Set this one as default
        payment_method.is_default = True
        payment_method.save()
        
        # Get all payment methods for the user
        payment_methods = request.user.payment_methods.filter(is_active=True).order_by('-is_default', '-added_at')
        
        # Return updated payment methods list
        return render(request, 'website/components/dashboard/tabs/wallet-payment-methods.html', {
            'payment_methods': payment_methods
        })
        
    except Exception as e:
        if request.htmx:
            return HttpResponse(
                f'<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">Error: {str(e)}</div>',
                status=400
            )
        messages.error(request, f"Error setting default payment method: {str(e)}")
        return redirect('website:dashboard')