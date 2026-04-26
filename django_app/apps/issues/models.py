from mongoengine import Document,StringField,DateTimeField,ListField,DictField,IntField,BooleanField
from datetime import datetime,timedelta
from uuid import uuid4
class Ward(Document):
    name=StringField(required=True); district=StringField(required=True); boundary_geojson=DictField(default=dict); officer_ids=ListField(StringField()); stats=DictField(default=dict)
class Issue(Document):
    issue_code=StringField(required=True,unique=True,sparse=True,default=lambda: str(uuid4())); title=StringField(required=True); description=StringField(required=True); category=StringField(required=True); sub_category=StringField(); status=StringField(default="Submitted"); priority=IntField(default=3); location=DictField(default=dict); photos=ListField(StringField()); work_proof=ListField(DictField(), default=list); reported_by=StringField(required=True); assigned_to=StringField(); upvotes=ListField(StringField()); ai_meta=DictField(default=dict); timeline=ListField(DictField(),default=list); created_at=DateTimeField(default=datetime.utcnow); updated_at=DateTimeField(default=datetime.utcnow); resolved_at=DateTimeField(); sla_deadline=DateTimeField(default=lambda: datetime.utcnow()+timedelta(hours=72))
class Comment(Document):
    issue_id=StringField(required=True); author_id=StringField(required=True); text=StringField(required=True); is_internal=BooleanField(default=False); is_flagged=BooleanField(default=False); created_at=DateTimeField(default=datetime.utcnow)
