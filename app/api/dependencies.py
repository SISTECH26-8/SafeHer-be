from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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


security = HTTPBearer(auto_error=False)

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Extracts and validates the JWT from the Authorization header.
    Returns the user_id (UUID string) from the token subject.
    """
    if not credentials:
        exc.auth_missing_token()

    token = credentials.credentials
    try:
        user_id = decode_access_token(token)
        return user_id
    except ExpiredSignatureError:
        exc.auth_token_expired()
    except JWTError:
        exc.auth_invalid_token()
