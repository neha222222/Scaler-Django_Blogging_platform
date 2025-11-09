"""
Management command to create sample data for testing

USAGE: python manage.py create_sample_data

This creates:
- 3 users (admin, author, reader)
- 5 blog posts
- 3 tags
- Sample comments and likes
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from blog.models import User, Post, Comment, Like, Tag
from django.db import transaction


class Command(BaseCommand):
    help = 'Creates sample data for testing the blogging platform'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))
        
        with transaction.atomic():
            # Clear existing data (optional)
            self.stdout.write('Clearing existing sample data...')
            
            # Create Users
            self.stdout.write('Creating users...')
            
            admin, _ = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@blogplatform.com',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'role': User.Role.ADMIN,
                    'bio': 'Platform administrator with full access'
                }
            )
            admin.set_password('admin123')
            admin.save()
            
            author, _ = User.objects.get_or_create(
                username='john_doe',
                defaults={
                    'email': 'john@blogplatform.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'role': User.Role.AUTHOR,
                    'bio': 'Passionate writer and software engineer'
                }
            )
            author.set_password('author123')
            author.save()
            
            reader, _ = User.objects.get_or_create(
                username='jane_reader',
                defaults={
                    'email': 'jane@blogplatform.com',
                    'first_name': 'Jane',
                    'last_name': 'Reader',
                    'role': User.Role.READER,
                    'bio': 'Avid reader and tech enthusiast'
                }
            )
            reader.set_password('reader123')
            reader.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Created {3} users'))
            
            # Create Tags
            self.stdout.write('Creating tags...')
            
            tag_python, _ = Tag.objects.get_or_create(name='Python')
            tag_django, _ = Tag.objects.get_or_create(name='Django')
            tag_webdev, _ = Tag.objects.get_or_create(name='Web Development')
            tag_tutorial, _ = Tag.objects.get_or_create(name='Tutorial')
            tag_best_practices, _ = Tag.objects.get_or_create(name='Best Practices')
            
            self.stdout.write(self.style.SUCCESS(f'✅ Created {5} tags'))
            
            # Create Posts
            self.stdout.write('Creating blog posts...')
            
            posts_data = [
                {
                    'title': 'Getting Started with Django REST Framework',
                    'content': '''Django REST Framework (DRF) is a powerful toolkit for building Web APIs. 
                    
In this comprehensive guide, we'll explore the fundamentals of DRF and how to build a production-ready API.

## What is Django REST Framework?

DRF is a flexible, full-featured library for building RESTful APIs with Django. It provides:
- Serialization for converting complex data types
- Authentication and permission classes
- ViewSets for quick API development
- Browsable API for easy testing

## Getting Started

First, install DRF:
```
pip install djangorestframework
```

Then add it to INSTALLED_APPS in settings.py. Start building your serializers and views!

Stay tuned for more tutorials on advanced DRF features.''',
                    'excerpt': 'Learn the basics of Django REST Framework and build your first API',
                    'tags': [tag_python, tag_django, tag_tutorial],
                    'status': Post.Status.PUBLISHED
                },
                {
                    'title': 'Best Practices for Django Model Design',
                    'content': '''Designing Django models properly is crucial for building maintainable applications.

## Key Principles

1. **Normalization**: Follow database normalization rules
2. **Indexes**: Add indexes to frequently queried fields
3. **Relationships**: Use appropriate ForeignKey and ManyToMany relationships
4. **Validation**: Add validators at model level
5. **Meta Options**: Use Meta class for ordering, indexes, and constraints

## Example

```python
class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]
```

Remember: Good model design leads to better performance and maintainability.''',
                    'excerpt': 'Essential tips for designing Django models the right way',
                    'tags': [tag_django, tag_best_practices],
                    'status': Post.Status.PUBLISHED
                },
                {
                    'title': 'Understanding JWT Authentication',
                    'content': '''JSON Web Tokens (JWT) have become the standard for API authentication.

## What is JWT?

JWT is a compact, URL-safe token format for transferring claims between parties. A JWT consists of three parts:
1. Header: Token type and hashing algorithm
2. Payload: Claims (user data)
3. Signature: Verification

## Advantages

- **Stateless**: No server-side session storage
- **Scalable**: Works across multiple servers
- **Mobile-friendly**: Easy to implement in mobile apps
- **Cross-domain**: Works across different domains

## Implementation in Django

Use `djangorestframework-simplejwt` for easy JWT integration:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
```

Security tip: Always use HTTPS and set appropriate token expiration times.''',
                    'excerpt': 'Deep dive into JWT authentication and how to implement it in Django',
                    'tags': [tag_django, tag_webdev],
                    'status': Post.Status.PUBLISHED
                },
                {
                    'title': 'Building a Scalable Blog Platform',
                    'content': '''Creating a blog platform requires careful planning and architecture decisions.

## Architecture Considerations

### Database Design
- Use UUIDs for better security
- Implement soft deletes
- Add proper indexes
- Use caching for frequently accessed data

### Performance Optimization
- Query optimization with select_related and prefetch_related
- Pagination for large datasets
- Database connection pooling
- CDN for static assets

### Security
- Role-based access control
- Input validation and sanitization
- CSRF protection
- Rate limiting

## Tech Stack

For our blog platform, we used:
- Django & DRF for backend
- PostgreSQL for database
- Redis for caching
- JWT for authentication

This combination provides excellent performance and security.''',
                    'excerpt': 'Learn how to architect and build a production-ready blog platform',
                    'tags': [tag_django, tag_webdev, tag_best_practices],
                    'status': Post.Status.PUBLISHED
                },
                {
                    'title': 'Draft: Advanced Django Query Optimization',
                    'content': '''This post covers advanced techniques for optimizing Django queries.

Content coming soon... This is a draft post that only the author can see.

Topics to cover:
- select_related vs prefetch_related
- Database indexes
- Query analysis with django-debug-toolbar
- Caching strategies
- Connection pooling''',
                    'excerpt': 'Advanced query optimization techniques (Draft)',
                    'tags': [tag_django, tag_best_practices],
                    'status': Post.Status.DRAFT
                }
            ]
            
            created_posts = []
            for post_data in posts_data:
                tags = post_data.pop('tags')
                post, created = Post.objects.get_or_create(
                    title=post_data['title'],
                    defaults={
                        **post_data,
                        'author': author,
                        'published_at': timezone.now() if post_data['status'] == Post.Status.PUBLISHED else None
                    }
                )
                if created:
                    post.tags.set(tags)
                    created_posts.append(post)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Created {len(created_posts)} blog posts'))
            
            # Create Comments
            self.stdout.write('Creating comments...')
            
            published_posts = [p for p in created_posts if p.status == Post.Status.PUBLISHED]
            if published_posts:
                comment1, _ = Comment.objects.get_or_create(
                    post=published_posts[0],
                    author=reader,
                    defaults={
                        'content': 'Great tutorial! Very helpful for beginners.',
                        'is_approved': True
                    }
                )
                
                comment2, _ = Comment.objects.get_or_create(
                    post=published_posts[0],
                    author=admin,
                    defaults={
                        'content': 'Excellent explanation of DRF concepts.',
                        'is_approved': True
                    }
                )
                
                # Create a comment awaiting approval
                comment3, _ = Comment.objects.get_or_create(
                    post=published_posts[1],
                    author=reader,
                    defaults={
                        'content': 'This comment is awaiting moderation.',
                        'is_approved': False
                    }
                )
                
                self.stdout.write(self.style.SUCCESS(f'✅ Created 3 comments'))
                
                # Create Likes
                self.stdout.write('Creating likes...')
                
                Like.objects.get_or_create(user=reader, post=published_posts[0])
                Like.objects.get_or_create(user=admin, post=published_posts[0])
                if len(published_posts) > 1:
                    Like.objects.get_or_create(user=reader, post=published_posts[1])
                
                self.stdout.write(self.style.SUCCESS(f'✅ Created likes'))
            
            # Summary
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS('✅ Sample data created successfully!'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write('')
            self.stdout.write('📊 Summary:')
            self.stdout.write(f'   Users: {User.objects.count()}')
            self.stdout.write(f'   Posts: {Post.objects.count()}')
            self.stdout.write(f'   Tags: {Tag.objects.count()}')
            self.stdout.write(f'   Comments: {Comment.objects.count()}')
            self.stdout.write(f'   Likes: {Like.objects.count()}')
            self.stdout.write('')
            self.stdout.write('🔑 Login Credentials:')
            self.stdout.write('   Admin: admin / admin123')
            self.stdout.write('   Author: john_doe / author123')
            self.stdout.write('   Reader: jane_reader / reader123')
            self.stdout.write('')
            self.stdout.write('🚀 Run server: python manage.py runserver')
            self.stdout.write('📚 API docs: http://127.0.0.1:8000/swagger/')

