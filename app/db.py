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
# from app.config import Config
# from contextlib import contextmanager
# from psycopg2.pool import SimpleConnectionPool
# from psycopg2.extensions import connection, cursor
# from typing import Any, List, Optional, Tuple, TypeVar, Generator
# import psycopg2
# import logging
# from time import sleep

# T = TypeVar('T')

# logger = logging.getLogger(__name__)

# class DatabaseError(Exception):
#     """Custom exception for database-related errors"""
#     pass

# class ConnectionPool:
#     def __init__(self, config: Config):
#         self._create_pool(config)
#         self.max_retries = 3
#         self.retry_delay = 1  # seconds

#     def _create_pool(self, config: Config):
#         try:
#             self.pool = SimpleConnectionPool(
#                 minconn=1,
#                 maxconn=10,
#                 dbname=config.DB_NAME,
#                 user=config.DB_USER,
#                 password=config.DB_PASSWORD,
#                 host=config.DB_HOST,
#                 keepalives=1,
#                 keepalives_idle=30,
#                 keepalives_interval=10,
#                 keepalives_count=5,
#                 connect_timeout=10
#             )
#         except psycopg2.Error as e:
#             logger.error(f"Failed to create connection pool: {str(e)}")
#             raise DatabaseError(f"Could not create connection pool: {str(e)}") from e

#     @contextmanager
#     def get_connection(self) -> Generator[connection, Any, None]:
#         conn = None
#         for attempt in range(self.max_retries):
#             try:
#                 conn = self.pool.getconn()
#                 conn.cursor().execute('SELECT 1')
#                 break
#             except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
#                 if conn:
#                     self.pool.putconn(conn, close=True)
#                 if attempt == self.max_retries - 1:
#                     raise DatabaseError(f"Could not establish database connection after {self.max_retries} attempts: {str(e)}")
#                 sleep(self.retry_delay)
#                 continue

#         try:
#             yield conn
#         except psycopg2.Error as e:
#             logger.error(f"Database error occurred: {str(e)}")
#             raise DatabaseError(f"Database error: {str(e)}") from e
#         finally:
#             if conn:
#                 try:
#                     self.pool.putconn(conn)
#                 except psycopg2.Error:
#                     conn.close()

# class Database:
#     def __init__(self, config: Config):
#         self.pool = ConnectionPool(config)
#         self.max_retries = 3

#     @contextmanager
#     def transaction(self) -> Generator[cursor, Any, None]:
#         """Context manager for database transactions with automatic rollback on error"""
#         conn = None
#         cur = None
#         for attempt in range(self.max_retries):
#             try:
#                 with self.pool.get_connection() as conn:
#                     cur = conn.cursor()
#                     try:
#                         yield cur
#                         conn.commit()
#                         return
#                     except Exception as e:
#                         conn.rollback()
#                         if attempt == self.max_retries - 1:
#                             raise DatabaseError(f"Transaction failed: {str(e)}") from e
#                         continue
#                     finally:
#                         if cur and not cur.closed:
#                             cur.close()
#             except DatabaseError:
#                 if attempt == self.max_retries - 1:
#                     raise
#                 continue
            

#     def execute(self, query: str, params: Optional[Tuple] = None, fetch: bool = False) -> Optional[List[Tuple]]:
#         """Execute a single query with parameters"""
#         try:
#             with self.transaction() as cur:
#                 cur.execute(query, params)
#                 return cur.fetchall() if fetch else None
#         except Exception as e:
#             logger.error(f"Database execution error: {str(e)}")
#             raise DatabaseError(f"Query execution failed: {str(e)}")
        
#     def executemany(self, query: str, params_list: List[Tuple]) -> None:
#         """Execute multiple queries with parameters"""
#         try:
#             with self.transaction() as cur:
#                 cur.executemany(query, params_list)
#                 cur.close()
#         except Exception as e:
#             logger.error(f"Database execution error: {str(e)}")
#             raise DatabaseError(f"Query execution failed: {str(e)}")