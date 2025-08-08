# create_tables.py

from database import engine, Base
import models # Make sure models are imported so Base knows about them

print("Connecting to the database and creating tables...")

# This command creates all tables defined in your models
Base.metadata.create_all(bind=engine)

print("Tables created successfully!")
