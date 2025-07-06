from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
import markdown

User = get_user_model()


class BlogPost(models.Model):
    """Blog posts for the website."""
    
    CATEGORY_CHOICES = [
        ("news", "News"),
        ("tips", "Tips & Tricks"),
        ("updates", "Updates"),
        ("guides", "Guides"),
        ("company", "Company"),
    ]
    
    title = models.CharField(
        max_length=180,
        help_text="Blog post title"
    )
    slug = models.SlugField(
        unique=True,
        help_text="URL-friendly version of the title"
    )
    excerpt = models.CharField(
        max_length=255,
        help_text="Brief description for previews"
    )
    body_md = models.TextField(
        help_text="Blog post content in Markdown format"
    )
    hero_image = models.ImageField(
        upload_to="blog/",
        help_text="Featured image for the blog post"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="news",
        help_text="Blog post category"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Author of the blog post"
    )
    published = models.DateTimeField(
        default=timezone.now,
        help_text="Publication date and time"
    )
    is_visible = models.BooleanField(
        default=True,
        help_text="Whether the post is visible to the public"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether to feature this post"
    )
    reading_time = models.PositiveIntegerField(
        default=5,
        help_text="Estimated reading time in minutes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return URL for blog post detail page."""
        return reverse('blog-post', kwargs={'slug': self.slug})
    
    @property
    def body_html(self) -> str:
        """Convert markdown to HTML."""
        return markdown.markdown(self.body_md, extensions=['codehilite', 'fenced_code'])
    
    @property
    def is_published(self) -> bool:
        """Check if post is published."""
        return self.is_visible and self.published <= timezone.now()
    
    def __str__(self) -> str:
        return self.title
    
    class Meta:
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'
        ordering = ['-published']


class HelpArticle(models.Model):
    """Help center articles."""
    
    CATEGORY_CHOICES = [
        ("getting_started", "Getting Started"),
        ("booking", "Booking Services"),
        ("payments", "Payments & Billing"),
        ("providers", "For Providers"),
        ("account", "Account Management"),
        ("troubleshooting", "Troubleshooting"),
        ("policies", "Policies"),
    ]
    
    category = models.CharField(
        max_length=60,
        choices=CATEGORY_CHOICES,
        help_text="Help article category"
    )
    title = models.CharField(
        max_length=160,
        help_text="Article title"
    )
    slug = models.SlugField(
        unique=True,
        help_text="URL-friendly version of the title"
    )
    body_md = models.TextField(
        help_text="Article content in Markdown format"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether to feature this article"
    )
    is_visible = models.BooleanField(
        default=True,
        help_text="Whether the article is visible"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within category"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return URL for help article detail page."""
        return reverse('help-article', kwargs={'slug': self.slug})
    
    @property
    def body_html(self) -> str:
        """Convert markdown to HTML."""
        return markdown.markdown(self.body_md, extensions=['codehilite', 'fenced_code'])
    
    def __str__(self) -> str:
        return self.title
    
    class Meta:
        verbose_name = 'Help Article'
        verbose_name_plural = 'Help Articles'
        ordering = ['category', 'order', 'title']


class Page(models.Model):
    """Static pages editable via admin (legal pages, etc.)."""
    
    slug = models.SlugField(
        unique=True,
        help_text="URL slug for the page"
    )
    title = models.CharField(
        max_length=120,
        help_text="Page title"
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO meta description"
    )
    body_md = models.TextField(
        help_text="Page content in Markdown format"
    )
    is_visible = models.BooleanField(
        default=True,
        help_text="Whether the page is visible"
    )
    show_in_footer = models.BooleanField(
        default=False,
        help_text="Whether to show link in footer"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def get_absolute_url(self):
        """Return URL for page."""
        return reverse('page', kwargs={'slug': self.slug})
    
    @property
    def body_html(self) -> str:
        """Convert markdown to HTML."""
        return markdown.markdown(self.body_md, extensions=['codehilite', 'fenced_code'])
    
    def __str__(self) -> str:
        return self.title
    
    class Meta:
        verbose_name = 'Page'
        verbose_name_plural = 'Pages'
        ordering = ['title']
