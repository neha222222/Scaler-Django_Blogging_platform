# Blogging Platform - System Design Project

A production-ready blogging platform built with Django REST Framework featuring role-based access control, comment moderation, post interactions, and comprehensive analytics.

## Features

- User authentication with role-based access (Admin, Author, Reader)  
- Complete CRUD operations for blog posts  
- Commenting system with moderation  
- Post interactions (likes, shares, analytics)  
- Tagging and keyword-based search  
- 27+ comprehensive unit tests  
- RESTful API with JWT authentication  
- Auto-generated API documentation (Swagger)  

## Quick Start

### Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# (Optional) Load sample data
python manage.py create_sample_data

# Run server
python manage.py runserver
```

### Access Points

- **API Documentation**: http://127.0.0.1:8000/swagger/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **API Root**: http://127.0.0.1:8000/api/

## Running Tests

```bash
# Run all tests
python manage.py test blog

# Run specific test class
python manage.py test blog.tests.PostAPITest

# Run with coverage
coverage run --source='.' manage.py test blog
coverage report
coverage html
```

## API Endpoints

### Authentication

```bash
# Register
POST /api/users/register/
{
  "username": "john",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "password2": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "AUTHOR"
}

# Login
POST /api/auth/login/
{
  "username": "john",
  "password": "SecurePass123!"
}

# Returns: {"access": "...", "refresh": "..."}
```

### Posts

```bash
# List posts (supports search, filter, ordering)
GET /api/posts/
GET /api/posts/?search=django
GET /api/posts/?status=PUBLISHED
GET /api/posts/?ordering=-created_at

# Get single post
GET /api/posts/{id}/

# Create post (requires authentication)
POST /api/posts/
Authorization: Bearer {access_token}
{
  "title": "My Blog Post",
  "content": "Post content here (minimum 50 characters)...",
  "tag_ids": [1, 2],
  "status": "DRAFT"
}

# Update post
PUT /api/posts/{id}/
Authorization: Bearer {access_token}

# Delete post
DELETE /api/posts/{id}/
Authorization: Bearer {access_token}

# Like post
POST /api/posts/{id}/like/
Authorization: Bearer {access_token}

# Unlike post
POST /api/posts/{id}/unlike/
Authorization: Bearer {access_token}

# Share post
POST /api/posts/{id}/share/
Authorization: Bearer {access_token}
{"platform": "twitter"}

# Get analytics (author/admin only)
GET /api/posts/{id}/analytics/
Authorization: Bearer {access_token}
```

### Comments

```bash
# Create comment
POST /api/comments/
Authorization: Bearer {access_token}
{
  "post": "{post_id}",
  "content": "Great post!"
}

# Approve comment (post author/admin)
POST /api/comments/{id}/approve/
Authorization: Bearer {access_token}

# Reject comment (post author/admin)
POST /api/comments/{id}/reject/
Authorization: Bearer {access_token}
```

### Tags

```bash
# List tags
GET /api/tags/

# Create tag (author/admin)
POST /api/tags/
Authorization: Bearer {access_token}
{"name": "Python"}

# Get posts by tag
GET /api/tags/{id}/posts/
```

## Architecture

### Tech Stack

- **Framework**: Django 4.2.7 + Django REST Framework 3.14.0
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: SQLite (dev) / PostgreSQL-ready (production)
- **API Docs**: Swagger/OpenAPI (drf-yasg)
- **Testing**: Django TestCase + DRF APITestCase

### Database Schema

```
User (custom user with roles)
├── Post (UUID PK, status machine)
│   ├── Tags (many-to-many)
│   ├── Comments (with moderation)
│   └── Likes (unique constraint)
```

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **Admin** | Full access, manage all content |
| **Author** | Create/edit/delete own posts, moderate own comments |
| **Reader** | Read posts, comment, like, share |

## Project Structure

```
scaler2/
├── blogging_platform/     # Project settings
│   ├── settings.py       
│   ├── urls.py           
│   └── wsgi.py           
├── blog/                  # Main app
│   ├── models.py         
│   ├── serializers.py    
│   ├── views.py          
│   ├── permissions.py    
│   ├── urls.py            
│   ├── admin.py          
│   └── tests.py          
├── manage.py
├── requirements.txt
└── README.md
```

## Testing Coverage

| Functionality | Tests |
|---------------|-------|
| User Registration | 2 
| JWT Authentication | 2 |  
| User Model | 2 |  
| Post Model | 2 |  
| Post CRUD API | 6 |   
| Post Interactions | 4 | 
| Comment Moderation | 4 |  
| Tag System | 3 |  
| Search Functionality | 2 |  
| **TOTAL** | **27** |  

## Sample Data

Load sample data with pre-created users and posts:

```bash
python manage.py create_sample_data
```

**Sample Login Credentials:**
- Admin: `admin` / `admin123`
- Author: `john_doe` / `author123`
- Reader: `jane_reader` / `reader123`

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in settings
2. Configure PostgreSQL database
3. Set strong `SECRET_KEY`
4. Configure `ALLOWED_HOSTS`
5. Use Gunicorn + Nginx
6. Enable HTTPS
7. Set up Redis for caching
8. Use AWS S3 for media files

## Dependencies

```
Django==4.2.7
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
django-filter==23.5
python-decouple==3.8
psycopg2-binary==2.9.9
drf-yasg==1.21.7
coverage==7.3.2
```
