from mongoengine import Document,StringField,BooleanField,DateTimeField
from datetime import datetime
class User(Document):
    supabase_uid=StringField()
    name=StringField(required=True)
    email=StringField(required=True,unique=True)
    role=StringField(default="citizen")
    ward=StringField()
    phone=StringField()
    avatar_url=StringField()
    is_verified=BooleanField(default=True)
    password_hash=StringField(required=True)
    created_at=DateTimeField(default=datetime.utcnow)
    
    @property
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return True

    @property
    def is_active(self):
        """Return True if the user account is active."""
        return True

    @property
    def is_anonymous(self):
        """Return False since this is a real user."""
        return False

    @property
    def is_staff(self):
        """Return True for admin users."""
        return self.role == "admin"

    @property
    def is_superuser(self):
        """Return True for admin users."""
        return self.role == "admin"

    def has_module_perms(self, app_label):
        """Return True for admin users."""
        return self.role == "admin"

    def has_perm(self, perm, obj=None):
        """Return True for admin users."""
        return self.role == "admin"
