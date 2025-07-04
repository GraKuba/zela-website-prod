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
        'title': 'Zela Pricing - Clear, Up-Front Pricing',
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
        'title': 'Welcome Back - Sign In to Zela',
    })

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
        'title': 'Refund & Satisfaction-Guarantee Policy - Zela',
    })


def help_center(request):
    return render(request, 'website/components/page-help-center/help-center.html', {
        'title': 'Help Center - Zela Support & Knowledge Base',
    })


def blog_post(request):
    return render(request, 'website/components/page-blog-post/blog-post.html', {
        'title': 'Blog Post - Zela Blog',
    })
