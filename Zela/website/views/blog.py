from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.utils import timezone
from cms.models import BlogPost
from typing import Dict, Any


class BlogIndexView(ListView):
    """Blog index view with pagination and HTMX support."""
    
    model = BlogPost
    template_name = 'website/components/page-blog/blog.html'
    context_object_name = 'blog_posts'
    paginate_by = 9
    
    def get_queryset(self):
        """Return published blog posts with search and filtering."""
        queryset = BlogPost.objects.filter(
            is_visible=True,
            published__lte=timezone.now()
        ).select_related('author').order_by('-published')
        
        # Handle search
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(excerpt__icontains=search_query) |
                Q(body_md__icontains=search_query)
            )
        
        # Handle category filtering
        category = self.request.GET.get('category', '').strip()
        if category and category != 'all':
            queryset = queryset.filter(category=category)
        
        return queryset
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for the blog page."""
        context = super().get_context_data(**kwargs)
        
        # Get featured posts
        featured_posts = BlogPost.objects.filter(
            is_visible=True,
            is_featured=True,
            published__lte=timezone.now()
        ).order_by('-published')[:3]
        
        # Get categories with post counts
        categories = BlogPost.objects.filter(
            is_visible=True,
            published__lte=timezone.now()
        ).values_list('category', flat=True).distinct()
        
        # Get search query and selected category
        search_query = self.request.GET.get('search', '').strip()
        selected_category = self.request.GET.get('category', '').strip()
        
        context.update({
            'title': 'Zela Blog - Tips, news and household inspiration',
            'meta_description': 'Stay updated with the latest home service tips, news, and inspiration from Zela.',
            'featured_posts': featured_posts,
            'categories': categories,
            'search_query': search_query,
            'selected_category': selected_category,
            'total_posts': self.get_queryset().count(),
        })
        
        # Handle HTMX requests for grid updates
        if self.request.htmx:
            context['template_name'] = 'website/components/page-blog/article-grid.html'
        
        return context
    
    def get_template_names(self):
        """Return appropriate template based on request type."""
        if self.request.htmx:
            return ['website/components/page-blog/article-grid.html']
        return [self.template_name]


class BlogPostView(DetailView):
    """Individual blog post detail view."""
    
    model = BlogPost
    template_name = 'website/components/page-blog-post/blog-post.html'
    context_object_name = 'blog_post'
    
    def get_object(self):
        """Get blog post by slug, ensuring it's published."""
        return get_object_or_404(
            BlogPost,
            slug=self.kwargs['slug'],
            is_visible=True,
            published__lte=timezone.now()
        )
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add context data for the blog post page."""
        context = super().get_context_data(**kwargs)
        
        blog_post = self.get_object()
        
        # Get related posts from the same category
        related_posts = BlogPost.objects.filter(
            category=blog_post.category,
            is_visible=True,
            published__lte=timezone.now()
        ).exclude(pk=blog_post.pk).order_by('-published')[:3]
        
        # Get next/previous posts
        next_post = BlogPost.objects.filter(
            is_visible=True,
            published__lte=timezone.now(),
            published__gt=blog_post.published
        ).order_by('published').first()
        
        previous_post = BlogPost.objects.filter(
            is_visible=True,
            published__lte=timezone.now(),
            published__lt=blog_post.published
        ).order_by('-published').first()
        
        context.update({
            'title': f'{blog_post.title} - Zela Blog',
            'meta_description': blog_post.excerpt,
            'related_posts': related_posts,
            'next_post': next_post,
            'previous_post': previous_post,
            # For structured data
            'published_date': blog_post.published.isoformat(),
            'modified_date': blog_post.updated_at.isoformat(),
            'author_name': blog_post.author.get_full_name() if blog_post.author else 'Zela Team',
        })
        
        return context 