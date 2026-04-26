import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.accounts.models import User
import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Create a test user
user = User(
    email='testuser@civic.local',
    name='Test User',
    password_hash=hash_password('TestPass123'),
    supabase_uid='local_testuser@civic.local',
    is_verified=True,
    role='citizen'
)
user.save()
print(f"User created successfully!")
print(f"User ID: {user.id}")
print(f"User Email: {user.email}")
print(f"User Name: {user.name}")
