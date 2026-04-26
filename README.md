# Civic Issue Reporting System

District-level issue reporting platform using Django, DRF, MongoDB, Flask AI, Channels, Redis, and Celery.

## Architecture
```text
Browser (Tailwind + JS)
      |
    Nginx
  /   |    \
Django FlaskAI WebSocket
  |      |      |
MongoDB  AI    Redis
  |
Celery worker/beat
```

## Run
1. Copy `.env.example` -> `.env`
2. Fill Supabase + AI keys
3. Run `docker compose up --build`
4. Open `http://localhost`
