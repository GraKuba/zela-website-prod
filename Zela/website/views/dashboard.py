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
from payments.models import Payment, Payout, RecentTransaction, ProviderWallet, EarningsHistory, PayoutRequest
from notifications.models import Notification
from accounts.models import User, ProviderProfile, Profile, PaymentMethod, DistanceRequest, UserSettings
from datetime import datetime, timedelta, date
from typing import Dict, Any
import uuid
from decimal import Decimal


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
        if user.role == 'admin':
            # Admins see all bookings
            total_bookings = Booking.objects.count()
            upcoming_bookings = Booking.objects.filter(
                status__in=['pending_confirmation', 'pending', 'accepted', 'in_progress']
            ).count()
            
            # Get next booking
            next_booking = Booking.objects.filter(
                status__in=['pending_confirmation', 'pending', 'accepted'],
                start_at__gt=timezone.now()
            ).order_by('start_at').first()
            
            dashboard_stats = {
                'total_bookings': total_bookings,
                'upcoming_bookings': upcoming_bookings,
                'completed_bookings': Booking.objects.filter(status='completed').count(),
                'next_booking': next_booking,
            }
            
        elif user.role == 'customer':
            total_bookings = user.bookings.count()
            upcoming_bookings = user.bookings.filter(
                status__in=['pending_confirmation', 'pending', 'accepted', 'in_progress']
            ).count()
            
            # Get next booking
            next_booking = user.bookings.filter(
                status__in=['pending_confirmation', 'pending', 'accepted'],
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
                status__in=['accepted', 'in_progress']
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
        
        # Get unread notifications count
        unread_notifications = user.notifications.filter(is_read=False).count()
        
        # Get all notifications for the notifications tab
        all_notifications = user.notifications.all()[:20]  # Get last 20 notifications
        
        # Group notifications by date
        from collections import defaultdict
        grouped_notifications = defaultdict(list)
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        week_start = today - timedelta(days=7)
        
        for notification in all_notifications:
            notification_date = notification.created_at.date()
            if notification_date == today:
                grouped_notifications['today'].append(notification)
            elif notification_date == yesterday:
                grouped_notifications['yesterday'].append(notification)
            elif notification_date >= week_start:
                grouped_notifications['this_week'].append(notification)
            else:
                grouped_notifications['older'].append(notification)
        
        # Get or create user profile
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Get or create user settings
        settings = UserSettings.get_or_create_for_user(user)
        
        # Build dashboard_data for template compatibility
        dashboard_data = {
            'next_booking': {
                'date': next_booking.start_at.strftime('%B %d, %Y') if next_booking else '',
                'time': next_booking.start_at.strftime('%I:%M %p') if next_booking else '',
                'service': getattr(next_booking.service_task, 'name', '') if next_booking and hasattr(next_booking, 'service_task') else '',
                'address': getattr(next_booking, 'address', '') if next_booking else '',
                'provider': next_booking.worker.user.get_full_name() if next_booking and next_booking.worker else '',
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
        if user.role == 'admin':
            # Admins see all bookings
            all_bookings = Booking.objects.select_related('customer', 'worker__user', 'service_task').order_by('-start_at')
            
            upcoming_bookings_list = all_bookings.filter(
                status__in=['pending_confirmation', 'pending', 'accepted', 'in_progress']
            )
            
            # Recurring bookings would need a separate model or field to track
            # For now, we'll leave it empty
            recurring_bookings_list = []
            
            completed_bookings_list = all_bookings.filter(status='completed')
            
            cancelled_bookings_list = all_bookings.filter(status='cancelled')
            
        elif user.role == 'customer':
            # Get bookings categorized by status
            all_bookings = user.bookings.select_related('worker__user', 'service_task').order_by('-start_at')
            
            upcoming_bookings_list = all_bookings.filter(
                status__in=['pending_confirmation', 'pending', 'accepted', 'in_progress']
            )
            
            # Recurring bookings would need a separate model or field to track
            # For now, we'll leave it empty
            recurring_bookings_list = []
            
            completed_bookings_list = all_bookings.filter(status='completed')
            
            cancelled_bookings_list = all_bookings.filter(status='cancelled')
            
        else:  # provider
            all_bookings = user.jobs.select_related('customer', 'service_task').order_by('-start_at')
            
            upcoming_bookings_list = all_bookings.filter(
                status__in=['accepted', 'in_progress']
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
        
        # Additional context for provider dashboard
        provider_context = {}
        if user.role == 'provider':
            provider_profile = getattr(user, 'provider', None)
            if provider_profile:
                # Calculate provider metrics
                provider_context['provider'] = provider_profile
                
                # Enhance next_job with additional properties
                if next_booking:
                    # Add time_until property
                    time_diff = next_booking.start_at - timezone.now()
                    minutes_until = int(time_diff.total_seconds() / 60)
                    next_booking.time_until = minutes_until if minutes_until > 0 else 0
                    
                    # Add scheduled_date and scheduled_end for template compatibility
                    next_booking.scheduled_date = next_booking.start_at
                    next_booking.scheduled_end = next_booking.end_at
                    
                    # Create a simple address object for template compatibility
                    class SimpleAddress:
                        def __init__(self, address_str):
                            self.full_address = address_str
                    
                    if isinstance(next_booking.address, str):
                        next_booking.address = SimpleAddress(next_booking.address)
                
                provider_context['next_job'] = next_booking  # Pass next_booking as next_job
                
                # Generate compliance alerts (example logic)
                compliance_alerts = []
                if not provider_profile.is_approved:
                    compliance_alerts.append({
                        'title': 'Complete Your Verification',
                        'message': 'Upload your KYC documents to start accepting jobs'
                    })
                # Add more compliance checks as needed
                provider_context['compliance_alerts'] = compliance_alerts
                
                # Calculate additional provider stats if needed
                from django.db.models import Count, Q
                
                # Get jobs completed count
                jobs_completed = user.jobs.filter(status='completed').count()
                
                # Calculate completion rate (completed vs total accepted)
                total_accepted = user.jobs.filter(
                    status__in=['accepted', 'in_progress', 'completed', 'cancelled']
                ).count()
                
                # Update provider profile statistics
                provider_profile.jobs_completed = jobs_completed
                provider_profile.jobs_total = total_accepted
                
                if total_accepted > 0:
                    provider_profile.completion_rate = (jobs_completed / total_accepted) * 100
                else:
                    provider_profile.completion_rate = 0
                
                # Get or create provider wallet
                wallet, created = ProviderWallet.objects.get_or_create(
                    provider=user,
                    defaults={'available_balance': 0, 'pending_balance': 0}
                )
                
                # Calculate this week's earnings from actual data
                today = timezone.now().date()
                week_start = today - timedelta(days=today.weekday())  # Monday of current week
                week_end = week_start + timedelta(days=6)  # Sunday
                
                # Get current week's earnings
                current_week_earnings = EarningsHistory.objects.filter(
                    provider=user,
                    date__gte=week_start,
                    date__lte=week_end
                ).aggregate(
                    total_gross=Sum('gross_amount'),
                    total_net=Sum('net_amount'),
                    total_jobs=Sum('jobs_count'),
                    total_tips=Sum('tips_amount')
                )
                
                # Get earnings for the past 4 weeks
                four_weeks_ago = week_start - timedelta(weeks=4)
                weekly_earnings_data = []
                
                for i in range(4):
                    week_offset = timedelta(weeks=i)
                    week_start_date = week_start - week_offset
                    week_end_date = week_start_date + timedelta(days=6)
                    
                    week_data = EarningsHistory.objects.filter(
                        provider=user,
                        date__gte=week_start_date,
                        date__lte=week_end_date
                    ).aggregate(
                        amount=Sum('net_amount'),
                        jobs=Sum('jobs_count')
                    )
                    
                    weekly_earnings_data.append({
                        'week': f"{week_start_date.strftime('%b %d')}-{week_end_date.strftime('%d')}",
                        'amount': float(week_data['amount'] or 0),
                        'jobs': week_data['jobs'] or 0
                    })
                
                # Get daily earnings for current week chart
                daily_earnings = []
                days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                
                for i in range(7):
                    day_date = week_start + timedelta(days=i)
                    day_earnings = EarningsHistory.objects.filter(
                        provider=user,
                        date=day_date
                    ).aggregate(
                        amount=Sum('net_amount')
                    )
                    daily_earnings.append(float(day_earnings['amount'] or 0))
                
                # Get recent earnings transactions for earnings tab
                earnings_transactions = []
                transactions = RecentTransaction.objects.filter(
                    user=user,
                    transaction_type__in=['earning', 'payout', 'tip']
                ).order_by('-created_at')[:10]
                
                for trans in transactions:
                    earnings_transactions.append({
                        'id': trans.reference,
                        'type': trans.transaction_type,
                        'description': trans.description,
                        'amount': float(trans.amount) if trans.is_credit else -float(trans.amount),
                        'date': trans.created_at.strftime('%Y-%m-%d'),
                        'status': trans.status
                    })
                
                # Get pending payouts
                pending_payouts = PayoutRequest.objects.filter(
                    provider=user,
                    status__in=['pending', 'processing']
                ).aggregate(
                    total=Sum('amount')
                )
                
                # Calculate average per job for this week
                avg_per_job = 0
                if current_week_earnings['total_jobs'] and current_week_earnings['total_jobs'] > 0:
                    avg_per_job = float(current_week_earnings['total_net'] or 0) / current_week_earnings['total_jobs']
                
                weekly_earnings = float(current_week_earnings['total_net'] or 0)
                
                # Only update if values have changed to avoid unnecessary DB writes
                if (provider_profile.total_earnings != weekly_earnings or
                    provider_profile.jobs_completed != jobs_completed or
                    provider_profile.jobs_total != total_accepted):
                    provider_profile.total_earnings = weekly_earnings
                    provider_profile.save(update_fields=['jobs_completed', 'jobs_total', 'completion_rate', 'total_earnings'])
                
                # Get job lists for job queue tab
                worker = getattr(user, 'worker_profile', None)
                if worker:
                    upcoming_jobs = worker.bookings.filter(
                        status__in=['accepted']
                    ).select_related('customer', 'service_task__category').order_by('start_at')
                    
                    in_progress_jobs = worker.bookings.filter(
                        status='in_progress'
                    ).select_related('customer', 'service_task__category').order_by('-updated_at')
                    
                    completed_jobs = worker.bookings.filter(
                        status='completed'
                    ).select_related('customer', 'service_task__category').prefetch_related('rating').order_by('-updated_at')[:10]  # Show last 10
                else:
                    upcoming_jobs = Booking.objects.none()
                    in_progress_jobs = Booking.objects.none()
                    completed_jobs = Booking.objects.none()
                
                provider_context['upcoming_jobs'] = upcoming_jobs
                provider_context['in_progress_jobs'] = in_progress_jobs
                provider_context['completed_jobs'] = completed_jobs
                provider_context['upcoming_jobs_count'] = upcoming_jobs.count()
                provider_context['in_progress_jobs_count'] = in_progress_jobs.count()
                provider_context['completed_jobs_count'] = worker.bookings.filter(status='completed').count() if worker else 0
                
                # Get working hours and service areas
                import json
                
                try:
                    # Initialize working hours if empty
                    if not provider_profile.working_hours:
                        provider_profile.working_hours = provider_profile.get_default_working_hours()
                        provider_profile.save(update_fields=['working_hours'])
                    
                    # Initialize service areas if empty
                    if not provider_profile.service_areas:
                        provider_profile.service_areas = provider_profile.get_default_service_areas()
                        provider_profile.save(update_fields=['service_areas'])
                    
                    # Pass data for availability and service area tabs
                    provider_context['working_hours'] = provider_profile.working_hours
                    provider_context['service_areas'] = provider_profile.service_areas
                    provider_context['time_off_requests'] = []  # Empty for now, can be implemented later
                    
                    # Calculate statistics for service areas
                    active_areas = [area for area in provider_profile.service_areas if area.get('enabled', False)]
                    provider_context['active_areas_count'] = len(active_areas)
                    
                    # Calculate average surcharge
                    if active_areas:
                        total_surcharge = sum(area.get('surcharge', 0) for area in active_areas)
                        provider_context['avg_surcharge'] = total_surcharge / len(active_areas)
                    else:
                        provider_context['avg_surcharge'] = 0
                    
                    # Get recent distance requests
                    recent_distance_requests = DistanceRequest.objects.filter(
                        provider=user
                    ).select_related('booking').order_by('-created_at')[:5]
                    
                    provider_context['recent_distance_requests'] = recent_distance_requests
                    
                    # Calculate population covered based on active areas
                    # This is a simplified calculation - in production you'd use actual demographic data
                    population_per_area = {
                        'Luanda Centro': 250000,
                        'Maianga': 180000,
                        'Ingombota': 150000,
                        'Rangel': 200000,
                        'Cazenga': 170000,
                        'Viana': 220000,
                        'Kilamba': 190000,
                        'Talatona': 160000,
                    }
                    
                    total_population = 0
                    for area in active_areas:
                        total_population += population_per_area.get(area.get('name', ''), 100000)
                    
                    # Format population for display
                    if total_population >= 1000000:
                        population_covered = f"{total_population / 1000000:.1f}M"
                    else:
                        population_covered = f"{total_population / 1000:.0f}k"
                    
                    provider_context['population_covered'] = population_covered
                
                    # Get provider documents for KYC tab
                    try:
                        from accounts.models import ProviderDocument, ProviderContract
                        provider_documents = ProviderDocument.objects.filter(
                            provider=provider_profile
                        ).order_by('document_type')
                        
                        provider_contracts = ProviderContract.objects.filter(
                            provider=provider_profile
                        ).order_by('-created_at')
                        
                        provider_context['provider_documents'] = provider_documents
                        provider_context['provider_contracts'] = provider_contracts
                        
                        # Get missing required documents
                        existing_types = list(provider_documents.values_list('document_type', flat=True))
                        required_types = ['national_id', 'proof_address', 'bank_statement', 'criminal_record']
                        missing_documents = []
                        
                        for doc_type in required_types:
                            if doc_type not in existing_types:
                                missing_documents.append({
                                    'document_type': doc_type,
                                    'display_name': dict(ProviderDocument.DOCUMENT_TYPES).get(doc_type, doc_type)
                                })
                        
                        provider_context['missing_documents'] = missing_documents
                    except:
                        provider_context['provider_documents'] = []
                        provider_context['provider_contracts'] = []
                        provider_context['missing_documents'] = []
                except Exception as e:
                    # Fallback for when database columns don't exist yet
                    print(f"Warning: Provider profile fields not available: {e}")
                    provider_context['working_hours'] = provider_profile.get_default_working_hours()
                    provider_context['service_areas'] = provider_profile.get_default_service_areas()
                    provider_context['time_off_requests'] = []
                    provider_context['active_areas_count'] = 4
                    provider_context['avg_surcharge'] = 7.5
                    provider_context['recent_distance_requests'] = []
                    provider_context['population_covered'] = '850k'
                    provider_context['provider_documents'] = []
                    provider_context['provider_contracts'] = []
                    provider_context['missing_documents'] = []
                
                # Add earnings data to context
                provider_context['wallet'] = {
                    'available_balance': float(wallet.available_balance),
                    'pending_balance': float(wallet.pending_balance),
                    'total_balance': float(wallet.total_balance)
                }
                provider_context['pending_payouts'] = float(pending_payouts['total'] or 0)
                provider_context['current_week_jobs'] = current_week_earnings['total_jobs'] or 0
                provider_context['current_week_earnings'] = weekly_earnings
                provider_context['avg_per_job'] = avg_per_job
                provider_context['weekly_earnings_data'] = json.dumps(weekly_earnings_data)
                provider_context['daily_earnings'] = json.dumps(daily_earnings)
                provider_context['earnings_chart_labels'] = json.dumps(days_of_week)
                provider_context['earnings_transactions'] = json.dumps(earnings_transactions if earnings_transactions else [])
                provider_context['total_week_earnings'] = sum(daily_earnings)
                
                # Calculate week-over-week growth
                if len(weekly_earnings_data) >= 2:
                    last_week = weekly_earnings_data[1]['amount'] if weekly_earnings_data[1]['amount'] > 0 else 1
                    this_week = weekly_earnings_data[0]['amount']
                    growth_percentage = ((this_week - last_week) / last_week) * 100
                else:
                    growth_percentage = 0
                    
                provider_context['earnings_growth'] = round(growth_percentage, 1)
        
        # Get recent transactions for all tabs that need them
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
        
        context.update({
            'title': 'Dashboard - Zela',
            'dashboard_stats': dashboard_stats,
            'dashboard_data': dashboard_data,  # Added for template compatibility
            'unread_notifications': unread_notifications,
            'all_notifications': all_notifications,  # Add all notifications
            'grouped_notifications': dict(grouped_notifications),  # Add grouped notifications
            'is_provider': user.role == 'provider',
            'recent_transactions': recent_transactions,  # Added for all tabs
            'profile': profile,
            'settings': settings,  # Add user settings
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
            **provider_context  # Add provider-specific context
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
        
        if user.role == 'admin':
            # Admins see all bookings
            queryset = Booking.objects.all()
        elif user.role == 'customer':
            queryset = user.bookings.all()
        else:  # provider
            queryset = user.jobs.all()
        
        # Filter by status
        status = self.request.GET.get('status', '').strip()
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related('customer', 'worker__user', 'service_task').order_by('-created_at')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for bookings."""
        context = super().get_context_data(**kwargs)
        
        # Get status counts
        user = self.request.user
        if user.role == 'admin':
            base_query = Booking.objects
        elif user.role == 'customer':
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
            if booking.worker and booking.worker.user != self.request.user:
                raise PermissionError("You don't have permission to modify this booking.")
        
        return booking
    
    def form_valid(self, form):
        """Handle valid booking update."""
        booking = form.save()
        
        # Create notification for the other party
        if self.request.user.role == 'customer':
            if booking.worker:
                Notification.objects.create(
                    user=booking.worker.user,
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
        
        # Update User model fields to keep them in sync
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
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
        if booking.worker and hasattr(booking.worker.user, 'provider'):
            provider_profile = booking.worker.user.provider
            
            # Calculate new average
            ratings = Rating.objects.filter(booking__worker=booking.worker)
            avg_rating = ratings.aggregate(Avg('score'))['score__avg']
            
            provider_profile.rating_average = round(avg_rating, 2)
            provider_profile.rating_count = ratings.count()
            provider_profile.save()
            
            # Create notification for provider
            Notification.objects.create(
                user=booking.worker.user,
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


class ProviderRatingsPartial(LoginRequiredMixin, TemplateView):
    """Provider ratings and reviews tab partial."""
    
    template_name = 'website/components/dashboard/partials/ratings-content.html'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add ratings context data."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Ensure user is a provider
        if user.role != 'provider':
            context['error'] = "Only providers can view ratings."
            return context
        
        # Get provider profile
        provider_profile = getattr(user, 'provider', None)
        if not provider_profile:
            context['error'] = "Provider profile not found."
            return context
        
        # Get all ratings for this provider
        ratings = Rating.objects.filter(
            booking__provider=user
        ).select_related('booking', 'booking__customer').order_by('-created')
        
        # Calculate rating breakdown with percentages
        rating_breakdown = {}
        total_count = ratings.count()
        for i in range(1, 6):
            count = ratings.filter(score=i).count()
            percentage = round((count / total_count * 100)) if total_count > 0 else 0
            rating_breakdown[i] = {
                'count': count,
                'percentage': percentage
            }
        
        # Get stats for the current month
        now = timezone.now()
        month_start = datetime(now.year, now.month, 1)
        month_ratings = ratings.filter(created__gte=month_start)
        
        # Calculate response stats (placeholder - you might want to track actual replies)
        total_with_comments = ratings.exclude(comment='').count()
        
        context.update({
            'provider_profile': provider_profile,
            'overall_rating': provider_profile.rating_average or 0,
            'total_reviews': provider_profile.rating_count or 0,
            'rating_breakdown': rating_breakdown,
            'ratings': ratings[:10],  # Show first 10, implement pagination later
            'reviews_this_month': month_ratings.count(),
            'positive_reviews_percentage': self._calculate_positive_percentage(ratings),
            'total_with_comments': total_with_comments,
            'has_ratings': ratings.exists(),
        })
        
        return context
    
    def _calculate_positive_percentage(self, ratings):
        """Calculate percentage of positive reviews (4 stars and above)."""
        if not ratings.exists():
            return 0
        
        positive_count = ratings.filter(score__gte=4).count()
        total_count = ratings.count()
        return round((positive_count / total_count) * 100) if total_count > 0 else 0


@require_http_methods(["POST"])
@login_required
def add_payment_method(request):
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


@login_required
@require_http_methods(["POST"])
def update_provider_availability(request):
    """Update provider availability status."""
    if request.user.role != 'provider':
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        
        # Get provider profile
        provider_profile = request.user.provider
        
        # Update availability fields
        fields_to_update = []
        
        if 'is_available' in data:
            provider_profile.is_available = data['is_available']
            fields_to_update.append('is_available')
        
        if 'accepts_same_day' in data:
            provider_profile.accepts_same_day = data['accepts_same_day']
            fields_to_update.append('accepts_same_day')
        
        # Save only the updated fields
        if fields_to_update:
            provider_profile.save(update_fields=fields_to_update)
        
        # Refresh from database to ensure we have the latest values
        provider_profile.refresh_from_db()
        
        return JsonResponse({
            'ok': 1,
            'message': 'Availability updated successfully',
            'is_available': provider_profile.is_available,
            'accepts_same_day': provider_profile.accepts_same_day
        })
        
    except Exception as e:
        return JsonResponse({
            'ok': 0,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def update_provider_schedule(request):
    """Update provider working hours schedule."""
    if request.user.role != 'provider':
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        provider_profile = request.user.provider
        
        # Update working hours
        if 'working_hours' in data:
            provider_profile.working_hours = data['working_hours']
            provider_profile.save()
        
        return JsonResponse({
            'ok': 1,
            'message': 'Schedule updated successfully',
            'working_hours': provider_profile.working_hours
        })
        
    except Exception as e:
        return JsonResponse({
            'ok': 0,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def update_service_areas(request):
    """Update provider service areas."""
    if request.user.role != 'provider':
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        provider_profile = request.user.provider
        
        # Update service areas
        if 'service_areas' in data:
            provider_profile.service_areas = data['service_areas']
        
        # Update travel settings
        if 'max_travel_distance' in data:
            provider_profile.max_travel_distance = data['max_travel_distance']
        
        if 'preferred_radius' in data:
            provider_profile.preferred_radius = data['preferred_radius']
        
        if 'include_traffic_time' in data:
            provider_profile.include_traffic_time = data['include_traffic_time']
        
        if 'avoid_tolls' in data:
            provider_profile.avoid_tolls = data['avoid_tolls']
        
        if 'prefer_main_roads' in data:
            provider_profile.prefer_main_roads = data['prefer_main_roads']
        
        provider_profile.save()
        
        return JsonResponse({
            'ok': 1,
            'message': 'Service areas updated successfully',
            'service_areas': provider_profile.service_areas,
            'travel_settings': {
                'max_travel_distance': provider_profile.max_travel_distance,
                'preferred_radius': provider_profile.preferred_radius,
                'include_traffic_time': provider_profile.include_traffic_time,
                'avoid_tolls': provider_profile.avoid_tolls,
                'prefer_main_roads': provider_profile.prefer_main_roads
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'ok': 0,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["POST"])
def upload_document(request):
    """Handle document upload for providers."""
    if request.user.role != 'provider':
        return JsonResponse({'ok': 0, 'message': 'Only providers can upload documents'}, status=403)
    
    try:
        from accounts.models import ProviderDocument
        provider_profile = request.user.provider
        document_type = request.POST.get('document_type')
        file = request.FILES.get('file')
        
        if not file:
            return JsonResponse({'ok': 0, 'message': 'No file provided'}, status=400)
        
        # Validate file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            return JsonResponse({'ok': 0, 'message': 'File size must be less than 10MB'}, status=400)
        
        # Check if document of this type already exists
        existing_doc = ProviderDocument.objects.filter(
            provider=provider_profile,
            document_type=document_type
        ).first()
        
        if existing_doc:
            # Update existing document
            existing_doc.file = file
            existing_doc.file_name = file.name
            existing_doc.status = 'pending'  # Reset to pending for re-verification
            existing_doc.uploaded_at = timezone.now()
            existing_doc.save()
            document = existing_doc
        else:
            # Create new document
            document = ProviderDocument.objects.create(
                provider=provider_profile,
                document_type=document_type,
                file=file,
                file_name=file.name,
                status='pending',
                is_required=document_type in ['national_id', 'proof_address', 'bank_statement', 'criminal_record']
            )
        
        # Create notification for admin
        admin_users = User.objects.filter(role='admin', is_active=True)
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                title="New Document Uploaded",
                message=f"{provider_profile.user.get_full_name()} uploaded {document.get_document_type_display()}",
                notification_type="document",
                link=f"/admin/accounts/providerdocument/{document.id}/change/"
            )
        
        return JsonResponse({
            'ok': 1,
            'message': 'Document uploaded successfully. It will be reviewed soon.',
            'document_id': document.id
        })
        
    except Exception as e:
        return JsonResponse({
            'ok': 0,
            'message': f'Error uploading document: {str(e)}'
        }, status=400)


@login_required
@require_http_methods(["POST"])
def update_profile(request):
    """Update user profile information."""
    try:
        user = request.user
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Update profile fields
        profile.first_name = request.POST.get('first_name', '')
        profile.last_name = request.POST.get('last_name', '')
        profile.address = request.POST.get('address', '')
        profile.national_id_number = request.POST.get('national_id_number', '')
        
        # Handle date of birth
        dob_str = request.POST.get('date_of_birth', '')
        if dob_str:
            try:
                profile.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            # Validate file size (5MB max)
            if profile_picture.size > 5 * 1024 * 1024:
                return JsonResponse({
                    'ok': False,
                    'message': 'Profile picture must be less than 5MB'
                })
            profile.profile_picture = profile_picture
        
        profile.save()
        
        # Update user fields to keep them in sync
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone = request.POST.get('phone', '')
        user.save()
        
        return JsonResponse({
            'ok': True,
            'message': 'Profile updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'ok': False,
            'message': f'Error updating profile: {str(e)}'
        }, status=400)


@login_required
@require_http_methods(["POST"])
def update_settings(request):
    """Update user settings."""
    try:
        import json
        data = json.loads(request.body)
        
        user = request.user
        settings = UserSettings.get_or_create_for_user(user)
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Update notification settings
        if 'notificationSettings' in data:
            ns = data['notificationSettings']
            settings.job_alerts = ns.get('jobAlerts', settings.job_alerts)
            settings.payment_alerts = ns.get('paymentAlerts', settings.payment_alerts)
            settings.weekly_reports = ns.get('weeklyReports', settings.weekly_reports)
            settings.push_notifications = ns.get('pushNotifications', settings.push_notifications)
            settings.system_updates = ns.get('systemUpdates', settings.system_updates)
            
            # Update profile notification settings
            profile.email_notifications = ns.get('emailNotifications', profile.email_notifications)
            profile.sms_notifications = ns.get('smsNotifications', profile.sms_notifications)
            profile.marketing_communications = ns.get('marketingEmails', profile.marketing_communications)
        
        # Update privacy settings
        if 'privacySettings' in data:
            ps = data['privacySettings']
            settings.profile_visibility = ps.get('profileVisibility', settings.profile_visibility)
            settings.share_location = ps.get('shareLocation', settings.share_location)
            settings.share_statistics = ps.get('shareStatistics', settings.share_statistics)
            settings.allow_reviews = ps.get('allowReviews', settings.allow_reviews)
            settings.data_collection = ps.get('dataCollection', settings.data_collection)
        
        # Update preferences
        if 'preferences' in data:
            prefs = data['preferences']
            settings.language = prefs.get('language', settings.language)
            settings.timezone = prefs.get('timezone', settings.timezone)
            settings.currency = prefs.get('currency', settings.currency)
            settings.theme = prefs.get('theme', settings.theme)
            settings.map_view = prefs.get('mapView', settings.map_view)
        
        # Update work settings (provider only)
        if user.role == 'provider' and 'workSettings' in data:
            ws = data['workSettings']
            settings.auto_accept_jobs = ws.get('autoAcceptJobs', settings.auto_accept_jobs)
            settings.max_jobs_per_day = str(ws.get('maxJobsPerDay', settings.max_jobs_per_day))
            settings.preferred_job_types = ws.get('preferredJobTypes', settings.preferred_job_types)
            settings.minimum_job_value = ws.get('minimumJobValue', settings.minimum_job_value)
            settings.travel_radius = ws.get('travelRadius', settings.travel_radius)
        
        # Save both models
        settings.save()
        profile.save()
        
        return JsonResponse({
            'ok': 1,
            'message': 'Settings updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'ok': 0,
            'message': f'Error updating settings: {str(e)}'
        }, status=400)


@login_required
def booking_details_modal(request, booking_id):
    """Render booking details modal via HTMX or as standalone page."""
    try:
        # Get the booking, ensuring it belongs to the current user
        booking = get_object_or_404(
            Booking.objects.select_related('worker__user__provider', 'service_task'), 
            id=booking_id,
            customer=request.user
        )
        
        # Check if this is an HTMX request
        is_htmx = request.headers.get('HX-Request', 'false') == 'true'
        
        context = {
            'booking': booking,
            'is_htmx_request': is_htmx,
            'title': f'Detalhes da Reserva #{booking.id} - Zela'
        }
        
        return render(
            request, 
            'website/components/dashboard/modals/booking-details.html', 
            context
        )
        
    except Booking.DoesNotExist:
        return HttpResponse("Reserva não encontrada", status=404)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    try:
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user=request.user
        )
        notification.mark_as_read()
        
        return JsonResponse({
            'ok': 1,
            'message': 'Notification marked as read',
            'unread_count': request.user.notifications.filter(is_read=False).count()
        })
    except Exception as e:
        return JsonResponse({
            'ok': 0,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user."""
    try:
        request.user.notifications.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return JsonResponse({
            'ok': 1,
            'message': 'All notifications marked as read',
            'unread_count': 0
        })
    except Exception as e:
        return JsonResponse({
            'ok': 0,
            'error': str(e)
        }, status=400)