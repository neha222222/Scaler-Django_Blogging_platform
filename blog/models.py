"""
Database Models for Blogging Platform
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.utils.text import slugify
import uuid


class User(AbstractUser):
    """
    Custom User Model with Role-Based Access Control
    Roles: ADMIN, AUTHOR, READER
    """
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        AUTHOR = 'AUTHOR', 'Author'
        READER = 'READER', 'Reader'
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.READER,
        help_text="User role for access control"
    )
    bio = models.TextField(blank=True, help_text="User biography")
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    class Meta:
        ordering = ['-date_joined']


class Tag(models.Model):
    """Tag Model for categorizing blog posts"""
    
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Post(models.Model):
    """
    Blog Post Model
    Status: DRAFT, PUBLISHED, ARCHIVED
    """
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'
        ARCHIVED = 'ARCHIVED', 'Archived'
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5)]
    )
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField(
        validators=[MinLengthValidator(50)]
    )
    excerpt = models.TextField(
        max_length=500,
        blank=True
    )
    
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    
    tags = models.ManyToManyField(Tag, related_name='posts', blank=True)
    
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    view_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        """Auto-generate unique slug and set published_at timestamp"""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        if self.status == self.Status.PUBLISHED and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def like_count(self):
        return self.likes.count()
    
    @property
    def comment_count(self):
        return self.comments.filter(is_approved=True).count()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-published_at']),
        ]


class Comment(models.Model):
    """
    Comment Model with Moderation Support
    Comments require approval before being visible to prevent spam
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField(validators=[MinLengthValidator(2)])
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
        ]


class Like(models.Model):
    """
    Like Model - Tracks post likes
    Unique constraint ensures one user can only like a post once
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"


class Share(models.Model):
    """Share Model - Tracks when posts are shared for analytics"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='share_records'
    )
    platform = models.CharField(
        max_length=50,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} shared {self.post.title}"
    
    class Meta:
        ordering = ['-created_at']

