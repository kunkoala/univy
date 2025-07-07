from fastapi_nextauth_jwt import NextAuthJWT
from univy.config import settings

JWT = NextAuthJWT(secret=settings.AUTH_SECRET)