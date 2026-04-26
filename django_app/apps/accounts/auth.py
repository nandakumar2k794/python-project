import jwt
from rest_framework import authentication,exceptions
from django.conf import settings
from .models import User
class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self,request):
        h=request.headers.get("Authorization","")
        if not h.startswith("Bearer "): return None
        token=h.split(" ",1)[1]
        try:
            p=jwt.decode(token,settings.JWT_SECRET,algorithms=["HS256"])
            if p.get("type") != "access":
                raise exceptions.AuthenticationFailed("Invalid token type")
            uid = p.get("uid")
            if not uid:
                raise exceptions.AuthenticationFailed("Invalid token payload")
            u=User.objects.get(id=uid)
            return (u,None)
        except jwt.ExpiredSignatureError as e:
            raise exceptions.AuthenticationFailed("Token expired") from e
        except User.DoesNotExist as e:
            raise exceptions.AuthenticationFailed("User not found") from e
        except exceptions.AuthenticationFailed:
            raise
        except Exception as e:
            raise exceptions.AuthenticationFailed("Invalid token") from e
