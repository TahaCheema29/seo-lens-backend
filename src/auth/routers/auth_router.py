from fastapi import APIRouter, Depends, status

from src.auth.schemas.schemas import LoginRequest, SignupRequest
from src.auth.service.auth_service import AuthService
from src.utils.response_helper import create_response
from src.constants.response_status import RESPONSE_STATUS_SUCCESS


router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service() -> AuthService:
    return AuthService()


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    token = await auth_service.signup(email=payload.email, password=payload.password)
    return create_response(RESPONSE_STATUS_SUCCESS, "Signup successful", token.model_dump())


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    token = await auth_service.login(email=payload.email, password=payload.password)
    return create_response(RESPONSE_STATUS_SUCCESS, "Login successful", token.model_dump())

