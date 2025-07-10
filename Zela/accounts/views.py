from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LogoutView
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.views.generic import FormView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django import forms
from .models import User
import json
import re


class RegistrationForm(forms.ModelForm):
    """Registration form for new users."""
    
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:outline-none transition-colors',
            'placeholder': 'Enter your full name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:outline-none transition-colors',
            'placeholder': 'Enter your email address'
        })
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:outline-none transition-colors',
            'placeholder': 'Enter your phone number'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:outline-none transition-colors',
            'placeholder': 'Create a secure password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-2 transition-colors',
            'placeholder': 'Confirm your password'
        })
    )
    address_line1 = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:outline-none transition-colors',
            'placeholder': 'Enter your street address'
        })
    )
    area = forms.CharField(
        max_length=100,
        widget=forms.Select(
            choices=[
                ('', 'Select your area'),
                ('city-centre', 'City Centre'),
                ('suburbs', 'Suburbs'),
                ('waterfront', 'Waterfront'),
                ('northern-suburbs', 'Northern Suburbs'),
                ('southern-suburbs', 'Southern Suburbs'),
            ],
            attrs={
                'class': 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:outline-none transition-colors'
            }
        )
    )
    referral_code = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:outline-none transition-colors',
            'placeholder': 'Enter referral code if you have one'
        })
    )
    marketing_opt_in = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'mr-3 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
        })
    )
    terms_consent = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'mr-3 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 mt-1'
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'phone']
    
    def clean_email(self):
        """Validate email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def clean_full_name(self):
        """Validate and split full name."""
        full_name = self.cleaned_data.get('full_name', '').strip()
        if not full_name:
            raise forms.ValidationError("Full name is required.")
        
        # Split into first and last name
        name_parts = full_name.split()
        if len(name_parts) < 2:
            raise forms.ValidationError("Please enter both first and last name.")
        
        return full_name
    
    def clean_password(self):
        """Validate password strength."""
        password = self.cleaned_data.get('password')
        if not password:
            return password
        
        # Check minimum length
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            raise forms.ValidationError("Password must contain at least one lowercase letter.")
        
        # Check for digit
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError("Password must contain at least one number.")
        
        # Check for special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError("Password must contain at least one special character.")
        
        return password
    
    def clean_confirm_password(self):
        """Validate passwords match."""
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        return confirm_password
    
    def clean_terms_consent(self):
        """Validate terms consent."""
        terms_consent = self.cleaned_data.get('terms_consent')
        if not terms_consent:
            raise forms.ValidationError("You must agree to the Terms of Service and Privacy Policy.")
        return terms_consent
    
    def save(self, commit=True):
        """Create user from form data."""
        # Split full name into first and last name
        full_name = self.cleaned_data['full_name']
        name_parts = full_name.split()
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:])
        
        # Create user
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=first_name,
            last_name=last_name,
            phone=self.cleaned_data['phone'],
            role='customer'
        )
        
        return user


class RegistrationView(FormView):
    """Registration view with HTMX support."""
    
    template_name = 'website/components/auth-register/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('website:dashboard')
    
    def get_context_data(self, **kwargs):
        """Add context data for registration page."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Create Your Free Zela Account - Sign Up',
            'meta_description': 'Join Zela today and start booking trusted home services.',
        })
        return context
    
    def form_valid(self, form):
        """Handle valid registration form."""
        try:
            # Create user
            user = form.save()
            
            # Log the user in
            login(self.request, user)
            
            # Handle HTMX response
            if self.request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': True,
                    'redirect': str(self.success_url)
                })
            
            messages.success(self.request, 'Welcome to Zela! Your account has been created.')
            return redirect(self.success_url)
            
        except Exception as e:
            if self.request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [str(e)]}
                })
            
            form.add_error(None, str(e))
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid registration form."""
        if self.request.headers.get('HX-Request'):
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
        
        return super().form_invalid(form)


def validate_password_strength(request):
    """AJAX endpoint to validate password strength in real-time."""
    if request.method == 'POST':
        password = request.POST.get('password', '')
        
        # Password strength checks
        checks = {
            'minLength': len(password) >= 8,
            'hasUpper': bool(re.search(r'[A-Z]', password)),
            'hasLower': bool(re.search(r'[a-z]', password)),
            'hasNumber': bool(re.search(r'[0-9]', password)),
            'hasSpecial': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
        }
        
        # Calculate strength
        met_requirements = sum(checks.values())
        if len(password) == 0:
            strength = 'weak'
        elif met_requirements == 5:
            strength = 'excellent'
        elif met_requirements >= 4:
            strength = 'strong'
        elif met_requirements >= 3:
            strength = 'fair'
        else:
            strength = 'weak'
        
        return JsonResponse({
            'checks': checks,
            'strength': strength
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


class ZelaLogoutView(LogoutView):
    """Custom logout view."""
    
    next_page = reverse_lazy('website:home')
    
    def dispatch(self, request, *args, **kwargs):
        """Handle logout redirect."""
        response = super().dispatch(request, *args, **kwargs)
        
        # Add success message
        messages.success(request, 'You have been successfully logged out.')
        
        return response
