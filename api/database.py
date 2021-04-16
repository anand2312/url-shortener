"""Database utilities for the application."""
from functools import wraps
from typing import (
    Any,
    AsyncGenerator,
    AsyncGenerator,
    Awaitable,
    Callable,
    List,
    Mapping,
    Optional,
)

from databases import Database as _Database


class DatabaseNotConnectedError(Exception):
    """Exception raised when any queries are attempted before the connection was made
    using the `Database.connect` method."""

    pass


def is_connected(
    func: Callable[[Any], Awaitable[Any]]
) -> Callable[[Any], Awaitable[Any]]:
    """
    A decorator which checks if the connection has been initialized using the
    `Database.connect` method before running any queries.
    Raises ::
        DatabaseNotConnectedError`
    """

    @wraps(func)
    async def wrapper(ref, *args, **kwargs):
        if not ref.is_connected:
            raise DatabaseNotConnectedError
        else:
            return await func(ref, *args, **kwargs)

    return wrapper


class Database:
    """Represents a connection to the underlying database."""

    def __init__(self, connection_uri: str) -> None:
        """
        Initializes a database instance.
        The database does not CONNECT until the `Database.connect` coroutine is called.

        Arguments:
            connection_uri: The database connection URI.
        """
        self.db = _Database(connection_uri)
        self.is_connected = False

    async def connect(self) -> None:
        """Establishes the connection with the database."""
        await self.db.connect()
        self.is_connected = True

    @is_connected
    async def disconnect(self) -> None:
        """Disconnects the connection with the database."""
        await self.db.disconnect()
        self.is_connected = False

    @is_connected
    async def initialize_tables(self) -> None:
        """
        Creates the tables in the database if they haven't been made already.
        """
        urls = """CREATE TABLE IF NOT EXISTS urls(short CHAR(10) PRIMARY KEY, long VARCHAR(500) NOT NULL, clicks INT DEFAULT 0, created_at TIMESTAMP DEFAULT (now() AT TIME ZONE 'utc'), created_by CHAR(20) REFERENCES users(uid))"""
        authenticated_users = """CREATE TABLE IF NOT EXISTS users(uid CHAR(20) PRIMARY KEY, token CHAR(13) UNIQUE NOT NULL"""
        await self.db.execute(query=urls)
        await self.db.execute(query=authenticated_users)

    @is_connected
    async def execute(self, query: str, **kwargs: Any) -> str:
        return await self.db.execute(query=query, values=kwargs)

    @is_connected
    async def executemany(self, query: str, *args: Any) -> str:
        return await self.db.execute_many(query=query, values=args)

    @is_connected
    async def fetch(self, query: str, **kwargs: Any) -> List[Mapping]:
        return await self.db.fetch_all(query=query, values=kwargs)

    @is_connected
    async def fetchrow(self, query: str, **kwargs: Any) -> Optional[Mapping]:
        return await self.db.fetch_one(query=query, values=kwargs)

    @is_connected
    async def fetchval(self, query: str, **kwargs: Any) -> Optional[Any]:
        return await self.db.fetch_one(query=query, values=kwargs)

    @is_connected
    async def iterate(self, query: str, **kwargs: Any) -> AsyncGenerator[Mapping, None]:
        # to be used like a cursor, in case large amounts of data is to be retrieved
        async for record in self.db.iterate(query=query, values=kwargs):
            yield record
