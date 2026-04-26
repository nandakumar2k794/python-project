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
1. Run `docker compose up --build`
2. Open `http://localhost
