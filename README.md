# Civic Issue Reporting System

A district-level issue reporting platform that enables citizens to report civic problems (roads, water, sanitation, electricity, etc.) with AI-powered image analysis and real-time tracking.

## Tech Stack Overview

### Backend Framework
**Django** - Python web framework for building the main application
- Handles user authentication, API endpoints, and business logic
- Provides ORM for database operations
- Manages WebSocket connections for real-time notifications
- Serves static files and templates

**Django REST Framework (DRF)** - Toolkit for building REST APIs
- Serializes data to/from JSON
- Provides authentication and permissions
- Automatic API documentation and browsable API interface

### Database
**MongoDB** - NoSQL document database
- Stores all application data (users, issues, notifications)
- Flexible schema allows storing varied issue types
- Horizontal scalability for handling large datasets
- Document-based storage matches Python object structures

### AI & Image Analysis
**Flask** - Lightweight Python web framework for AI microservice
- Separate service for image analysis to avoid blocking main app
- Handles image processing and AI model inference

**Ollama** - Local LLM inference engine
- Runs LLaVA (Large Language and Vision Assistant) model locally
- Analyzes civic issue images without external API calls
- Free, no rate limits, completely offline
- Provides accurate image descriptions for issue categorization

**Gemini API** - Google's generative AI (fallback)
- Backup AI provider if Ollama is unavailable
- Used for advanced image understanding
- Rate-limited free tier

### Real-Time Communication
**Django Channels** - WebSocket support for Django
- Enables real-time notifications to connected clients
- Maintains persistent connections for live updates
- Handles asynchronous message broadcasting

**Redis** - In-memory data store
- Message broker for Channels
- Caches frequently accessed data
- Stores session data for WebSocket connections
- Enables communication between multiple workers

### Task Queue & Scheduling
**Celery** - Distributed task queue
- Processes long-running tasks asynchronously
- Sends notifications without blocking requests
- Handles scheduled tasks (e.g., daily reports)

**Celery Beat** - Scheduler for Celery
- Runs periodic tasks at specified intervals
- Generates weekly/monthly reports
- Cleans up old data

### Web Server & Reverse Proxy
**Nginx** - High-performance web server and reverse proxy
- Routes requests to appropriate services (Django, Flask AI)
- Handles SSL/TLS termination
- Serves static files efficiently
- Load balancing across multiple workers
- Configurable timeouts for long-running requests

**Gunicorn** - WSGI HTTP Server
- Runs Django application with multiple worker processes
- Handles concurrent requests efficiently
- Graceful reload and worker management

### Frontend
**HTML/CSS/JavaScript** - Client-side interface
- Responsive design for mobile and desktop
- Form validation and error handling
- Real-time updates via WebSocket
- Image upload and preview

**Tailwind CSS** - Utility-first CSS framework
- Rapid UI development
- Consistent styling across components
- Mobile-first responsive design

### Containerization & Orchestration
**Docker** - Container platform
- Packages each service in isolated containers
- Ensures consistency across development and production
- Easy deployment and scaling

**Docker Compose** - Multi-container orchestration
- Defines and runs all services together
- Manages networking between containers
- Simplifies local development setup

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Browser                          │
│              (HTML/CSS/JavaScript/Tailwind)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                    HTTP/WebSocket
                         │
        ┌────────────────▼────────────────┐
        │         Nginx (Reverse Proxy)   │
        │    - Route requests             │
        │    - SSL termination            │
        │    - Static file serving        │
        └────┬──────────────┬─────────────┘
             │              │
        ┌────▼──────┐  ┌────▼──────────┐
        │  Django   │  │  Flask AI     │
        │  (DRF)    │  │  (Image Anal) │
        │ Gunicorn  │  │  Gunicorn     │
        └────┬──────┘  └────┬──────────┘
             │              │
        ┌────▼──────────────▼──────┐
        │      MongoDB Database    │
        │  - Users                 │
        │  - Issues                │
        │  - Notifications         │
        │  - Audit logs            │
        └──────────────────────────┘
             │
        ┌────▼──────────┐
        │  Redis Cache  │
        │  - Sessions   │
        │  - Messages   │
        │  - Cache      │
        └────┬──────────┘
             │
        ┌────▼──────────┐
        │  Celery Queue │
        │  - Tasks      │
        │  - Scheduler  │
        └───────────────┘
             │
        ┌────▼──────────┐
        │  Ollama LLM   │
        │  - LLaVA 7B   │
        │  - Image AI   │
        └───────────────┘
```

## How Django is Used

### 1. **User Authentication & Authorization**
```python
# Django handles user registration, login, and permissions
- User models with role-based access (citizen, officer, admin)
- JWT token authentication for API endpoints
- Permission classes to restrict access to specific endpoints
```

### 2. **REST API Endpoints**
```python
# Django REST Framework provides:
- /api/auth/login - User authentication
- /api/issues/ - CRUD operations for civic issues
- /api/notifications/ - Real-time notifications
- /api/dashboard/ - Analytics and reporting
- /api/users/ - User management
```

### 3. **Database Models**
```python
# Django ORM models define data structure:
- User model: stores user information and roles
- Issue model: stores reported civic problems
- Notification model: tracks user notifications
- AuditLog model: maintains activity history
```

### 4. **WebSocket Connections**
```python
# Django Channels handles real-time updates:
- Connects users to notification channels
- Broadcasts issue updates to relevant users
- Maintains persistent connections
```

### 5. **Middleware & Utilities**
```python
# Django provides:
- CORS handling for cross-origin requests
- Request/response logging
- Error handling and exception management
- Static file serving
```

## How MongoDB is Used

### 1. **Document Storage**
```javascript
// MongoDB stores flexible documents:
{
  "_id": ObjectId("..."),
  "user_id": "user123",
  "title": "Pothole on Main Street",
  "description": "Large pothole causing traffic issues",
  "category": "Roads",
  "location": {
    "latitude": 10.123,
    "longitude": 76.456,
    "address": "Main Street, District"
  },
  "images": ["image_url_1", "image_url_2"],
  "status": "open",
  "priority": 4,
  "created_at": ISODate("2026-04-26T14:30:00Z"),
  "updated_at": ISODate("2026-04-26T14:30:00Z")
}
```

### 2. **Collections**
- **users** - User accounts and profiles
- **issues** - Reported civic problems
- **notifications** - User notifications
- **audit_logs** - Activity tracking
- **comments** - Issue discussions

### 3. **Advantages Over SQL**
- **Flexible Schema**: Add new fields without migrations
- **Nested Documents**: Store related data together
- **Scalability**: Horizontal scaling across multiple servers
- **Performance**: Fast queries on indexed fields
- **JSON-like**: Natural fit with Python dictionaries

### 4. **Indexing Strategy**
```javascript
// Indexes for fast queries:
db.issues.createIndex({ "user_id": 1 })
db.issues.createIndex({ "category": 1 })
db.issues.createIndex({ "status": 1 })
db.issues.createIndex({ "created_at": -1 })
db.issues.createIndex({ "location": "2dsphere" }) // Geospatial
```

## Service Communication

### Django ↔ Flask AI
- Django receives image upload from client
- Sends image to Flask AI service via HTTP POST
- Flask AI analyzes image with Ollama
- Returns AI-generated title, description, category
- Django stores result in MongoDB

### Django ↔ Redis
- Stores session data for WebSocket connections
- Caches frequently accessed data
- Message broker for Celery tasks

### Django ↔ Celery
- Queues long-running tasks (notifications, reports)
- Celery workers process tasks asynchronously
- Results stored back in MongoDB

### Flask AI ↔ Ollama
- Flask AI sends image to Ollama
- Ollama runs LLaVA model for image analysis
- Returns structured analysis (title, description, category)

## Deployment Flow

1. **Docker Build**: Each service built into container image
2. **Docker Compose**: All services started together
3. **Nginx**: Routes traffic to appropriate service
4. **Django**: Handles business logic and API
5. **MongoDB**: Persists all data
6. **Redis**: Manages sessions and messages
7. **Celery**: Processes background tasks
8. **Flask AI**: Analyzes images with Ollama

## Quick Start

### Prerequisites
- Docker and Docker Compose
- 8GB RAM minimum
- 20GB disk space (for Ollama model)

### Setup
```bash
# Clone repository
git clone https://github.com/nandakumar2k794/python-project.git
cd python-project/civic-report

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# Access application
# Frontend: http://localhost
# API: http://localhost/api/
# MongoDB: localhost:27017
```

### Services
- **Django**: http://localhost (port 8000 internally)
- **Flask AI**: http://localhost/ai/ (port 5001 internally)
- **MongoDB**: localhost:27017
- **Redis**: localhost:6379
- **Ollama**: localhost:11434

## Key Features

✅ **Citizen Reporting** - Upload issue photos with location
✅ **AI Image Analysis** - Automatic categorization using Ollama
✅ **Real-time Updates** - WebSocket notifications
✅ **Officer Dashboard** - Track and manage issues
✅ **Analytics** - Weekly/monthly reports
✅ **Offline AI** - No external API dependencies
✅ **Scalable** - Horizontal scaling with Docker
✅ **Secure** - JWT authentication, role-based access

## Performance Considerations

- **Nginx Timeout**: 150s for AI analysis requests
- **Ollama Timeout**: 120s for image processing
- **Database Indexes**: Optimized for common queries
- **Redis Caching**: Reduces database load
- **Celery Workers**: Async processing prevents blocking
- **Image Compression**: Reduces upload size and processing time

## Troubleshooting

### 504 Gateway Timeout
- Increase nginx timeout in `nginx/nginx.conf`
- Check Ollama is running: `docker-compose logs ollama`

### MongoDB Connection Error
- Verify MongoDB is healthy: `docker-compose ps`
- Check connection string in Django settings

### WebSocket Not Working
- Ensure Redis is running
- Check Django Channels configuration
- Verify browser supports WebSocket

## License

MIT License - See LICENSE file for details
