# Import all views from the views package
from .views.public import HomeView, ContactFormView, handler404, handler500
from .views.services import ServiceCatalogueView, ServiceDetailPartial, ServiceTaskDetailPartial, ServiceListView
from .views.blog import BlogIndexView, BlogPostView
from .views.help_center import HelpCenterView, HelpCenterSearch, HelpArticleView
from .views.auth import RegisterWizardView, SignInView, SignOutView
from .views.dashboard import (
    DashboardShellView, BookingListPartial, BookingUpdatePartial,
    ProfileUpdateView, RatingCreatePartial
)
from .views.providers import ProviderLandingView, ProviderApplicationWizard

# Keep the existing simple views for backwards compatibility
from django.shortcuts import render
from django.views.generic import TemplateView
from pricing.models import PricingConfig
from cms.models import Page


class AboutView(TemplateView):
    """About page view."""
    template_name = 'website/components/page-about/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'About Zela - Attention and care for your home',
            'meta_description': 'Learn about Zela\'s mission to provide reliable home services in Angola.',
        })
        return context


class PricingView(TemplateView):
    """Pricing page view."""
    template_name = 'website/components/page-pricing/pricing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pricing = PricingConfig.get_instance()
        context.update({
            'title': 'Zela Pricing - Transparent and Fair',
            'meta_description': 'View our transparent pricing for home services in Angola.',
            'pricing': pricing,
        })
        return context


class FlatPageView(TemplateView):
    """Generic view for CMS pages."""
    
    def get_object(self):
        """Get the page by slug."""
        from django.shortcuts import get_object_or_404
        return get_object_or_404(Page, slug=self.kwargs['slug'], is_visible=True)
    
    def get_template_names(self):
        """Return template based on page slug."""
        page = self.get_object()
        
        # Map specific slugs to templates
        template_map = {
            'privacy-policy': 'website/components/page-privacy-policy/privacy-policy.html',
            'terms-of-service': 'website/components/page-terms-of-service/terms-of-service.html',
            'cookie-policy': 'website/components/page-cookie-policy/cookie-policy.html',
            'accessibility-statement': 'website/components/page-accessibility-statement/accessibility-statement.html',
            'refund-policy': 'website/components/page-refund-policy/refund-policy.html',
        }
        
        return [template_map.get(page.slug, 'website/components/page-generic.html')]
    
    def get_context_data(self, **kwargs):
        """Add page context."""
        context = super().get_context_data(**kwargs)
        page = self.get_object()
        
        context.update({
            'page': page,
            'title': f'{page.title} - Zela',
            'meta_description': page.meta_description or page.title,
        })
        
        return context


# Legacy function-based views for backwards compatibility
def home(request):
    return HomeView.as_view()(request)

def about(request):
    return AboutView.as_view()(request)

def blog(request):
    return BlogIndexView.as_view()(request)

def contact(request):
    return ContactFormView.as_view()(request)

def pricing(request):
    return PricingView.as_view()(request)

def services(request):
    return ServiceCatalogueView.as_view()(request)

def register(request):
    return RegisterWizardView.as_view()(request)

def sign_in(request):
    return SignInView.as_view()(request)

def dashboard(request):
    return DashboardShellView.as_view()(request)

def privacy_policy(request):
    return FlatPageView.as_view()(request, slug='privacy-policy')

def terms_of_service(request):
    return FlatPageView.as_view()(request, slug='terms-of-service')

def cookie_policy(request):
    return FlatPageView.as_view()(request, slug='cookie-policy')

def accessibility_statement(request):
    return FlatPageView.as_view()(request, slug='accessibility-statement')

def refund_policy(request):
    return FlatPageView.as_view()(request, slug='refund-policy')

def help_center(request):
    return HelpCenterView.as_view()(request)

def blog_post(request):
    # This would need a slug parameter
    return render(request, 'website/components/page-blog-post/blog-post.html', {
        'title': 'Blog Post - Zela Blog',
    })
