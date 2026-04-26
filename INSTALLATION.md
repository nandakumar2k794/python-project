# Civic Report - Setup & Installation Guide

## Overview
Civic Report is a district-level civic issue reporting platform built with Django, Flask AI service, MongoDB, and Redis.

## Prerequisites
- Docker & Docker Compose (recommended)
- Python 3.10+ (for local development)
- Node.js 18+ (optional, for frontend build tools)
- MongoDB 7+
- Redis 7+

## Quick Start with Docker

### 1. Clone and Navigate
```bash
cd civic-report
```

### 2. Environment Configuration
Create a `.env` file in the `civic-report` directory:

```env
# Django Configuration
DJANGO_SECRET_KEY=your-super-secret-key-here-change-in-production
DJANGO_DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Database
MONGODB_URI=mongodb://mongodb:27017/civic_db

# Cache & Message Broker
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Flask AI Service
FLASK_AI_SERVICE_URL=http://flask_ai:5001

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost,http://localhost:3000,http://127.0.0.1

# API Rate Limiting
THROTTLE_ANON=100/hour
THROTTLE_USER=1000/hour
API_PAGE_SIZE=20

# Authentication
JWT_SECRET=your-jwt-secret-key
SUPABASE_URL=
SUPABASE_ANON_KEY=

# Optional: Email Configuration for Notifications
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 3. Build and Start Services
```bash
docker compose up --build
```

The application will be available at:
- **Frontend**: http://localhost (via Nginx)
- **Django API**: http://localhost:8000
- **Flask AI**: http://localhost:5001

### 4. Create Admin User (Optional)
```bash
docker exec civic-report-django_app-1 python manage.py shell
```

Then in the Python shell:
```python
from apps.accounts.models import User
import bcrypt

password = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
user = User(
    email="admin@example.com",
    name="Admin User",
    password_hash=password,
    role="admin"
)
user.save()
print(f"Admin user created: {user.email}")
```

## Local Development Setup

### 1. Install Python Dependencies
```bash
cd django_app
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Start MongoDB & Redis Locally
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:7
docker run -d -p 6379:6379 --name redis redis:7
```

### 3. Run Django Development Server
```bash
python manage.py migrate
python manage.py runserver
```

### 4. Run Celery Worker (in another terminal)
```bash
celery -A config worker --loglevel=info
```

### 5. Run Celery Beat (in another terminal)
```bash
celery -A config beat --loglevel=info
```

### 6. Start Flask AI Service
```bash
cd flask_ai_service
pip install -r requirements.txt
python app.py
```

## Project Structure

```
civic-report/
├── django_app/                 # Main Django application
│   ├── config/                 # Settings and configuration
│   │   ├── settings/
│   │   │   ├── base.py        # Base settings (enhanced)
│   │   │   ├── dev.py         # Development settings
│   │   │   └── prod.py        # Production settings
│   │   ├── exceptions.py       # Custom exception handlers
│   │   ├── asgi.py
│   │   ├── wsgi.py
│   │   └── urls.py
│   ├── apps/                   # Django applications
│   │   ├── accounts/          # User authentication & management
│   │   ├── issues/            # Issue CRUD & management (enhanced)
│   │   ├── notifications/     # Real-time notifications
│   │   ├── dashboard/         # Role-based dashboards
│   │   ├── analytics/         # Analytics & reporting
│   │   └── audit/             # Audit logging
│   ├── static/                # CSS, JS, images
│   │   ├── css/styles.css     # Enhanced responsiveness
│   │   └── js/app.js          # Enhanced JavaScript
│   ├── templates/             # HTML templates
│   ├── manage.py
│   └── requirements.txt        # Updated dependencies
├── flask_ai_service/          # AI classification & NLP
│   ├── routes/
│   ├── utils/
│   └── app.py
├── nginx/                     # Reverse proxy configuration
├── docker-compose.yml         # Docker orchestration
├── Dockerfile (Django & Flask)
├── .env                       # Environment variables (create locally)
└── README.md
```

## Key Features & Enhancements

### Backend Improvements
✅ **Pagination**: All list endpoints support pagination with `page` and `page_size` parameters
✅ **Validation**: Input validation for all endpoints
✅ **Error Handling**: Custom exception handler with consistent error responses
✅ **Logging**: Comprehensive logging to console and rotating file handlers
✅ **Rate Limiting**: Throttling configured for anonymous and authenticated users
✅ **Security**: CORS, CSRF, CSP headers configured

### Frontend Improvements
✅ **Responsive Design**: Mobile-first CSS with media queries for all breakpoints
✅ **Better Error Handling**: Graceful error handling with user feedback
✅ **Validation**: Client-side and server-side validation
✅ **Accessibility**: ARIA labels, semantic HTML, keyboard navigation
✅ **Performance**: Optimized JavaScript, minimal DOM manipulation
✅ **State Management**: Improved API state handling with retry logic

### API Endpoints

#### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh JWT token

#### Issues
- `GET /api/issues/?page=1&page_size=20` - List issues (paginated)
- `POST /api/issues/` - Create issue
- `GET /api/issues/{id}/` - Get issue details
- `PATCH /api/issues/{id}/status/` - Update issue status
- `POST /api/issues/{id}/upvote/` - Upvote issue
- `GET /api/issues/{id}/comments/` - Get comments
- `POST /api/issues/{id}/comments/` - Add comment
- `GET /api/issues/{id}/timeline/` - Get issue timeline

#### Notifications
- `GET /api/notifications/` - Get notifications
- `PATCH /api/notifications/mark-read/` - Mark notifications as read

#### Dashboard
- `GET /api/dashboard/citizen/` - Citizen dashboard data
- `GET /api/dashboard/officer/` - Officer dashboard data
- `GET /api/dashboard/admin/analytics/` - Admin analytics

#### Analytics
- `GET /api/dashboard/admin/analytics/` - Analytics data
- `GET /api/wards/` - List wards
- `PATCH /api/wards/{id}/` - Update ward

## Configuration Guide

### Production Setup

1. **Update `.env` for Production**
```env
DJANGO_DEBUG=False
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

2. **Configure Database**
```bash
# Use external MongoDB instance
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/civic_db
```

3. **Setup SSL/HTTPS**
Use nginx with Let's Encrypt certificates

4. **Configure Email Service**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-smtp-server
EMAIL_PORT=587
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-app-password
```

## Troubleshooting

### Issue: MongoDB Connection Error
```bash
# Check MongoDB is running
docker logs mongodb

# Verify connection string
MONGODB_URI=mongodb://mongodb:27017/civic_db
```

### Issue: Redis Connection Error
```bash
# Check Redis is running
docker logs redis

# Verify connection string
REDIS_URL=redis://redis:6379/0
```

### Issue: CORS Errors
Update `CORS_ALLOWED_ORIGINS` in `.env` to include your frontend domain

### Issue: Slow API Requests
1. Check MongoDB indexes
2. Reduce pagination `page_size` if needed
3. Enable Redis caching
4. Monitor Celery worker

## Performance Tips

1. **Enable Caching**: Configure Redis for query caching
2. **Database Indexing**: Add indexes to frequently queried fields
3. **CDN**: Use CDN for static assets
4. **Compression**: Enable Gzip compression in Nginx
5. **Load Balancing**: Use multiple Django workers behind a load balancer

## Monitoring & Maintenance

### Logs
- Django logs: `/logs/django.log`
- Celery logs: Check container output
- Nginx logs: `/var/log/nginx/`

### Health Checks
All services include health check endpoints at `/health` or `/ready`

### Database Cleanup
```bash
# Remove old notifications (older than 30 days)
db.notifications.deleteMany({
  "created_at": { $lt: new Date(Date.now() - 30*24*60*60*1000) }
})
```

## Deployment

### Using Docker Compose (Recommended)
```bash
docker compose -f docker-compose.yml up -d
```

### Using Kubernetes
See `k8s/` directory for Kubernetes manifests

### Using Heroku
1. Add Procfile
2. Set environment variables
3. Deploy: `git push heroku main`

## Support & Contributing

For issues, bugs, or feature requests, please visit the project repository.

## License
MIT License - See LICENSE file for details
