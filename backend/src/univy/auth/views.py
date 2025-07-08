from fastapi import APIRouter, Depends
from univy.auth.security import get_current_user, JWT
from typing import Annotated
from univy.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/test-auth")
async def return_jwt(jwt: Annotated[dict, Depends(JWT)]):
    return {"message": f"Hi {jwt['name']}. Greetings from fastapi!"}


@router.get("/read-user")
async def read_user(jwt: Annotated[str, Depends(get_current_user)]):
    return jwt
