import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import urlparse, unquote

DATABASE_URL = os.getenv("DATABASE_URL", "")

def ensure_database_exists(database_url: str) -> None:
    """Ensure DB exists – only executed when using MySQL URLs."""
    parsed = urlparse(database_url)
    if not parsed.scheme.startswith("mysql"):
        return  # Skip for Postgres, SQLite, SQLServer, etc.

    db_name = parsed.path.lstrip('/')
    if not db_name:
        return

    user = unquote(parsed.username) if parsed.username else None
    password = unquote(parsed.password) if parsed.password else None
    host = parsed.hostname or "localhost"
    port = parsed.port or 3306

    try:
        import pymysql
        conn = pymysql.connect(host=host, user=user, password=password, port=port, charset="utf8mb4")
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        conn.commit()
        conn.close()
    except Exception as exc:
        raise RuntimeError(f"Failed to ensure database '{db_name}' exists: {exc}") from exc

# MySQL DB creation check (won’t run in Postgres mode)
ensure_database_exists(DATABASE_URL)

# SQLAlchemy Engine with OPTIMIZED pool settings for cloud DBs (Supabase)
engine_kwargs = {}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Connection pool optimization for PostgreSQL/MySQL
    # CRITICAL: These settings prevent connection exhaustion and freezing
    connect_args = {}
    
    # PostgreSQL-specific connection timeout
    if DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres"):
        connect_args["connect_timeout"] = 10  # 10 second connection timeout
        connect_args["options"] = "-c statement_timeout=30000"  # 30s query timeout
    
    engine_kwargs.update({
        "pool_size": 3,            # Reduced for cloud DB limits (Render free tier)
        "max_overflow": 5,         # Extra connections when pool is exhausted
        "pool_pre_ping": True,     # Verify connections before use (handles stale connections)
        "pool_recycle": 180,       # Recycle connections every 3 min (cloud timeout)
        "pool_timeout": 20,        # Wait max 20s for connection from pool
        "echo": False,             # Disable SQL logging for performance
        "connect_args": connect_args,
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Session setup with expire_on_commit=False for better performance
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()

# DB dependency generator
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
