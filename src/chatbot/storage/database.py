"""
Database connection and session management.

This module handles:
- Creating the async database engine
- Configuring connection pooling
- Providing async session factories
- Creating database tables
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chatbot.storage.models import Base


class DatabaseManager:
    """
    Manages database connections and sessions.

    This class follows the singleton pattern - only one instance should exist
    per application. It handles:
    - Creating and configuring the async engine
    - Providing session factories
    - Creating/dropping tables
    """

    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize the database manager.

        Args:
            database_url: SQLAlchemy database URL
                - SQLite: "sqlite+aiosqlite:///./chatbot.db"
                - PostgreSQL: "postgresql+asyncpg://user:pass@host/db"
            echo: If True, log all SQL queries (useful for debugging)
        """
        # Create async engine
        # Engine = manages the connection pool and database driver
        self.engine = create_async_engine(
            database_url,
            echo=echo,  # Log SQL if True
            # Connection pool settings
            pool_size=5,  # Keep 5 connections ready
            max_overflow=10,  # Can create 10 more if needed
            pool_pre_ping=True,  # Test connections before using (prevents stale connections)
            pool_recycle=3600,  # Recycle connections after 1 hour
        )

        # Create session factory
        # sessionmaker = factory for creating Session objects
        # async_sessionmaker = async version for async/await
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,  # Use AsyncSession for async operations
            expire_on_commit=False,  # Don't expire objects after commit (we might access them)
            autoflush=False,  # Don't auto-flush (we'll do it manually for control)
            autocommit=False,  # Use explicit commits for safety
        )

    async def create_tables(self) -> None:
        """
        Create all tables defined in the models.

        This uses the Base.metadata to create all tables that inherit from Base.
        In production, you'd use Alembic migrations instead.

        Note: This is idempotent - safe to call multiple times.
        SQLAlchemy will only create tables that don't exist.
        """
        async with self.engine.begin() as conn:
            # run_sync: Run synchronous code in async context
            # create_all: Create all tables defined in Base
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """
        Drop all tables defined in the models.

        ⚠️ WARNING: This deletes ALL data!
        Only use for testing or development.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session.

        This is a context manager that:
        1. Creates a new session
        2. Yields it for use
        3. Commits if no exceptions
        4. Rolls back if exceptions occur
        5. Closes the session

        Usage:
            async with db_manager.get_session() as session:
                result = await session.execute(...)
                # Session is automatically committed and closed

        Yields:
            AsyncSession: Database session for queries
        """
        async with self.async_session() as session:
            try:
                yield session
                # Commit if no exceptions
                await session.commit()
            except Exception:
                # Rollback on any exception
                await session.rollback()
                raise
            finally:
                # Always close the session
                await session.close()

    async def close(self) -> None:
        """
        Close the database engine and all connections.

        Call this when shutting down the application to cleanly
        close all database connections.
        """
        await self.engine.dispose()


# Global database manager instance
# This will be initialized in the FastAPI startup event
_db_manager: DatabaseManager | None = None


def init_db(database_url: str, echo: bool = False) -> DatabaseManager:
    """
    Initialize the global database manager.

    Call this once at application startup.

    Args:
        database_url: SQLAlchemy database URL
        echo: If True, log all SQL queries

    Returns:
        DatabaseManager: The initialized database manager
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url, echo=echo)
    return _db_manager


def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance.

    Raises:
        RuntimeError: If database not initialized (forgot to call init_db)

    Returns:
        DatabaseManager: The global database manager
    """
    if _db_manager is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first "
            "(usually in FastAPI startup event)."
        )
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting a database session.

    Usage in routes:
        @app.post("/chat")
        async def chat(
            request: ChatRequest,
            db: AsyncSession = Depends(get_db_session)
        ):
            # Use db here
            result = await db.execute(...)

    The session is automatically:
    - Created at the start of the request
    - Committed if the request succeeds
    - Rolled back if an exception occurs
    - Closed at the end of the request

    Yields:
        AsyncSession: Database session
    """
    db_manager = get_db_manager()
    async for session in db_manager.get_session():
        yield session


# Key Concepts Explained:
#
# 1. create_async_engine() - Creates the database connection manager
#    - Manages connection pooling
#    - Handles database driver (aiosqlite, asyncpg)
#    - Configures connection lifecycle
#
# 2. async_sessionmaker() - Factory for creating sessions
#    - Sessions = units of work (like transactions)
#    - Each request gets its own session
#    - Sessions are NOT thread-safe (one per async task)
#
# 3. Connection Pool - Reuses database connections
#    - pool_size: Keep this many connections open
#    - max_overflow: Can create more if busy
#    - pool_pre_ping: Test before use (detect stale connections)
#    - pool_recycle: Refresh connections periodically
#
# 4. Session Lifecycle:
#    - Create: async_session()
#    - Use: execute queries
#    - Commit: Save changes
#    - Rollback: Undo on error
#    - Close: Release connection back to pool
#
# 5. FastAPI Integration:
#    - Depends(get_db_session): Inject session into routes
#    - Automatic cleanup via context manager
#    - One session per request (isolated)
