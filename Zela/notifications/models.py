from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Notification(models.Model):
    """User notifications for the bell icon dropdown."""
    
    TYPE_CHOICES = [
        ("booking", "Booking"),
        ("payment", "Payment"),
        ("rating", "Rating"),
        ("system", "System"),
        ("promotion", "Promotion"),
        ("reminder", "Reminder"),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User who should receive this notification"
    )
    title = models.CharField(
        max_length=120,
        help_text="Notification title"
    )
    message = models.CharField(
        max_length=255,
        help_text="Notification message"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="system",
        help_text="Type of notification"
    )
    link = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional link when notification is clicked"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the notification has been read"
    )
    is_important = models.BooleanField(
        default=False,
        help_text="Whether this is an important notification"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this notification expires (optional)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the notification was read"
    )
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def __str__(self) -> str:
        return f"{self.user.username}: {self.title}"
    
    @property
    def is_expired(self) -> bool:
        """Check if notification is expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def time_since_created(self) -> str:
        """Return human-readable time since creation."""
        now = timezone.now()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
