from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from formtools.wizard.views import SessionWizardView
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.core.files.storage import default_storage
from django import forms
from accounts.models import User, ProviderProfile
from pricing.models import PricingConfig
from typing import Dict, Any


class ProviderLandingView(TemplateView):
    """Provider landing page with marketing pitch."""
    
    template_name = 'website/components/page-providers/providers-landing.html'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for provider landing page."""
        context = super().get_context_data(**kwargs)
        
        # Get pricing configuration
        pricing = PricingConfig.get_instance()
        
        # Calculate potential earnings
        potential_earnings = {
            'per_hour': pricing.hourly_clean_base,
            'per_day': pricing.hourly_clean_base * 8,  # 8 hours
            'per_week': pricing.hourly_clean_base * 8 * 5,  # 5 days
            'per_month': pricing.hourly_clean_base * 8 * 5 * 4,  # 4 weeks
        }
        
        # After commission
        commission_rate = float(pricing.provider_commission_rate)
        net_earnings = {
            key: int(value * (1 - commission_rate))
            for key, value in potential_earnings.items()
        }
        
        context.update({
            'title': 'Become a Zela Provider - Earn Money with Your Skills',
            'meta_description': 'Join Zela as a service provider and earn money using your skills. Flexible work, fair pay, and professional growth.',
            'pricing': pricing,
            'potential_earnings': potential_earnings,
            'net_earnings': net_earnings,
            'commission_percentage': int(commission_rate * 100),
        })
        
        return context


class ProviderBasicInfoForm(forms.Form):
    """Basic provider information form."""
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Email Address'
        })
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Phone Number'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Confirm Password'
        })
    )
    
    def clean_email(self):
        """Validate email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def clean_password2(self):
        """Validate passwords match."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2


class ProviderSkillsForm(forms.Form):
    """Provider skills and experience form."""
    
    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Tell us about yourself, your experience, and why you want to join Zela...',
            'rows': 5
        })
    )
    skills = forms.MultipleChoiceField(
        choices=[
            ('house_cleaning', 'House Cleaning'),
            ('deep_cleaning', 'Deep Cleaning'),
            ('office_cleaning', 'Office Cleaning'),
            ('laundry', 'Laundry & Ironing'),
            ('cooking', 'Cooking'),
            ('meal_prep', 'Meal Preparation'),
            ('gardening', 'Gardening'),
            ('landscaping', 'Landscaping'),
            ('home_maintenance', 'Home Maintenance'),
            ('plumbing', 'Plumbing'),
            ('electrical', 'Electrical Work'),
            ('painting', 'Painting'),
            ('childcare', 'Childcare'),
            ('eldercare', 'Elder Care'),
            ('pet_care', 'Pet Care'),
            ('tutoring', 'Tutoring'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox'
        })
    )
    experience_years = forms.ChoiceField(
        choices=[
            ('less_than_1', 'Less than 1 year'),
            ('1_to_3', '1-3 years'),
            ('3_to_5', '3-5 years'),
            ('5_to_10', '5-10 years'),
            ('more_than_10', 'More than 10 years'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio'
        })
    )
    service_area = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Service Area (e.g., Luanda, Talatona, Viana)'
        })
    )
    
    def clean_skills(self):
        """Validate at least one skill is selected."""
        skills = self.cleaned_data.get('skills', [])
        if not skills:
            raise forms.ValidationError("Please select at least one skill.")
        return skills


class ProviderDocumentsForm(forms.Form):
    """Provider documents and verification form."""
    
    id_document = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text="Upload a clear photo of your ID card, passport, or driver's license"
    )
    references = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'List any references (name, relationship, phone number) - Optional',
            'rows': 3
        })
    )
    background_check_consent = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        })
    )
    terms_agreement = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        })
    )
    
    def clean_background_check_consent(self):
        """Validate background check consent."""
        consent = self.cleaned_data.get('background_check_consent')
        if not consent:
            raise forms.ValidationError("Background check consent is required.")
        return consent
    
    def clean_terms_agreement(self):
        """Validate terms agreement."""
        agreement = self.cleaned_data.get('terms_agreement')
        if not agreement:
            raise forms.ValidationError("You must agree to the terms and conditions.")
        return agreement


class ProviderApplicationWizard(SessionWizardView):
    """Provider application wizard - multi-step form."""
    
    template_name = 'website/components/page-providers/provider-application.html'
    form_list = [
        ('basic_info', ProviderBasicInfoForm),
        ('skills', ProviderSkillsForm),
        ('documents', ProviderDocumentsForm),
    ]
    file_storage = default_storage
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for provider application wizard."""
        context = super().get_context_data(**kwargs)
        
        # Get current step info
        current_step = self.steps.current
        step_titles = {
            'basic_info': 'Basic Information',
            'skills': 'Skills & Experience',
            'documents': 'Documents & Verification',
        }
        
        context.update({
            'title': 'Apply to Become a Zela Provider',
            'meta_description': 'Apply to join Zela as a service provider and start earning money with your skills.',
            'step_count': len(self.get_form_list()),
            'current_step_number': list(self.get_form_list().keys()).index(current_step) + 1,
            'current_step_title': step_titles.get(current_step, 'Application'),
            'step_titles': step_titles,
        })
        
        return context
    
    def done(self, form_list, **kwargs):
        """Process completed provider application."""
        # Get all form data
        form_data = self.get_all_cleaned_data()
        
        # Create user account
        user = User.objects.create_user(
            username=form_data['email'],
            email=form_data['email'],
            password=form_data['password1'],
            first_name=form_data['first_name'],
            last_name=form_data['last_name'],
            phone=form_data['phone'],
            role='provider'
        )
        
        # Create provider profile
        provider_profile = ProviderProfile.objects.create(
            user=user,
            bio=form_data['bio'],
            skills=form_data['skills'],
            service_area=form_data['service_area'],
            id_document=form_data['id_document'],
            is_approved=False  # Requires manual approval
        )
        
        # Log the user in
        login(self.request, user)
        
        # Send welcome email (would implement this in production)
        # send_provider_welcome_email(user)
        
        # Handle HTMX response
        if self.request.htmx:
            return JsonResponse({
                'ok': 1,
                'redirect': reverse_lazy('dashboard'),
                'message': 'Application submitted successfully! We will review your application and get back to you within 2-3 business days.'
            })
        
        messages.success(
            self.request,
            'Application submitted successfully! We will review your application and get back to you within 2-3 business days.'
        )
        return redirect('dashboard')
    
    def get_form_kwargs(self, step):
        """Add additional kwargs to forms if needed."""
        kwargs = super().get_form_kwargs(step)
        return kwargs 