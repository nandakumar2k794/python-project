from mongoengine import Document, StringField, DictField, DateTimeField
from datetime import datetime

class AuditLog(Document):
    actor_id=StringField(required=True)
    action=StringField(required=True)
    resource=StringField(required=True)
    resource_id=StringField(required=True)
    old_value=DictField(default=dict)
    new_value=DictField(default=dict)
    ip=StringField()
    timestamp=DateTimeField(default=datetime.utcnow)
