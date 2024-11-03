from app.config import Config
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extensions import connection, cursor
from typing import Any, List, Optional, Tuple, TypeVar, Generator

T = TypeVar('T')

class DatabaseError(Exception):
    """Custom exception for database-related errors"""
    pass

class ConnectionPool:
    def __init__(self, config: Config):
        self.pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
        )

    @contextmanager
    def get_connection(self) -> Generator[connection, Any, None]:
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)

class Database:
    def __init__(self, config: Config):
        self.pool = ConnectionPool(config)

    @contextmanager
    def transaction(self) -> Generator[cursor, Any, None]:
        """Context manager for database transactions with automatic rollback on error"""
        with self.pool.get_connection() as conn:
            cur = conn.cursor()
            try:
                yield cur
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise DatabaseError(f"Transaction failed: {str(e)}") from e
            finally:
                cur.close()

    def execute(self, query: str, params: Optional[Tuple] = None, fetch: bool = False) -> Optional[List[Tuple]]:
        """Execute a single query with parameters"""
        with self.transaction() as cur:
            cur.execute(query, params)
            return cur.fetchall() if fetch else None

    def executemany(self, query: str, params_list: List[Tuple]) -> None:
        """Execute multiple queries with parameters"""
        with self.transaction() as cur:
            cur.executemany(query, params_list)