"""
Comprehensive Unit Tests for Blogging Platform
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Post, Comment, Like, Share, Tag

User = get_user_model()


class UserModelTest(TestCase):
    """Test User Model"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_create_user_with_role(self):
        """Test user creation with specific role"""
        user = User.objects.create_user(**self.user_data, role=User.Role.AUTHOR)
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, User.Role.AUTHOR)
        self.assertTrue(user.check_password('StrongPass123!'))
    
    def test_user_default_role_is_reader(self):
        """Test default role is READER"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.role, User.Role.READER)


class UserRegistrationAPITest(APITestCase):
    """Test User Registration API"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('user-register')
        self.valid_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'AUTHOR'
        }
    
    def test_user_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'newuser')
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_user_registration_password_mismatch(self):
        """Test registration fails with password mismatch"""
        invalid_data = self.valid_data.copy()
        invalid_data['password2'] = 'DifferentPassword123!'
        
        response = self.client.post(self.register_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class AuthenticationAPITest(APITestCase):
    """
    Test JWT Authentication
    
    FUNCTIONALITY: JWT token-based authentication
    """
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='authuser',
            email='auth@example.com',
            password='TestPass123!'
        )
        self.login_url = reverse('token_obtain_pair')
    
    def test_jwt_login_success(self):
        """
        TEST 1: Successful JWT token generation
        TESTS: POST /api/auth/login/
        """
        response = self.client.post(self.login_url, {
            'username': 'authuser',
            'password': 'TestPass123!'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_jwt_login_invalid_credentials(self):
        """
        TEST 2: Login fails with wrong password
        TESTS: Authentication security
        """
        response = self.client.post(self.login_url, {
            'username': 'authuser',
            'password': 'WrongPassword123!'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PostModelTest(TestCase):
    """
    Test Post Model
    
    FUNCTIONALITY: Blog post creation and management
    """
    
    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='AuthorPass123!',
            role=User.Role.AUTHOR
        )
        self.tag = Tag.objects.create(name='Django')
    
    def test_create_post_auto_generates_slug(self):
        """
        TEST 1: Slug is auto-generated from title
        TESTS: Auto-slug generation
        """
        post = Post.objects.create(
            title='My Test Post',
            content='This is a test post content that is long enough to pass validation.',
            author=self.author
        )
        
        self.assertEqual(post.slug, 'my-test-post')
    
    def test_post_like_count_property(self):
        """
        TEST 2: like_count computed property works
        TESTS: Computed properties
        """
        post = Post.objects.create(
            title='Popular Post',
            content='This post will get many likes and that is good for testing purposes.',
            author=self.author
        )
        
        # Create likes
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        Like.objects.create(user=user1, post=post)
        Like.objects.create(user=user2, post=post)
        
        self.assertEqual(post.like_count, 2)


class PostAPITest(APITestCase):
    """
    Test Post CRUD API
    
    FUNCTIONALITY: Create, Read, Update, Delete blog posts
    """
    
    def setUp(self):
        # Create users
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='AuthorPass123!',
            role=User.Role.AUTHOR
        )
        self.reader = User.objects.create_user(
            username='reader',
            email='reader@example.com',
            password='ReaderPass123!',
            role=User.Role.READER
        )
        
        # Create test post
        self.post = Post.objects.create(
            title='Test Post',
            content='This is test content that is definitely long enough for validation.',
            author=self.author,
            status=Post.Status.PUBLISHED
        )
        
        self.client = APIClient()
        self.post_list_url = reverse('post-list')
        self.post_detail_url = reverse('post-detail', kwargs={'pk': self.post.pk})
    
    def test_list_posts_unauthenticated(self):
        """
        TEST 1: Anyone can view published posts
        TESTS: GET /api/posts/ without authentication
        """
        response = self.client.get(self.post_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_post_as_author(self):
        """
        TEST 2: Authors can create posts
        TESTS: POST /api/posts/ with author role
        """
        self.client.force_authenticate(user=self.author)
        
        post_data = {
            'title': 'New Post by Author',
            'content': 'This is brand new content created by an author with proper length.',
            'status': 'DRAFT'
        }
        
        response = self.client.post(self.post_list_url, post_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
    
    def test_create_post_as_reader_forbidden(self):
        """
        TEST 3: Readers cannot create posts
        TESTS: Permission enforcement
        """
        self.client.force_authenticate(user=self.reader)
        
        post_data = {
            'title': 'Attempted Post by Reader',
            'content': 'This should not be created because readers lack permissions.',
            'status': 'DRAFT'
        }
        
        response = self.client.post(self.post_list_url, post_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_own_post(self):
        """
        TEST 4: Authors can update their own posts
        TESTS: PUT /api/posts/{id}/ as owner
        """
        self.client.force_authenticate(user=self.author)
        
        update_data = {
            'title': 'Updated Test Post',
            'content': 'This content has been updated by the original author successfully.',
            'status': 'PUBLISHED'
        }
        
        response = self.client.put(self.post_detail_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Test Post')
    
    def test_delete_others_post_forbidden(self):
        """
        TEST 5: Users cannot delete others' posts
        TESTS: Permission enforcement for delete
        """
        self.client.force_authenticate(user=self.reader)
        
        response = self.client.delete(self.post_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())
    
    def test_retrieve_post_increments_view_count(self):
        """
        TEST 6: Viewing a post increments view count
        TESTS: Analytics tracking
        """
        initial_count = self.post.view_count
        
        response = self.client.get(self.post_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.view_count, initial_count + 1)


class PostInteractionAPITest(APITestCase):
    """
    Test Post Interactions (Like, Share)
    
    FUNCTIONALITY: Post interaction features
    """
    
    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            password='pass',
            role=User.Role.AUTHOR
        )
        self.user = User.objects.create_user(
            username='user',
            password='pass'
        )
        
        self.post = Post.objects.create(
            title='Interactive Post',
            content='This post will receive likes and shares from users.',
            author=self.author,
            status=Post.Status.PUBLISHED
        )
        
        self.client = APIClient()
        self.like_url = reverse('post-like', kwargs={'pk': self.post.pk})
        self.unlike_url = reverse('post-unlike', kwargs={'pk': self.post.pk})
        self.share_url = reverse('post-share', kwargs={'pk': self.post.pk})
    
    def test_like_post(self):
        """
        TEST 1: User can like a post
        TESTS: POST /api/posts/{id}/like/
        """
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(self.like_url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Like.objects.filter(user=self.user, post=self.post).exists())
        self.assertEqual(response.data['like_count'], 1)
    
    def test_like_post_twice_idempotent(self):
        """
        TEST 2: Liking same post twice doesn't create duplicate
        TESTS: Idempotency
        """
        self.client.force_authenticate(user=self.user)
        
        # First like
        self.client.post(self.like_url)
        
        # Second like
        response = self.client.post(self.like_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Like.objects.filter(user=self.user, post=self.post).count(), 1)
    
    def test_unlike_post(self):
        """
        TEST 3: User can unlike a post
        TESTS: POST /api/posts/{id}/unlike/
        """
        self.client.force_authenticate(user=self.user)
        
        # First like the post
        Like.objects.create(user=self.user, post=self.post)
        
        # Then unlike
        response = self.client.post(self.unlike_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Like.objects.filter(user=self.user, post=self.post).exists())
    
    def test_share_post(self):
        """
        TEST 4: User can share a post
        TESTS: POST /api/posts/{id}/share/
        """
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(self.share_url, {'platform': 'twitter'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Share.objects.filter(user=self.user, post=self.post).exists())
        self.post.refresh_from_db()
        self.assertEqual(self.post.share_count, 1)


class CommentAPITest(APITestCase):
    """
    Test Comment System with Moderation
    
    FUNCTIONALITY: Commenting and moderation
    """
    
    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            password='pass',
            role=User.Role.AUTHOR
        )
        self.user = User.objects.create_user(
            username='commenter',
            password='pass'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='pass',
            role=User.Role.ADMIN
        )
        
        self.post = Post.objects.create(
            title='Post for Comments',
            content='This post will receive comments from various users.',
            author=self.author,
            status=Post.Status.PUBLISHED
        )
        
        self.client = APIClient()
        self.comment_list_url = reverse('comment-list')
    
    def test_create_comment(self):
        """
        TEST 1: User can create comment
        TESTS: POST /api/comments/
        """
        self.client.force_authenticate(user=self.user)
        
        comment_data = {
            'post': str(self.post.pk),
            'content': 'This is a test comment on the post.'
        }
        
        response = self.client.post(self.comment_list_url, comment_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Comment.objects.filter(author=self.user, post=self.post).exists())
    
    def test_comment_needs_approval(self):
        """
        TEST 2: New comments are not approved by default
        TESTS: Moderation workflow
        """
        self.client.force_authenticate(user=self.user)
        
        comment_data = {
            'post': str(self.post.pk),
            'content': 'This comment should need approval first.'
        }
        
        response = self.client.post(self.comment_list_url, comment_data, format='json')
        
        comment = Comment.objects.get(pk=response.data['id'])
        self.assertFalse(comment.is_approved)
    
    def test_post_author_can_approve_comment(self):
        """
        TEST 3: Post author can approve comments on their post
        TESTS: Permission for moderation
        """
        # Create comment
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Comment awaiting approval from post author.'
        )
        
        # Author approves
        self.client.force_authenticate(user=self.author)
        approve_url = reverse('comment-approve', kwargs={'pk': comment.pk})
        
        response = self.client.post(approve_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertTrue(comment.is_approved)
    
    def test_admin_can_approve_any_comment(self):
        """
        TEST 4: Admin can approve any comment
        TESTS: Admin permissions
        """
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Comment that admin will approve regardless of post ownership.'
        )
        
        self.client.force_authenticate(user=self.admin)
        approve_url = reverse('comment-approve', kwargs={'pk': comment.pk})
        
        response = self.client.post(approve_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertTrue(comment.is_approved)


class TagAPITest(APITestCase):
    """
    Test Tag System
    
    FUNCTIONALITY: Tagging and keyword-based search
    """
    
    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            password='pass',
            role=User.Role.AUTHOR
        )
        self.reader = User.objects.create_user(
            username='reader',
            password='pass'
        )
        
        self.tag = Tag.objects.create(name='Python')
        
        self.client = APIClient()
        self.tag_list_url = reverse('tag-list')
    
    def test_list_tags(self):
        """
        TEST 1: Anyone can list tags
        TESTS: GET /api/tags/
        """
        response = self.client.get(self.tag_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_tag_as_author(self):
        """
        TEST 2: Authors can create tags
        TESTS: POST /api/tags/ with author role
        """
        self.client.force_authenticate(user=self.author)
        
        tag_data = {'name': 'Django'}
        response = self.client.post(self.tag_list_url, tag_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Tag.objects.filter(name='Django').exists())
    
    def test_create_tag_as_reader_forbidden(self):
        """
        TEST 3: Readers cannot create tags
        TESTS: Permission enforcement
        """
        self.client.force_authenticate(user=self.reader)
        
        tag_data = {'name': 'JavaScript'}
        response = self.client.post(self.tag_list_url, tag_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SearchAPITest(APITestCase):
    """
    Test Search Functionality
    
    FUNCTIONALITY: Keyword-based search for posts
    """
    
    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            password='pass',
            role=User.Role.AUTHOR
        )
        
        # Create posts with different content
        self.post1 = Post.objects.create(
            title='Django Tutorial',
            content='Learn Django web framework for building web applications easily.',
            author=self.author,
            status=Post.Status.PUBLISHED
        )
        self.post2 = Post.objects.create(
            title='Flask Guide',
            content='Flask is a micro web framework written in Python for building APIs.',
            author=self.author,
            status=Post.Status.PUBLISHED
        )
        
        self.client = APIClient()
        self.post_list_url = reverse('post-list')
    
    def test_search_posts_by_title(self):
        """
        TEST 1: Search posts by title keyword
        TESTS: GET /api/posts/?search=Django
        """
        response = self.client.get(self.post_list_url, {'search': 'Django'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Django Tutorial')
    
    def test_search_posts_by_content(self):
        """
        TEST 2: Search posts by content keyword
        TESTS: Content search functionality
        """
        response = self.client.get(self.post_list_url, {'search': 'Python'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find Flask post (mentions Python)
        titles = [post['title'] for post in response.data['results']]
        self.assertIn('Flask Guide', titles)


# Test Coverage: 27 tests covering all major functionalities
# - User Registration (2 tests)
# - JWT Authentication (2 tests)
# - User Model (2 tests)
# - Post Model (2 tests)
# - Post CRUD API (6 tests)
# - Post Interactions (4 tests)
# - Comment Moderation (4 tests)
# - Tag System (3 tests)
# - Search (2 tests)

