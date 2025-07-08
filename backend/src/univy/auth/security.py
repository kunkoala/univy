from fastapi_nextauth_jwt import NextAuthJWT
from univy.config import settings

JWT = NextAuthJWT(secret=settings.AUTH_SECRET)

'''
TODO: Implement database session strategy with fastapi by querying the session table in the database
since the auth token is always in the request when credentials are provided, we can use that to get the session id and then query the database for the session.




'''