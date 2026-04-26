import jwt
import bcrypt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User


def _t(uid, mins=30, typ="access"):
    return jwt.encode(
        {"uid": str(uid), "exp": datetime.utcnow() + timedelta(minutes=mins), "type": typ},
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def _hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _verify_password(password, hash_val):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hash_val.encode('utf-8'))
    except Exception:
        return False


class RegisterView(APIView):
    permission_classes = []

    def post(self, r):
        e = r.data.get("email", "").lower().strip()
        n = r.data.get("name", "")
        p = r.data.get("password", "")
        
        if not all([e, n, p]):
            return Response({"detail": "Missing required fields"}, status=400)
        
        if len(p) < 8:
            return Response({"detail": "Password must be at least 8 characters"}, status=400)
        
        if len(n) < 2:
            return Response({"detail": "Name must be at least 2 characters"}, status=400)
        
        # Check if user already exists
        existing = User.objects(email=e).first()
        if existing:
            return Response({"detail": "Email already registered"}, status=400)
        
        try:
            # Create new user with local password
            user = User(
                email=e,
                name=n,
                password_hash=_hash_password(p),
                supabase_uid=f"local_{e}",
                is_verified=True,  # Auto-verify for local auth
                role="citizen"
            )
            user.save()
            
            return Response({
                "detail": "Registration successful. You can now log in.",
                "error": False
            }, status=201)
        except Exception as err:
            return Response({"detail": f"Registration failed: {str(err)}"}, status=500)


class LoginView(APIView):
    permission_classes = []

    def post(self, r):
        e = r.data.get("email", "").lower().strip()
        p = r.data.get("password", "")
        
        if not all([e, p]):
            return Response({"detail": "Missing email or password"}, status=400)
        
        try:
            user = User.objects(email=e).first()
            
            if not user:
                return Response({"detail": "Invalid email or password"}, status=401)
            
            if not user.password_hash or not _verify_password(p, user.password_hash):
                return Response({"detail": "Invalid email or password"}, status=401)
            
            # Generate tokens
            access_token = _t(user.id, mins=60, typ="access")
            refresh_token = _t(user.id, mins=10080, typ="refresh")  # 7 days
            
            return Response({
                "access": access_token,
                "refresh": refresh_token,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                    "is_verified": user.is_verified
                }
            }, status=200)
        except Exception as err:
            return Response({"detail": f"Login failed: {str(err)}"}, status=500)


class RefreshView(APIView):
    permission_classes = []

    def post(self, r):
        token = r.data.get("refresh")
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            if payload.get("type") != "refresh":
                return Response({"detail": "Invalid token type"}, status=400)
            return Response({"access": _t(str(payload["uid"]))})
        except Exception:
            return Response({"detail": "Invalid refresh token"}, status=401)


class LogoutView(APIView):
    def post(self, r):
        return Response({"detail": "Logged out"})
