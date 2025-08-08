# database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Get the database URL from environment variables
# This will be provided by Vercel in production
DATABASE_URL = os.getenv("POSTGRES_URL")

if not DATABASE_URL:
    raise ValueError("POSTGRES_URL environment variable not set.")

# For PostgreSQL, we don't need 'connect_args'
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
