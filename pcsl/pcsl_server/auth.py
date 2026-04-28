# pcsl/pcsl_server/auth.py
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from pathlib import Path
from dotenv import load_dotenv

# Load from ~/.pcsl/.env (created by pcsl init)
load_dotenv(dotenv_path=Path.home() / ".pcsl" / ".env", override=True)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. Run `pcsl init` to generate one, "
        "or set SECRET_KEY in ~/.pcsl/.env"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_token_data(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        scopes: List[str] = payload.get("scopes", [])
        client_id: str = payload.get("client_id", "unknown-client")
        if user_id is None:
            raise credentials_exception
        return {"user_id": user_id, "scopes": scopes, "client_id": client_id}
    except JWTError:
        raise credentials_exception
