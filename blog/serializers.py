"""
Serializers for Blog API
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from .models import User, Post, Comment, Like, Share, Tag


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name', 'role', 'bio')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True}
        }
    
    def validate(self, attrs):
        """Ensure password fields match"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested relationships"""
    
    post_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'bio', 'post_count', 'date_joined')
        read_only_fields = ('id', 'date_joined')
    
    def get_post_count(self, obj):
        return obj.posts.filter(status=Post.Status.PUBLISHED).count()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags"""
    
    post_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'post_count')
        read_only_fields = ('slug',)
    
    def get_post_count(self, obj):
        return obj.posts.filter(status=Post.Status.PUBLISHED).count()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments"""
    
    author_detail = UserSerializer(source='author', read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ('id', 'post', 'author', 'author_detail', 'content', 'is_approved', 
                  'parent', 'replies', 'created_at', 'updated_at')
        read_only_fields = ('id', 'author', 'is_approved', 'created_at', 'updated_at')
    
    def get_replies(self, obj):
        """Get approved replies to this comment"""
        if obj.replies.exists():
            replies = obj.replies.filter(is_approved=True)
            return CommentSerializer(replies, many=True).data
        return []


class LikeSerializer(serializers.ModelSerializer):
    """Serializer for likes"""
    
    user_detail = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = Like
        fields = ('id', 'user', 'user_detail', 'post', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
    
    def validate(self, attrs):
        """Prevent duplicate likes"""
        user = self.context['request'].user
        post = attrs.get('post')
        
        if Like.objects.filter(user=user, post=post).exists():
            raise serializers.ValidationError("You have already liked this post.")
        
        return attrs


class ShareSerializer(serializers.ModelSerializer):
    """Serializer for shares"""
    
    user_detail = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = Share
        fields = ('id', 'user', 'user_detail', 'post', 'platform', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for post lists"""
    
    author_detail = UserSerializer(source='author', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Post
        fields = ('id', 'title', 'slug', 'excerpt', 'author', 'author_detail', 
                  'tags', 'status', 'view_count', 'like_count', 'comment_count',
                  'share_count', 'created_at', 'published_at')
        read_only_fields = ('id', 'slug', 'author', 'view_count', 'share_count', 'created_at', 'published_at')


class PostDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single post view"""
    
    author_detail = UserSerializer(source='author', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Tag.objects.all(),
        source='tags'
    )
    comments = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ('id', 'title', 'slug', 'content', 'excerpt', 'author', 'author_detail',
                  'tags', 'tag_ids', 'status', 'view_count', 'like_count', 'comment_count',
                  'share_count', 'comments', 'is_liked', 'created_at', 'updated_at', 'published_at')
        read_only_fields = ('id', 'slug', 'author', 'view_count', 'share_count', 'created_at', 'updated_at', 'published_at')
    
    def get_comments(self, obj):
        """Get approved top-level comments"""
        comments = obj.comments.filter(is_approved=True, parent=None)
        return CommentSerializer(comments, many=True).data
    
    def get_is_liked(self, obj):
        """Check if current user has liked this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, post=obj).exists()
        return False
    
    def validate(self, attrs):
        """Business logic validation"""
        if attrs.get('status') == Post.Status.PUBLISHED and not attrs.get('excerpt'):
            attrs['excerpt'] = attrs.get('content', '')[:200]
        
        return attrs


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for create/update operations"""
    
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source='tags',
        required=False
    )
    
    class Meta:
        model = Post
        fields = ('title', 'content', 'excerpt', 'tag_ids', 'status')
    
    def validate_status(self, value):
        """Validate status transitions based on user role"""
        user = self.context['request'].user
        instance = self.instance
        
        if value == Post.Status.PUBLISHED:
            if instance and instance.author != user and user.role != User.Role.ADMIN:
                raise serializers.ValidationError("You can only publish your own posts.")
        
        if value == Post.Status.ARCHIVED:
            if user.role not in [User.Role.ADMIN, User.Role.AUTHOR]:
                raise serializers.ValidationError("Only authors and admins can archive posts.")
        
        return value

