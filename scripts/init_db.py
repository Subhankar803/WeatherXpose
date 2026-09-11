import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database_setup import engine, Base, ensure_schema_sync
from app.models import User, Admin, Source, Reports, Images_Videos, Action_Log


def init_database():
    print("[init_db] Creating all database tables and synchronizing schema...")
    Base.metadata.create_all(bind=engine)
    ensure_schema_sync(verbose=True)
    print("[init_db] All database tables successfully created and synchronized.")


if __name__ == "__main__":
    init_database()

