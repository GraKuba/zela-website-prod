from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.db.models import Q
from cms.models import HelpArticle
from typing import Dict, Any


class HelpCenterView(TemplateView):
    """Help center main page with category tiles and search."""
    
    template_name = 'website/components/page-help-center/help-center.html'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for the help center page."""
        context = super().get_context_data(**kwargs)
        
        # Get featured articles
        featured_articles = HelpArticle.objects.filter(
            is_visible=True,
            is_featured=True
        ).order_by('order', 'title')[:6]
        
        # Get articles by category
        categories = {}
        for choice in HelpArticle.CATEGORY_CHOICES:
            category_key = choice[0]
            category_name = choice[1]
            
            articles = HelpArticle.objects.filter(
                category=category_key,
                is_visible=True
            ).order_by('order', 'title')[:5]  # Top 5 per category
            
            if articles:
                categories[category_key] = {
                    'name': category_name,
                    'articles': articles,
                    'count': HelpArticle.objects.filter(
                        category=category_key,
                        is_visible=True
                    ).count()
                }
        
        # Get total article count
        total_articles = HelpArticle.objects.filter(is_visible=True).count()
        
        context.update({
            'title': 'Help Center - Zela',
            'meta_description': 'Find answers to your questions about Zela services, bookings, and more.',
            'featured_articles': featured_articles,
            'categories': categories,
            'total_articles': total_articles,
        })
        
        return context


class HelpCenterSearch(ListView):
    """Help center search results (HTMX partial)."""
    
    model = HelpArticle
    template_name = 'website/components/page-help-center/search-results.html'
    context_object_name = 'articles'
    paginate_by = 10
    
    def get_queryset(self):
        """Return search results for help articles."""
        query = self.request.GET.get('q', '').strip()
        category = self.request.GET.get('category', '').strip()
        
        queryset = HelpArticle.objects.filter(is_visible=True)
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(body_md__icontains=query)
            )
        
        if category and category != 'all':
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('order', 'title')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for search results."""
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('q', '').strip()
        selected_category = self.request.GET.get('category', '').strip()
        
        context.update({
            'search_query': search_query,
            'selected_category': selected_category,
            'total_results': self.get_queryset().count(),
        })
        
        return context
    
    def get_template_names(self):
        """Return appropriate template based on request type."""
        if self.request.htmx:
            return ['website/components/page-help-center/search-results.html']
        return ['website/components/page-help-center/help-center.html']


class HelpArticleView(ListView):
    """Individual help article detail view."""
    
    model = HelpArticle
    template_name = 'website/components/page-help-center/article-detail.html'
    context_object_name = 'article'
    
    def get_object(self):
        """Get help article by slug."""
        from django.shortcuts import get_object_or_404
        return get_object_or_404(
            HelpArticle,
            slug=self.kwargs['slug'],
            is_visible=True
        )
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for the help article page."""
        context = super().get_context_data(**kwargs)
        
        article = self.get_object()
        
        # Get related articles from the same category
        related_articles = HelpArticle.objects.filter(
            category=article.category,
            is_visible=True
        ).exclude(pk=article.pk).order_by('order', 'title')[:5]
        
        # Get breadcrumb category name
        category_name = dict(HelpArticle.CATEGORY_CHOICES).get(article.category)
        
        context.update({
            'title': f'{article.title} - Help Center - Zela',
            'meta_description': article.body_md[:160] + '...' if len(article.body_md) > 160 else article.body_md,
            'article': article,
            'related_articles': related_articles,
            'category_name': category_name,
        })
        
        return context 