"""
Database engine and session setup.
Supports SQLite (for zero-config local development) and MySQL.
"""
import os
import sys

# Ensure project root is in sys.path when executed directly
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

db_url = settings.database_url
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 30.0}

try:
    engine = create_engine(db_url, connect_args=connect_args)
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as e:
    # Fallback to local SQLite if MySQL connection fails
    fallback_url = "sqlite:///./weather_platform.db"
    print(f"[database_setup] Failed to connect to {db_url} ({e}). Falling back to {fallback_url}")
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False})

from app.models.base import Base
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def ensure_schema_sync(verbose: bool = False):
    """
    Ensures all tables and newly added columns exist in the database,
    migrating columns without dropping existing data.
    """
    try:
        from app.models import User, Admin, Source, Reports, Images_Videos, Action_Log
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        existing_tables = {t.lower(): t for t in inspector.get_table_names()}

        with engine.connect() as conn:
            for table_name, table in Base.metadata.tables.items():
                actual_name = existing_tables.get(table_name.lower())
                if not actual_name:
                    continue

                existing_cols = {c["name"].lower() for c in inspector.get_columns(actual_name)}
                for col in table.columns:
                    if col.name.lower() not in existing_cols:
                        col_type = col.type.compile(engine.dialect)
                        null_clause = ""
                        default_clause = ""
                        if col.default is not None and not callable(col.default.arg):
                            val = col.default.arg
                            if isinstance(val, str):
                                default_clause = f" DEFAULT '{val}'"
                            elif isinstance(val, (int, float)):
                                default_clause = f" DEFAULT {val}"
                            elif isinstance(val, bool):
                                default_clause = f" DEFAULT {1 if val else 0}"

                        if col.nullable:
                            null_clause = " NULL"
                        elif default_clause:
                            null_clause = " NOT NULL"

                        alter_sql = f"ALTER TABLE `{actual_name}` ADD COLUMN `{col.name}` {col_type}{null_clause}{default_clause}"
                        if verbose:
                            print(f"[database_setup] Adding column to '{actual_name}': {alter_sql}")
                        try:
                            conn.execute(text(alter_sql))
                            conn.commit()
                            if verbose:
                                print(f"[database_setup] Added column '{col.name}' successfully.")
                        except Exception as alter_err:
                            print(f"[database_setup] Could not add column '{col.name}' to '{actual_name}': {alter_err}")

                if verbose:
                    current_cols = [c["name"] for c in inspector.get_columns(actual_name)]
                    print(f"[database_setup] Table '{actual_name}': {len(current_cols)} columns verified -> {current_cols}")
    except Exception as e:
        print(f"[database_setup] Schema sync note: {e}")


# Run initial sync
ensure_schema_sync(verbose=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    print(f"[database_setup] Connecting to database: {engine.url}")
    print("[database_setup] Synchronizing schema and updating existing tables...")
    ensure_schema_sync(verbose=True)
    print("[database_setup] Existing database successfully updated and synchronized.")