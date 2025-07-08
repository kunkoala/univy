from fastapi import APIRouter, Depends, Request
from univy.auth.security import JWT
from typing import Annotated
from univy.config import settings
from fastapi import Request

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/test-auth")
async def return_jwt(jwt: Annotated[dict, Depends(JWT)]):
    return {"message": f"Hi {jwt['name']}. Greetings from fastapi!"}


@router.get("/test-endpoint")
async def test_endpoint():
    return {"message": f"Endpoint Works!, Next Secret: {settings.AUTH_SECRET}"}


@router.get("/test-cookies")
async def test_cookies(request: Request):
    cookies = request.cookies
    print("Received cookies:", cookies)
    return {"cookies": dict(cookies)}
