import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


db_url = os.getenv("MYSQL_URL", "mysql+pymysql://root:Subhankar21@localhost:3306/Debug_Dynasty")

engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)