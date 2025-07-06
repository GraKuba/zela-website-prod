from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import BlogPost, HelpArticle, Page


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Blog post admin."""
    
    list_display = (
        'title', 'author', 'category', 'published_status', 
        'is_featured', 'reading_time', 'published'
    )
    list_filter = ('category', 'is_visible', 'is_featured', 'published', 'author')
    search_fields = ('title', 'excerpt', 'body_md')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published'
    ordering = ('-published',)
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'excerpt', 'body_md'),
        }),
        ('Media', {
            'fields': ('hero_image',),
        }),
        ('Publication', {
            'fields': ('author', 'category', 'published', 'is_visible', 'is_featured'),
        }),
        ('SEO', {
            'fields': ('reading_time',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def published_status(self, obj):
        """Display publication status."""
        now = timezone.now()
        
        if not obj.is_visible:
            return format_html('<span style="color: red;">Hidden</span>')
        elif obj.published > now:
            return format_html('<span style="color: orange;">Scheduled</span>')
        else:
            return format_html('<span style="color: green;">Published</span>')
    published_status.short_description = 'Status'
    
    actions = ['publish_posts', 'unpublish_posts', 'feature_posts', 'unfeature_posts']
    
    def publish_posts(self, request, queryset):
        """Publish selected posts."""
        updated = queryset.update(is_visible=True)
        self.message_user(request, f'{updated} posts published.')
    publish_posts.short_description = 'Publish selected posts'
    
    def unpublish_posts(self, request, queryset):
        """Unpublish selected posts."""
        updated = queryset.update(is_visible=False)
        self.message_user(request, f'{updated} posts unpublished.')
    unpublish_posts.short_description = 'Unpublish selected posts'
    
    def feature_posts(self, request, queryset):
        """Feature selected posts."""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} posts featured.')
    feature_posts.short_description = 'Feature selected posts'
    
    def unfeature_posts(self, request, queryset):
        """Unfeature selected posts."""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} posts unfeatured.')
    unfeature_posts.short_description = 'Unfeature selected posts'


@admin.register(HelpArticle)
class HelpArticleAdmin(admin.ModelAdmin):
    """Help article admin."""
    
    list_display = (
        'title', 'category', 'is_featured', 'is_visible', 
        'order', 'updated'
    )
    list_filter = ('category', 'is_featured', 'is_visible', 'updated')
    search_fields = ('title', 'body_md')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('category', 'order', 'title')
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'category', 'body_md'),
        }),
        ('Display Options', {
            'fields': ('is_featured', 'is_visible', 'order'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated')
    
    actions = ['feature_articles', 'unfeature_articles', 'show_articles', 'hide_articles']
    
    def feature_articles(self, request, queryset):
        """Feature selected articles."""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} articles featured.')
    feature_articles.short_description = 'Feature selected articles'
    
    def unfeature_articles(self, request, queryset):
        """Unfeature selected articles."""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} articles unfeatured.')
    unfeature_articles.short_description = 'Unfeature selected articles'
    
    def show_articles(self, request, queryset):
        """Show selected articles."""
        updated = queryset.update(is_visible=True)
        self.message_user(request, f'{updated} articles made visible.')
    show_articles.short_description = 'Show selected articles'
    
    def hide_articles(self, request, queryset):
        """Hide selected articles."""
        updated = queryset.update(is_visible=False)
        self.message_user(request, f'{updated} articles hidden.')
    hide_articles.short_description = 'Hide selected articles'


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Static page admin."""
    
    list_display = ('title', 'slug', 'is_visible', 'show_in_footer', 'updated')
    list_filter = ('is_visible', 'show_in_footer', 'updated')
    search_fields = ('title', 'slug', 'body_md')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('title',)
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'meta_description', 'body_md'),
        }),
        ('Display Options', {
            'fields': ('is_visible', 'show_in_footer'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated')
    
    actions = ['show_pages', 'hide_pages', 'add_to_footer', 'remove_from_footer']
    
    def show_pages(self, request, queryset):
        """Show selected pages."""
        updated = queryset.update(is_visible=True)
        self.message_user(request, f'{updated} pages made visible.')
    show_pages.short_description = 'Show selected pages'
    
    def hide_pages(self, request, queryset):
        """Hide selected pages."""
        updated = queryset.update(is_visible=False)
        self.message_user(request, f'{updated} pages hidden.')
    hide_pages.short_description = 'Hide selected pages'
    
    def add_to_footer(self, request, queryset):
        """Add selected pages to footer."""
        updated = queryset.update(show_in_footer=True)
        self.message_user(request, f'{updated} pages added to footer.')
    add_to_footer.short_description = 'Add to footer'
    
    def remove_from_footer(self, request, queryset):
        """Remove selected pages from footer."""
        updated = queryset.update(show_in_footer=False)
        self.message_user(request, f'{updated} pages removed from footer.')
    remove_from_footer.short_description = 'Remove from footer'
