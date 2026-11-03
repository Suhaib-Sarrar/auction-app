import os
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from . import schemas

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + \
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        name = payload.get("sub")
        if name is None:
            raise credentials_exception
        return schemas.TokenData(name=name)
    except JWTError:
        raise credentials_exception


class Hash:
    @staticmethod
    def bcrypt(password: str) -> str:
        return hash_password(password)

    @staticmethod
    def verify(hashed_password: str, plain_password: str) -> bool:
        return verify_password(plain_password, hashed_password)
