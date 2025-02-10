import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from rest_framework import exceptions
from .models import ActiveTokens


class CustomTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """
        Custom token authentication method.

        Validates JWT token, checks token validity, and user status.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            # Check token in ActiveTokens
            active_token = ActiveTokens.objects.filter(
                token=token,
            ).first()
            if not active_token:
                raise AuthenticationFailed("Invalid or expired token")

            user = active_token.user
            if not user.is_active:
                raise AuthenticationFailed("User account is inactive")

            return (user, token)

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")
        except Exception as e:
            raise AuthenticationFailed(str(e))
