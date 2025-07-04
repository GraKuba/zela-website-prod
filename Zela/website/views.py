from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return render(request, 'website/home.html', {
        'title': 'Zela - Home',
    })

def about(request):
    return render(request, 'website/components/page-about/about.html', {
        'title': 'About Zela - Attention and care for your home',
    })

def blog(request):
    return render(request, 'website/components/page-blog/blog.html', {
        'title': 'Zela Blog - Tips, news and household inspiration',
    })

def contact(request):
    return render(request, 'website/components/page-contact/contact.html', {
        'title': 'Contact Zela - Get in Touch',
    })

def pricing(request):
    return render(request, 'website/components/page-pricing/pricing.html', {
        'title': 'Zela Pricing - Transparent and Fair',
    })

def services(request):
    return render(request, 'website/components/page-services/services.html', {
        'title': 'Zela Services - Choose the Perfect Service',
    })

def register(request):
    return render(request, 'website/components/auth-register/register.html', {
        'title': 'Create Your Free Zela Account - Sign Up',
    })

def sign_in(request):
    return render(request, 'website/components/auth-login/sign-in.html', {
        'title': 'Sign In to Zela - Welcome Back',
    })

def dashboard(request):
    # Mock user data - in production this would come from the database
    context = {
        'title': 'Dashboard - Zela',
        'user': {
            'name': 'Maria Santos',
            'email': 'maria@example.com',
            'avatar': 'https://via.placeholder.com/64',
            'is_provider': False,  # This would be determined by user's role
            'provider_verified': False,
        },
        'dashboard_data': {
            'next_booking': {
                'date': '2024-01-15',
                'time': '10:00',
                'service': 'Deep Clean',
                'address': '123 Main Street, City Centre',
                'provider': 'Ana Silva',
                'countdown': '2 days, 3 hours'
            },
            'wallet_balance': 150.50,
            'referral_credits': 25.00,
            'total_bookings': 12,
            'upcoming_bookings': 3,
            'completed_bookings': 9,
            'notifications_count': 5,
            'unread_messages': 2,
        }
    }
    return render(request, 'website/components/dashboard/dashboard.html', context)

def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'website/components/page-404/404.html', status=404)


def handler500(request):
    """Custom 500 error handler"""
    return render(request, 'website/components/page-500/500.html', status=500)


def privacy_policy(request):
    return render(request, 'website/components/page-privacy-policy/privacy-policy.html', {
        'title': 'Privacy Policy - Zela',
    })


def terms_of_service(request):
    return render(request, 'website/components/page-terms-of-service/terms-of-service.html', {
        'title': 'Terms of Service - Zela',
    })


def cookie_policy(request):
    return render(request, 'website/components/page-cookie-policy/cookie-policy.html', {
        'title': 'Cookie Policy - Zela',
    })


def accessibility_statement(request):
    return render(request, 'website/components/page-accessibility-statement/accessibility-statement.html', {
        'title': 'Accessibility Statement - Zela',
    })


def refund_policy(request):
    return render(request, 'website/components/page-refund-policy/refund-policy.html', {
        'title': 'Refund Policy - Zela',
    })


def help_center(request):
    return render(request, 'website/components/page-help-center/help-center.html', {
        'title': 'Help Center - Zela',
    })


def blog_post(request):
    return render(request, 'website/components/page-blog-post/blog-post.html', {
        'title': 'Blog Post - Zela Blog',
    })
