from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User


# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


# HTTP Bearer authentication
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its stored hash."""
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    """Create a JWT for the authenticated user."""

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    return token


def decode_access_token(token: str) -> int:
    """Decode JWT and return the user ID."""

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise ValueError("Token does not contain a user ID")

        return int(user_id)

    except (JWTError, ValueError, TypeError):
        raise ValueError("Invalid or expired token")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get the authenticated user from the JWT."""

    token = credentials.credentials

    try:
        user_id = decode_access_token(token)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user