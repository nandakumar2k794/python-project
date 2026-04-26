# AI Image Description Generator - Setup & Usage Guide

## Quick Start

### 1. Start the Full Stack
```bash
cd civic-report
docker-compose up -d
```

This will automatically start:
- **Ollama** (image analysis engine)
- **Flask AI Service** (API wrapper)
- **Django** (web application)
- **MongoDB** (data storage)
- **Redis** (caching)
- **Nginx** (reverse proxy)

### 2. Wait for Services to Be Ready
```bash
# Check service health
docker-compose ps

# Should show all services as "Up"
```

### 3. Access the Application
- Web UI: http://localhost
- Django API: http://localhost:8000
- Flask AI API: http://localhost:5001
- Ollama API: http://localhost:11434

### 4. Create a Report with AI Image Analysis
1. Log in as a citizen account
2. Go to "Report a Civic Issue"
3. Fill in Step 1 (Category) and Step 2 (Location)
4. On Step 3, upload an image
5. Click "✨ Generate Description from Media"
6. AI will analyze the image and auto-fill the title and description
7. Edit if needed and proceed to final step
8. Submit the report

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   User Browser                          │
│  Report Form with Image Upload                         │
└──────────────┬──────────────────────────────────────────┘
               │ POST /api/dashboard/ai/describe-issue/
               ↓
┌─────────────────────────────────────────────────────────┐
│          Django Application (Port 8000)                │
│  ✓ Authentication ✓ Rate Limiting ✓ Request Validation │
└──────────────┬──────────────────────────────────────────┘
               │ POST /ai/describe-issue
               ↓
┌─────────────────────────────────────────────────────────┐
│        Flask AI Service (Port 5001)                    │
│  ✓ Ollama Health Check                                 │
│  ✓ Fallback Decision Logic                             │
└──┬────────────────────┬────────────────────────────────┐
   │                    │
   ↓ Available          ↓ Not Available
┌──────────────┐  ┌──────────────┐
│   OLLAMA     │  │   GEMINI     │
│ (Free/Local) │  │  (Paid/API)  │
│ Port 11434   │  │  Google Cloud│
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                ↓
        Response (title, description,
                  category, priority)
```

## Service Details

### Ollama Service (LLaVA)
- **Container**: `civic-report-ollama-1`
- **Port**: 11434
- **Models**: llava:7b (default)
- **Features**:
  - Completely free
  - No rate limits
  - Local processing
  - Privacy-friendly (no data sent to external servers)

**First Time Setup**:
- First request will download the model (~1.4GB)
- Subsequent requests are faster
- Model is cached in `ollama_data` Docker volume

### Flask AI Service
- **Container**: `civic-report-flask_ai-1`
- **Port**: 5001
- **Routes**:
  - `GET /health` - Service status
  - `POST /ai/describe-issue` - Image analysis
  - `POST /ai/report-assist` - Text improvement
  - `POST /ai/issue-insights` - Issue analysis

### Django Proxy
- **Endpoint**: `/api/dashboard/ai/describe-issue/`
- **Auth**: Required (authenticated users only)
- **Timeout**: 30 seconds
- **Rate Limit**: Per-user rate limiting applied

## Environment Configuration

### Main .env File
Located at `civic-report/.env`:

```env
# Ollama Configuration
FLASK_AI_SERVICE_URL=http://flask_ai:5001

# Optional: Gemini Fallback
GEMINI_API_KEY=your-api-key-here
```

### Flask .env File
Located at `flask_ai_service/.env`:

```env
# Ollama Configuration (for local development)
OLLAMA_HOST=http://localhost:11434

# Or in Docker (container-to-container networking)
OLLAMA_HOST=http://ollama:11434

# Gemini Fallback (optional)
GEMINI_API_KEY=your-api-key-here
```

## Testing & Debugging

### 1. Run Test Suite
```bash
python test_ai_image_description.py
```

This will test:
- Ollama connectivity
- Flask service health
- Response parsing
- Image analysis workflow

### 2. Check Service Logs
```bash
# Ollama logs
docker logs civic-report-ollama-1

# Flask logs
docker logs civic-report-flask_ai-1

# Django logs
docker logs civic-report-django-1
```

### 3. Manual API Testing
```bash
# Test Flask health
curl http://localhost:5001/health

# Test image analysis (requires valid base64 image)
curl -X POST http://localhost:5001/ai/describe-issue \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/...",
    "category": "Roads",
    "address": "Main Street"
  }'

# Test Django endpoint (requires authentication)
curl -X POST http://localhost:8000/api/dashboard/ai/describe-issue/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/...",
    "category": "Roads",
    "address": "Main Street"
  }'
```

### 4. Monitor Performance
```bash
# Check Ollama memory usage
docker stats civic-report-ollama-1

# Check Flask service performance
docker stats civic-report-flask_ai-1
```

## Troubleshooting

### Problem: "Ollama service is not responding"
**Solution**:
1. Check if Ollama container is running:
   ```bash
   docker ps | grep ollama
   ```
2. Check Ollama logs:
   ```bash
   docker logs civic-report-ollama-1
   ```
3. Restart the service:
   ```bash
   docker-compose restart ollama
   ```

### Problem: Image analysis is slow
**Expected behavior**:
- First request: 30-120 seconds (model initialization + inference)
- Subsequent requests: 5-15 seconds

**Optimization tips**:
- Ensure Docker has sufficient CPU allocated
- Check system resource usage: `docker stats`
- Consider using a faster machine for production

### Problem: Gemini API being used instead of Ollama
**Solution**:
1. Verify Ollama is healthy:
   ```bash
   curl http://localhost:11434/api/tags
   ```
2. Check Flask logs for connection attempts:
   ```bash
   docker logs civic-report-flask_ai-1 | grep -i ollama
   ```
3. Verify OLLAMA_HOST environment variable is set correctly

### Problem: Rate limit errors from Gemini
**Solution**:
1. Ensure Ollama is running (primary provider)
2. Implement request caching with Redis
3. Monitor API usage in Google Cloud Console

## Performance Optimization

### 1. Enable Response Caching
```python
# In Django settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'civic_ai',
        'TIMEOUT': 3600,  # 1 hour
    }
}
```

### 2. Use LLaVA 13b for Better Accuracy
Edit `flask_ai_service/utils/ollama_client.py`:
```python
OLLAMA_MODEL = 'llava:13b'  # Instead of llava:7b
```
Note: Requires more memory (~4-6GB)

### 3. Implement Batch Processing
For bulk image analysis, consider:
- Submitting multiple images asynchronously
- Using Celery tasks for background processing
- Caching similar image analyses

## Security Considerations

### Image Data Handling
- ✓ Images are processed locally when using Ollama
- ✓ No image storage (processed in memory)
- ✓ No telemetry or analytics on image content
- ⚠ Gemini API respects Google's privacy policies

### API Security
- ✓ Django proxy requires authentication
- ✓ Rate limiting prevents abuse
- ✓ CORS properly configured
- ✓ Input validation on all endpoints

### Best Practices
1. Keep `GEMINI_API_KEY` in environment variables only
2. Don't commit `.env` files to version control
3. Monitor API usage for anomalies
4. Use HTTPS in production
5. Implement IP whitelisting if needed

## Advanced Configuration

### Custom Ollama Model
To use a different vision model:

```bash
# List available models
curl http://localhost:11434/api/tags

# Pull a different model
curl -X POST http://localhost:11434/api/pull \
  -d '{"name": "llava:13b"}'

# Update environment variable
OLLAMA_MODEL=llava:13b
```

### Increase Model Timeout
Edit `flask_ai_service/utils/ollama_client.py`:
```python
response = requests.post(url, json=payload, timeout=180)  # 3 minutes
```

### Custom Response Processing
Edit `parse_ollama_response()` function to handle different response formats or add additional fields.

## Monitoring & Logging

### Enable Debug Logging
```bash
# Set environment variable
FLASK_DEBUG=True
DJANGO_DEBUG=True

# Restart services
docker-compose restart
```

### Log Aggregation
For production, integrate with:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Sentry (error tracking)
- DataDog (monitoring)

### Metrics to Monitor
- Image analysis latency
- Ollama/Gemini success rate
- Error rate and types
- Cache hit ratio
- API response times

## Maintenance

### Regular Tasks
- Monitor disk space (Ollama models take space)
- Update Docker images periodically
- Check logs for errors
- Monitor API rate limits (if using Gemini)

### Cleanup
```bash
# Clean up old Docker images
docker image prune

# Clean up unused volumes
docker volume prune

# Clear Ollama cache (if needed)
docker-compose exec ollama rm -rf /root/.ollama/models
```

## Performance Benchmarks

### Response Times (measured on local machine)
| Operation | Time | Notes |
|-----------|------|-------|
| Ollama health check | <100ms | Very fast |
| First image analysis (Ollama) | 40-120s | Model init + inference |
| Subsequent image analysis (Ollama) | 5-20s | Inference only |
| Image analysis (Gemini) | 3-10s | Cloud-based |
| Response parsing | <50ms | Local parsing |
| Django proxy overhead | <200ms | Auth + validation |

## Resources

- [Ollama Documentation](https://ollama.ai)
- [LLaVA Model](https://huggingface.co/liuhaotian/llava-v1.5-7b)
- [Gemini API](https://ai.google.dev)
- [Docker Documentation](https://docs.docker.com)

## Support

For issues or questions:
1. Check logs: `docker logs [service-name]`
2. Run test suite: `python test_ai_image_description.py`
3. Review this guide for similar issues
4. Check GitHub issues: [civic-report-issues](https://github.com/civic-report/issues)

## License
This AI image description generator is part of the Civic Report App. See LICENSE file for details.
