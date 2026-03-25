import datetime as dt

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext

from src.auth.schemas import db
from src.auth.schemas.schemas import AuthTokenResponse
from src.config.settings import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _create_access_token(subject: str, email: str) -> str:
    expire = dt.datetime.utcnow() + dt.timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {"sub": subject, "email": email, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


class AuthService:
    async def signup(self, email: str, password: str) -> AuthTokenResponse:
        # bcrypt will error if the raw password exceeds 72 bytes (UTF-8).
        if len(password.encode("utf-8")) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password too long for bcrypt (max 72 bytes).",
            )

        existing = await db.get_user_by_email(email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        try:
            password_hash = _pwd_context.hash(password)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password too long for bcrypt (max 72 bytes).",
            )

        user = await db.create_user(email=email, password_hash=password_hash)
        token = _create_access_token(subject=str(user["id"]), email=user["email"])
        return AuthTokenResponse(access_token=token)

    async def login(self, email: str, password: str) -> AuthTokenResponse:
        user = await db.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if len(password.encode("utf-8")) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password too long for bcrypt (max 72 bytes).",
            )

        try:
            ok = _pwd_context.verify(password, user["password_hash"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password too long for bcrypt (max 72 bytes).",
            )

        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = _create_access_token(subject=str(user["id"]), email=user["email"])
        return AuthTokenResponse(access_token=token)

