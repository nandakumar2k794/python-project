from mongoengine import Document,StringField,BooleanField,DateTimeField
from datetime import datetime
class Notification(Document):
    user_id=StringField(required=True); type=StringField(required=True); message=StringField(required=True); issue_id=StringField(); is_read=BooleanField(default=False); created_at=DateTimeField(default=datetime.utcnow)
