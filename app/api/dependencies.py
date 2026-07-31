from fastapi import Depends, Header
from sqlalchemy.orm import Session
from jose import JWTError, ExpiredSignatureError
from app.db.session import SessionLocal
from app.core.security import decode_access_token
from app.core import exceptions as exc


def get_db():
    """Yield a SQLAlchemy DB session, ensuring it's closed after each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_id(authorization: str = Header(default=None)) -> str:
    """
    Extracts and validates the JWT from the Authorization header.
    Returns the user_id (UUID string) from the token subject.
    """
    if not authorization or not authorization.startswith("Bearer "):
        exc.auth_missing_token()

    token = authorization.split(" ", 1)[1]
    try:
        user_id = decode_access_token(token)
        return user_id
    except ExpiredSignatureError:
        exc.auth_token_expired()
    except JWTError:
        exc.auth_invalid_token()
