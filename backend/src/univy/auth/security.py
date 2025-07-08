from fastapi_nextauth_jwt import NextAuthJWT
from typing import Annotated
from univy.config import settings
from fastapi import Depends
from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str
    email: str


JWT = NextAuthJWT(secret=settings.AUTH_SECRET,
                  csrf_prevention_enabled=settings.CSRF_PREVENTION_ENABLED)

    
async def get_current_user(jwt: Annotated[User, Depends(JWT)]) -> User:
    return User(id=jwt["id"], name=jwt["name"], email=jwt["email"])

'''
TODO: Implement database session strategy with fastapi by querying the session table in the database
since the auth token is always in the request when credentials are provided, we can use that to get the session id and then query the database for the session.




'''
