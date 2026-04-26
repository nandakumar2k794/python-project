# AI Image Description Generator

## Overview
The Civic Report App includes an advanced AI-powered image description generator that automatically analyzes uploaded images to generate issue titles and descriptions. The system uses **Ollama's free LLaVA model** as the primary provider with an automatic fallback to Gemini API.

## Architecture

### Priority Order
1. **Ollama LLaVA (Primary)** - Free, local, no rate limits, no API costs
   - Model: `llava:7b` (lightweight, ~1.4GB)
   - Alternative: `llava:13b` (better accuracy, ~7.9GB)
   - Runs in Docker container for easy deployment

2. **Gemini 2.0 Flash (Fallback)** - Paid API, rate-limited
   - Only used if Ollama is unavailable
   - Requires `GEMINI_API_KEY` environment variable
   - Better for complex analysis but has rate limits

## Services

### Flask AI Service
- **Endpoint**: `/ai/describe-issue` (POST)
- **Port**: 5001
- **Docker Service**: `flask_ai`

**Request Body**:
```json
{
  "image": "data:image/jpeg;base64,...",
  "category": "Roads",
  "address": "Main St, District"
}
```

**Response**:
```json
{
  "title": "Large pothole on Main Street",
  "description": "A significant pothole discovered on Main Street causing safety hazards...",
  "category": "Roads",
  "priority": 4,
  "summary": "Image analyzed with LLaVA",
  "provider": "Ollama (free, local)"
}
```

### Django Proxy Endpoint
- **Endpoint**: `/api/dashboard/ai/describe-issue/` (POST)
- **Authentication**: Required
- **Timeout**: 30 seconds
- **Rate Limiting**: Applied per user

## How It Works

### User Flow
1. Citizen uploads an image in the issue report form (Step 3)
2. Clicks "✨ Generate Description from Media" button
3. Frontend sends base64 image to Django proxy
4. Django forwards to Flask AI service
5. Flask AI service:
   - Checks if Ollama is healthy
   - If yes: Analyzes with LLaVA model
   - If no: Falls back to Gemini API
6. Response is parsed and form fields are auto-populated
7. User can edit the generated text or submit as-is

### Image Processing
- Supported formats: JPG, PNG, WebP, GIF
- Base64 encoding for transport
- Automatic data URL prefix removal
- Image size: No specific limit (processed locally)

### Response Parsing

**Ollama Response Format**:
```
TITLE: [Generated title]
DESCRIPTION: [Multi-line description]
CATEGORY: [Category name]
PRIORITY: [1-5]
```

**Gemini Response Format**: JSON structure with same fields

## Configuration

### Environment Variables
```env
# Ollama Configuration
OLLAMA_HOST=http://ollama:11434

# Gemini Fallback (optional)
GEMINI_API_KEY=your-api-key-here

# Flask Service
FLASK_AI_SERVICE_URL=http://flask_ai:5001
```

### Docker Compose
The `docker-compose.yml` includes the complete stack:
- **ollama**: Runs Ollama with LLaVA model
- **flask_ai**: Flask AI service
- **django**: Django application with proxy endpoints
- **mongodb**: Data storage
- **redis**: Caching and task queue
- **nginx**: Reverse proxy

## Features

### ✅ Free Local AI
- No API costs when Ollama is running
- No rate limiting for image analysis
- Fully local processing for privacy

### ✅ Automatic Fallback
- Seamless fallback to Gemini API if Ollama fails
- Users are notified of the provider being used
- Error handling for rate limits and timeouts

### ✅ Smart Categorization
- AI suggests the most appropriate category
- Respects user's initial category selection as context
- Validates categories against predefined list

### ✅ Priority Detection
- AI estimates issue priority (1-5)
- Based on severity indicators in the image

### ✅ Robust Error Handling
- Timeout protection (120s for Ollama, 30s for Gemini)
- Graceful fallback to user manual entry
- Detailed error messages for debugging

## Deployment

### Docker
```bash
docker-compose up -d
```

The stack will automatically:
1. Pull and run Ollama
2. Deploy Flask AI service
3. Setup Django application
4. Configure all networking

### Local Development
```bash
# Start only Flask AI and dependencies
docker-compose up -d ollama flask_ai mongodb

# In another terminal, run Django
cd django_app
python manage.py runserver
```

### Manual Testing
```bash
# Check Flask AI health
curl http://localhost:5001/health

# Test image analysis
curl -X POST http://localhost:5001/ai/describe-issue \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,...",
    "category": "Roads",
    "address": "Main Street"
  }'
```

## Monitoring

### Health Checks
```bash
# Flask AI service
curl http://localhost:5001/health

# Response includes Ollama availability
{
  "status": "ok",
  "ai_provider": "ollama",
  "ollama_available": true
}
```

### Logs
```bash
# Flask service logs
docker logs civic-report-flask_ai-1

# Ollama logs
docker logs civic-report-ollama-1
```

## Performance

### Ollama (LLaVA 7b)
- First analysis: ~30-60 seconds (includes model loading)
- Subsequent analyses: ~5-15 seconds
- Memory: ~2GB during inference
- CPU: Variable (optimized for efficiency)

### Gemini API
- First analysis: ~3-10 seconds
- Memory: Minimal (cloud-based)
- Cost: Per API call ($0.00001-$0.00002 per image approx)

## Troubleshooting

### Ollama Not Available
1. Check Docker container: `docker ps | grep ollama`
2. Check logs: `docker logs civic-report-ollama-1`
3. Verify connectivity: `curl http://ollama:11434/api/tags`
4. Service will automatically fallback to Gemini

### Slow Image Analysis
- First request is slower due to model initialization
- LLaVA 7b is optimized for speed/accuracy trade-off
- Consider LLaVA 13b for better accuracy (slower)
- Ensure sufficient CPU resources allocated to Docker

### Rate Limited
- Ollama: No limits (fully local)
- Gemini: Wait 1-5 minutes before retry
- Check `GEMINI_API_KEY` validity
- Monitor usage in Google Cloud Console

### Form Not Populating
1. Check browser console for JavaScript errors
2. Verify Django proxy endpoint: `/api/dashboard/ai/describe-issue/`
3. Check Flask service logs for parsing errors
4. Ensure image is valid and within size limits

## Future Enhancements

- [ ] Batch image analysis for multiple images
- [ ] Video frame extraction for video analysis
- [ ] Custom model fine-tuning for civic issues
- [ ] Model caching for frequently analyzed issue types
- [ ] Real-time analysis streaming
- [ ] Confidence score visualization
- [ ] Analysis result caching with Redis

## Security Considerations

- Images are only processed, never stored
- No telemetry or analytics on image content
- Local Ollama processing keeps data on-premises
- Gemini API respects Google's data handling policies
- API keys are environment-variable based

## API Integration

### For Developers
```javascript
// Frontend usage
const response = await fetch('/api/dashboard/ai/describe-issue/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    image: base64ImageData,
    category: 'Roads',
    address: 'Specific location'
  })
});

const result = await response.json();
console.log(result.title);      // "Large pothole..."
console.log(result.description); // "A significant pothole..."
console.log(result.provider);    // "Ollama (free, local)"
```

## References

- [Ollama Documentation](https://ollama.ai/library/llava)
- [LLaVA Model Card](https://huggingface.co/liuhaotian/llava-v1.5-7b)
- [Gemini API Documentation](https://ai.google.dev/)
- [Civic Report GitHub](https://github.com/civic-report)
