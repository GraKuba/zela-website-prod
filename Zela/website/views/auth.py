from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import FormView, View
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from formtools.wizard.views import SessionWizardView
from django.core.files.storage import default_storage
from django.conf import settings
from django import forms
from accounts.models import User, ProviderProfile
from typing import Dict, Any


class RegisterForm(forms.Form):
    """User registration form."""
    
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
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Phone Number (Optional)'
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
    role = forms.ChoiceField(
        choices=[('customer', 'Customer'), ('provider', 'Service Provider')],
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio'
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


class ProviderApplicationForm(forms.Form):
    """Provider application form for the wizard."""
    
    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Tell us about yourself and your experience...',
            'rows': 4
        })
    )
    skills = forms.MultipleChoiceField(
        choices=[
            ('cleaning', 'House Cleaning'),
            ('deep_cleaning', 'Deep Cleaning'),
            ('laundry', 'Laundry'),
            ('cooking', 'Cooking'),
            ('gardening', 'Gardening'),
            ('maintenance', 'Home Maintenance'),
            ('childcare', 'Childcare'),
            ('eldercare', 'Elder Care'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox'
        })
    )
    service_area = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Service Area (e.g., Luanda, Talatona)'
        })
    )
    id_document = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )


class RegisterWizardView(SessionWizardView):
    """Multi-step registration wizard with Alpine.js progress bar."""
    
    template_name = 'website/components/auth-register/register.html'
    form_list = [RegisterForm, ProviderApplicationForm]
    file_storage = default_storage
    condition_dict = {'1': lambda wizard: wizard.get_cleaned_data_for_step('0') and wizard.get_cleaned_data_for_step('0').get('role') == 'provider'}
    
    def get_form_list(self):
        """Return form list based on user type."""
        return super().get_form_list()
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for the registration wizard."""
        context = super().get_context_data(**kwargs)
        
        context.update({
            'title': 'Create Your Free Zela Account - Sign Up',
            'meta_description': 'Join Zela today and start booking trusted home services.',
            'step_count': len(self.get_form_list()),
            'current_step': int(self.steps.current) + 1,
            'is_provider_registration': self.steps.current == '1',
        })
        
        return context
    
    def done(self, form_list, **kwargs):
        """Process completed registration."""
        form_data = self.get_all_cleaned_data()
        
        # Create user
        user = User.objects.create_user(
            username=form_data['email'],
            email=form_data['email'],
            password=form_data['password1'],
            first_name=form_data['first_name'],
            last_name=form_data['last_name'],
            phone=form_data.get('phone', ''),
            role=form_data['role']
        )
        
        # Create provider profile if needed
        if form_data['role'] == 'provider':
            ProviderProfile.objects.create(
                user=user,
                bio=form_data['bio'],
                skills=form_data['skills'],
                service_area=form_data['service_area'],
                id_document=form_data['id_document']
            )
        
        # Log the user in
        login(self.request, user)
        
        # Handle HTMX response
        if self.request.htmx:
            return JsonResponse({
                'ok': 1,
                'redirect': reverse_lazy('website:dashboard')
            })
        
        messages.success(self.request, 'Welcome to Zela! Your account has been created.')
        return redirect('website:dashboard')


class SignInForm(forms.Form):
    """Sign in form."""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Email Address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        })
    )


class SignInView(FormView):
    """Sign in view with HTMX support."""
    
    template_name = 'website/components/auth-login/sign-in.html'
    form_class = SignInForm
    success_url = reverse_lazy('website:dashboard')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for sign in page."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Sign In to Zela - Welcome Back',
            'meta_description': 'Sign in to your Zela account to manage bookings and services.',
        })
        return context
    
    def form_valid(self, form):
        """Handle valid sign in form."""
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        remember_me = form.cleaned_data['remember_me']
        
        # Authenticate user
        user = authenticate(
            self.request,
            username=email,
            password=password
        )
        
        if user is not None:
            if user.is_active:
                login(self.request, user)
                
                # Set session expiry
                if not remember_me:
                    self.request.session.set_expiry(0)  # Browser close
                
                # Handle HTMX response
                if self.request.htmx:
                    return JsonResponse({
                        'ok': 1,
                        'redirect': self.get_success_url()
                    })
                
                messages.success(self.request, f'Successfully logged in! Welcome back, {user.get_full_name() or user.username}.')
                return redirect(f"{self.get_success_url()}?login=success")
            else:
                form.add_error(None, 'Your account is inactive. Please contact support.')
        else:
            form.add_error(None, 'Invalid email or password.')
        
        return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid sign in form."""
        if self.request.htmx:
            return JsonResponse({
                'ok': 0,
                'errors': form.errors,
                'message': 'Please check your credentials and try again.'
            })
        
        return super().form_invalid(form)


class SignOutView(View):
    """Sign out view."""
    
    def get(self, request):
        """Handle sign out."""
        logout(request)
        messages.success(request, 'You have been signed out successfully.')
        return redirect('home')
    
    def post(self, request):
        """Handle HTMX sign out."""
        logout(request)
        
        if request.htmx:
            return JsonResponse({
                'ok': 1,
                'redirect': reverse_lazy('home')
            })
        
        return redirect('home') 