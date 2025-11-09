"""
API Views for Blogging Platform
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q, F
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import User, Post, Comment, Like, Share, Tag
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    PostListSerializer, PostDetailSerializer, PostCreateUpdateSerializer,
    CommentSerializer, LikeSerializer, ShareSerializer, TagSerializer
)
from .permissions import (
    IsAdminUser, IsAuthorOrAdmin, IsOwnerOrReadOnly,
    CanModerateComments, IsAuthenticatedOrReadOnly, CanPublishPost
)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User management"""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['date_joined', 'username']
    
    def get_serializer_class(self):
        if self.action == 'register':
            return UserRegistrationSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action == 'register':
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """User registration endpoint"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'user': UserSerializer(user).data,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """Get user's published posts"""
        user = self.get_object()
        posts = Post.objects.filter(
            author=user,
            status=Post.Status.PUBLISHED
        ).annotate(
            like_count=Count('likes'),
            comment_count=Count('comments', filter=Q(comments__is_approved=True))
        )
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for Blog Posts"""
    
    queryset = Post.objects.select_related('author').prefetch_related('tags', 'likes').annotate(
        like_count=Count('likes'),
        comment_count=Count('comments', filter=Q(comments__is_approved=True))
    )
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'author']
    search_fields = ['title', 'content', 'tags__name']
    ordering_fields = ['created_at', 'published_at', 'view_count', 'like_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PostCreateUpdateSerializer
        return PostDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'create':
            return [CanPublishPost()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_authenticated:
            return queryset.filter(status=Post.Status.PUBLISHED)
        
        if user.role == User.Role.ADMIN:
            return queryset
        
        if user.role == User.Role.AUTHOR:
            return queryset.filter(
                Q(status=Post.Status.PUBLISHED) | Q(author=user)
            )
        
        return queryset.filter(status=Post.Status.PUBLISHED)
    
    def perform_create(self, serializer):
        """Automatically set author to current user"""
        serializer.save(author=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to increment view count"""
        instance = self.get_object()
        
        Post.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        instance.refresh_from_db()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Like a post"""
        post = self.get_object()
        user = request.user
        
        like, created = Like.objects.get_or_create(user=user, post=post)
        
        if created:
            return Response({
                'message': 'Post liked successfully',
                'like_count': post.likes.count()
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'message': 'You have already liked this post',
                'like_count': post.likes.count()
            }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        """Unlike a post"""
        post = self.get_object()
        user = request.user
        
        deleted_count, _ = Like.objects.filter(user=user, post=post).delete()
        
        if deleted_count > 0:
            return Response({
                'message': 'Post unliked successfully',
                'like_count': post.likes.count()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'You have not liked this post',
                'like_count': post.likes.count()
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def share(self, request, pk=None):
        """Share a post"""
        post = self.get_object()
        user = request.user
        platform = request.data.get('platform', '')
        
        share = Share.objects.create(user=user, post=post, platform=platform)
        
        Post.objects.filter(pk=post.pk).update(share_count=F('share_count') + 1)
        post.refresh_from_db()
        
        return Response({
            'message': 'Post shared successfully',
            'share_count': post.share_count
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get post analytics"""
        post = self.get_object()
        
        if request.user != post.author and request.user.role != User.Role.ADMIN:
            return Response({
                'error': 'You do not have permission to view analytics for this post'
            }, status=status.HTTP_403_FORBIDDEN)
        
        analytics = {
            'view_count': post.view_count,
            'like_count': post.likes.count(),
            'comment_count': post.comments.filter(is_approved=True).count(),
            'share_count': post.share_count,
            'engagement_rate': self._calculate_engagement_rate(post),
        }
        
        return Response(analytics)
    
    def _calculate_engagement_rate(self, post):
        """Calculate engagement rate: (likes + comments + shares) / views * 100"""
        if post.view_count == 0:
            return 0
        
        total_engagements = (
            post.likes.count() +
            post.comments.filter(is_approved=True).count() +
            post.share_count
        )
        
        return round((total_engagements / post.view_count) * 100, 2)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for Comments"""
    
    queryset = Comment.objects.select_related('author', 'post').all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['post', 'is_approved']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Users see only approved comments (except their own)"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_authenticated:
            return queryset.filter(is_approved=True)
        
        if user.role == User.Role.ADMIN:
            return queryset
        
        return queryset.filter(
            Q(is_approved=True) |
            Q(author=user) |
            Q(post__author=user)
        ).distinct()
    
    def perform_create(self, serializer):
        """Auto-set author"""
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanModerateComments])
    def approve(self, request, pk=None):
        """Approve a comment"""
        comment = self.get_object()
        comment.is_approved = True
        comment.save()
        
        return Response({
            'message': 'Comment approved successfully'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanModerateComments])
    def reject(self, request, pk=None):
        """Reject (delete) a comment"""
        comment = self.get_object()
        comment.delete()
        
        return Response({
            'message': 'Comment rejected successfully'
        }, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for Tags"""
    
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering = ['name']
    
    def get_permissions(self):
        """Only authors and admins can create/modify tags"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthorOrAdmin()]
        return [AllowAny()]
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """Get all published posts with this tag"""
        tag = self.get_object()
        posts = Post.objects.filter(
            tags=tag,
            status=Post.Status.PUBLISHED
        ).annotate(
            like_count=Count('likes'),
            comment_count=Count('comments', filter=Q(comments__is_approved=True))
        )
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)
