from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, UpdateView, CreateView, FormView
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.contrib import messages
from django import forms
from bookings.models import Booking, Rating
from payments.models import Payment, Payout
from notifications.models import Notification
from accounts.models import User, ProviderProfile, Profile
from datetime import datetime, timedelta
from typing import Dict, Any


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
        
        # Get recent transactions
        recent_transactions = []
        if user.role == 'customer':
            # Get customer payments
            payments = Payment.objects.filter(
                booking__customer=user
            ).select_related('booking', 'booking__service_task').order_by('-created_at')[:10]
            
            for payment in payments:
                recent_transactions.append({
                    'id': payment.reference,
                    'date': payment.created_at,
                    'description': f'Booking: {payment.booking.service_task.name if payment.booking.service_task else "Service"}',
                    'amount': payment.amount,
                    'amount_display': payment.amount_display,
                    'status': payment.status,
                    'status_display': payment.get_status_display(),
                    'type': 'payment',
                })
        else:  # provider
            # Get provider payouts
            payouts = Payout.objects.filter(
                provider=user
            ).order_by('-created_at')[:10]
            
            for payout in payouts:
                recent_transactions.append({
                    'id': f'PAYOUT-{payout.id}',
                    'date': payout.created_at,
                    'description': f'Payout for week {payout.week_display}',
                    'amount': payout.net_amount,
                    'amount_display': payout.net_amount_display,
                    'status': payout.status,
                    'status_display': payout.get_status_display(),
                    'type': 'payout',
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