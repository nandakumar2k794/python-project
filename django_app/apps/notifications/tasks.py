import requests
from celery import shared_task
from django.conf import settings
@shared_task
def send_status_email(to_email, issue_code, old_status, new_status):
    return {"sent":True,"to":to_email,"issue_code":issue_code,"before":old_status,"after":new_status}
@shared_task
def send_weekly_ai_summary():
    return requests.post(f"{settings.FLASK_AI_SERVICE_URL}/ai/weekly-report",json={"ward_id":"all"},timeout=20).json()
