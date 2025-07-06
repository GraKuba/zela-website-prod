from django.shortcuts import render, redirect
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django import forms
from typing import Dict, Any


class ContactForm(forms.Form):
    """Contact form for customer inquiries."""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Your Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'your.email@example.com'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Your Phone Number (Optional)'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Your Message',
            'rows': 5
        })
    )


class HomeView(TemplateView):
    """Landing page view."""
    
    template_name = 'website/home.html'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for the home page."""
        context = super().get_context_data(**kwargs)
        
        # Import here to avoid circular imports
        from services.models import ServiceCategory
        from pricing.models import PricingConfig
        
        # Get featured service categories
        context['featured_services'] = ServiceCategory.objects.filter(
            is_active=True
        ).order_by('order')[:6]
        
        # Get pricing configuration
        context['pricing'] = PricingConfig.get_instance()
        
        context.update({
            'title': 'Zela - Professional Home Services in Angola',
            'meta_description': 'Book trusted home services in Angola. From cleaning to repairs, find verified professionals for your home.',
        })
        
        return context


class ContactFormView(FormView):
    """Contact form view with HTMX support."""
    
    template_name = 'website/components/page-contact/contact.html'
    form_class = ContactForm
    success_url = '/contact/'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for the contact page."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Contact Zela - Get in Touch',
            'meta_description': 'Get in touch with Zela for questions about our home services.',
        })
        return context
    
    def form_valid(self, form):
        """Handle valid form submission."""
        # Send email notification
        try:
            subject = f"Contact Form: {form.cleaned_data['subject']}"
            message = f"""
            New contact form submission:
            
            Name: {form.cleaned_data['name']}
            Email: {form.cleaned_data['email']}
            Phone: {form.cleaned_data.get('phone', 'Not provided')}
            Subject: {form.cleaned_data['subject']}
            
            Message:
            {form.cleaned_data['message']}
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],  # Send to ourselves
                fail_silently=False,
            )
            
            # Auto-reply to customer
            auto_reply = f"""
            Hi {form.cleaned_data['name']},
            
            Thank you for contacting Zela! We've received your message and will get back to you within 24 hours.
            
            Best regards,
            The Zela Team
            """
            
            send_mail(
                "Thank you for contacting Zela",
                auto_reply,
                settings.DEFAULT_FROM_EMAIL,
                [form.cleaned_data['email']],
                fail_silently=True,
            )
            
        except Exception as e:
            # Log error but don't fail the form submission
            pass
        
        # Handle HTMX request
        if self.request.htmx:
            return JsonResponse({
                'ok': 1,
                'message': 'Thank you for your message! We\'ll get back to you soon.',
                'title': 'Message Sent'
            })
        
        # Regular form submission
        messages.success(
            self.request,
            'Thank you for your message! We\'ll get back to you soon.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission."""
        if self.request.htmx:
            return JsonResponse({
                'ok': 0,
                'message': 'Please check your form and try again.',
                'errors': form.errors
            })
        
        return super().form_invalid(form)


# Error handlers
def handler404(request, exception):
    """Custom 404 error handler."""
    return render(
        request,
        'website/components/page-404/404.html',
        {'title': 'Page Not Found - Zela'},
        status=404
    )


def handler500(request):
    """Custom 500 error handler."""
    return render(
        request,
        'website/components/page-500/500.html',
        {'title': 'Server Error - Zela'},
        status=500
    ) 