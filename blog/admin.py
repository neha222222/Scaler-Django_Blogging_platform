"""
Django Admin Configuration
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Post, Comment, Like, Share, Tag


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with role management"""
    list_display = ('username', 'email', 'role', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role', 'bio', 'profile_picture')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role', 'bio')}),
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Tag administration"""
    list_display = ('name', 'slug', 'post_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Post Count'


class CommentInline(admin.TabularInline):
    """Inline admin for comments"""
    model = Comment
    extra = 0
    readonly_fields = ('author', 'created_at')
    fields = ('author', 'content', 'is_approved', 'created_at')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Post administration"""
    list_display = ('title', 'author', 'status', 'view_count', 'like_count', 'comment_count', 'created_at', 'published_at')
    list_filter = ('status', 'created_at', 'published_at', 'tags')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('view_count', 'share_count', 'created_at', 'updated_at', 'published_at', 'like_count', 'comment_count')
    filter_horizontal = ('tags',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'status')
        }),
        ('Content', {
            'fields': ('content', 'excerpt', 'tags')
        }),
        ('Analytics', {
            'fields': ('view_count', 'share_count', 'like_count', 'comment_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [CommentInline]
    
    def like_count(self, obj):
        return obj.likes.count()
    like_count.short_description = 'Likes'
    
    def comment_count(self, obj):
        return obj.comments.filter(is_approved=True).count()
    comment_count.short_description = 'Comments'
    
    actions = ['publish_posts', 'archive_posts']
    
    def publish_posts(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status=Post.Status.PUBLISHED, published_at=timezone.now())
        self.message_user(request, f'{updated} post(s) published successfully.')
    publish_posts.short_description = 'Publish selected posts'
    
    def archive_posts(self, request, queryset):
        updated = queryset.update(status=Post.Status.ARCHIVED)
        self.message_user(request, f'{updated} post(s) archived successfully.')
    archive_posts.short_description = 'Archive selected posts'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Comment administration"""
    list_display = ('author', 'post', 'content_preview', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    readonly_fields = ('author', 'post', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    actions = ['approve_comments', 'reject_comments']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comment(s) approved.')
    approve_comments.short_description = 'Approve selected comments'
    
    def reject_comments(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} comment(s) rejected.')
    reject_comments.short_description = 'Reject selected comments'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """Like administration"""
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title')
    readonly_fields = ('user', 'post', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    """Share administration"""
    list_display = ('user', 'post', 'platform', 'created_at')
    list_filter = ('platform', 'created_at')
    search_fields = ('user__username', 'post__title')
    readonly_fields = ('user', 'post', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

