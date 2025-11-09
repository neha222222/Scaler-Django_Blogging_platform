"""
Custom Permissions for Role-Based Access Control
"""

from rest_framework import permissions
from .models import User, Post, Comment


class IsAdminUser(permissions.BasePermission):
    """Only admins can access"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == User.Role.ADMIN


class IsAuthorOrAdmin(permissions.BasePermission):
    """Only authors and admins can access"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in [User.Role.AUTHOR, User.Role.ADMIN]


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Read operations: Anyone | Write operations: Only owner or admin"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(obj, 'author'):
            return obj.author == request.user or request.user.role == User.Role.ADMIN
        
        if isinstance(obj, User):
            return obj == request.user or request.user.role == User.Role.ADMIN
        
        return False


class CanModerateComments(permissions.BasePermission):
    """Post authors can moderate comments on their posts. Admins can moderate any comment"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Role.ADMIN:
            return True
        
        if isinstance(obj, Comment):
            return obj.post.author == request.user
        
        return False


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """Unauthenticated users can read, only authenticated users can write"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class CanPublishPost(permissions.BasePermission):
    """Only authors and admins can publish posts"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_authenticated and request.user.role in [User.Role.AUTHOR, User.Role.ADMIN]
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if request.user.role == User.Role.ADMIN:
            return True
        
        if isinstance(obj, Post):
            return obj.author == request.user
        
        return False

