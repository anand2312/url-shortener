from datetime import datetime
from enum import Enum
from time import time
from functools import wraps

from api.database import Database


class IDType(Enum):
    """Enumeration representing the different kinds of UIDs generated."""

    TOKEN = 3
    SHORT_URL = 10


def generate_uid(id_type: IDType) -> str:
    """
    Generates a unique ID from the current time (based on it's hex).

    Arguments:
        slice_from: The kind of ID to be generated.
    Returns:
        str
    """
    return hex(int(time() * 10000000))[id_type.value :]


async def authenticate_token(db: Database, token: str) -> bool:
    data = await db.fetchrow("SELECT * FROM users WHERE token = :token", token=token)
    if not data:
        return False
    else:
        return True


async def create_short_url(db: Database, token: str, long: str) -> str:
    """
    Creates and registers a new short URL in the database.

    Arguments:
        db: The active Database connection object.
        token: The user's API token.
        long: The original URL to redirect to.
    Returns:
        The generated short URL.
    """
    short = generate_uid(IDType.SHORT_URL)
    created_by = await db.fetchval(
        "SELECT uid FROM users WHERE token = :token", token=token
    )
    print(f"short {short}")
    print(f"Long {long}")
    print(f"created by {created_by}")
    now = datetime.utcnow()

    await db.execute(
        "INSERT INTO urls(short, long, created_by, created_at) VALUES(:short, :long, :created_by, :created_at)",
        short=short,
        long=long,
        created_by=created_by,
        created_at=now,
    )

    return short


async def create_user(db: Database, uid: str) -> str:
    """
    Creates and registers a new user in the database.

    Arguments:
        db: The active Database connection object.
        uid: User's discord user ID.
    Returns:
        The API access token for the user.
    """
    existing = await db.fetchrow("SELECT * FROM users WHERE uid = :uid", uid=uid)
    if not existing:
        token = generate_uid(IDType.TOKEN)
        await db.execute(
            "INSERT INTO users(uid, token) VALUES(:uid, :token)", uid=uid, token=token
        )
    else:
        token = existing["token"]

    return token
