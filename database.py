# database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# For SQLite, the URL is "sqlite:///./keys.db". This will create a file named keys.db in your project folder.
DATABASE_URL = "sqlite:///./keys.db"

# The engine is the entry point to the database.
engine = create_engine(
    DATABASE_URL,
    # "connect_args" is needed only for SQLite to allow multi-threaded access.
    connect_args={"check_same_thread": False}
)

# Each instance of the SessionLocal class will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This Base will be used to create our ORM models.
Base = declarative_base()

# Dependency to get a DB session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
