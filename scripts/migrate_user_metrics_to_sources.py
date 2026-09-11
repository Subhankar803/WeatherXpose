"""
Database Migration: Move trust and reporting metrics from users to Sources
and establish composite unique constraint on (Username, Platform).
"""
import sys
import os

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect, text
from app.database_setup import engine

def run_migration():
    print(f"[migration] Running migration against: {engine.url}")
    inspector = inspect(engine)
    is_mysql = engine.dialect.name == "mysql"
    is_sqlite = engine.dialect.name == "sqlite"

    with engine.connect() as conn:
        # =========================================================
        # 1. Update 'users' table: Drop the 4 relocated columns
        # =========================================================
        existing_user_cols = {c["name"].lower() for c in inspector.get_columns("users")}
        cols_to_drop = ["trust_status", "total_reports", "fake_reports", "warnings_count"]
        
        for col_name in cols_to_drop:
            if col_name in existing_user_cols:
                if is_mysql:
                    try:
                        print(f"[migration] Dropping '{col_name}' from users...")
                        conn.execute(text(f"ALTER TABLE `users` DROP COLUMN `{col_name}`"))
                        conn.commit()
                        print(f"[migration] Dropped '{col_name}' successfully.")
                    except Exception as e:
                        print(f"[migration] Error dropping '{col_name}' from users: {e}")
                elif is_sqlite:
                    try:
                        conn.execute(text(f"ALTER TABLE users DROP COLUMN {col_name}"))
                        conn.commit()
                    except Exception as e:
                        print(f"[migration] SQLite drop column note for '{col_name}': {e}")

        # =========================================================
        # 2. Update 'Sources' table
        # =========================================================
        existing_source_cols = {c["name"].lower() for c in inspector.get_columns("Sources")}

        # 2.1 Add 'Username' column if not exists
        if "username" not in existing_source_cols:
            print("[migration] Adding 'Username' to Sources...")
            if is_mysql:
                conn.execute(text("ALTER TABLE `Sources` ADD COLUMN `Username` VARCHAR(255) NULL AFTER `Id`"))
            else:
                conn.execute(text("ALTER TABLE Sources ADD COLUMN Username VARCHAR(255)"))
            conn.commit()

        # 2.2 Populate Username from Source_Name for existing rows if empty
        conn.execute(text("UPDATE `Sources` SET `Username` = `Source_Name` WHERE `Username` IS NULL OR `Username` = ''"))
        conn.commit()

        # 2.3 Add relocated metrics to Sources
        source_cols_to_add = [
            ("Trust_Status", "ENUM('GREEN', 'GREY', 'RED') NOT NULL DEFAULT 'GREY'", "VARCHAR(20) NOT NULL DEFAULT 'GREY'"),
            ("Total_Reports", "INT NOT NULL DEFAULT 0", "INTEGER NOT NULL DEFAULT 0"),
            ("Fake_Reports", "INT NOT NULL DEFAULT 0", "INTEGER NOT NULL DEFAULT 0"),
            ("Warnings_Count", "INT NOT NULL DEFAULT 0", "INTEGER NOT NULL DEFAULT 0"),
        ]

        for col_name, mysql_def, sqlite_def in source_cols_to_add:
            if col_name.lower() not in existing_source_cols:
                print(f"[migration] Adding '{col_name}' to Sources...")
                col_type = mysql_def if is_mysql else sqlite_def
                try:
                    conn.execute(text(f"ALTER TABLE `Sources` ADD COLUMN `{col_name}` {col_type}"))
                    conn.commit()
                    print(f"[migration] Added '{col_name}' successfully.")
                except Exception as e:
                    print(f"[migration] Error adding '{col_name}' to Sources: {e}")

        # 2.4 Drop old single-column unique constraint on Source_Name if present
        if is_mysql:
            indexes = inspector.get_indexes("Sources")
            for idx in indexes:
                idx_name = idx["name"]
                col_names = idx["column_names"]
                if idx.get("unique") and col_names == ["Source_Name"]:
                    print(f"[migration] Dropping obsolete single-column unique index '{idx_name}' from Sources...")
                    try:
                        conn.execute(text(f"ALTER TABLE `Sources` DROP INDEX `{idx_name}`"))
                        conn.commit()
                        print(f"[migration] Dropped index '{idx_name}' successfully.")
                    except Exception as e:
                        print(f"[migration] Could not drop index '{idx_name}': {e}")

            # 2.5 Ensure composite unique constraint on (Username, Platform)
            inspector = inspect(engine)
            existing_indexes = inspector.get_indexes("Sources")
            has_composite = any(
                idx.get("unique") and set(idx["column_names"]) == {"Username", "Platform"}
                for idx in existing_indexes
            )
            if not has_composite:
                print("[migration] Creating composite unique index 'uq_source_username_platform' (Username, Platform)...")
                try:
                    conn.execute(text("ALTER TABLE `Sources` ADD CONSTRAINT `uq_source_username_platform` UNIQUE (`Username`, `Platform`)"))
                    conn.commit()
                    print("[migration] Created composite unique constraint successfully.")
                except Exception as e:
                    print(f"[migration] Note creating composite unique: {e}")

    print("[migration] Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
