"""Script to initialize the database and create all tables."""
from database import engine, Base
from models import User, Doctor, Patient, Entry, Report


def init_db():
    """Create all tables in the database."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    print("\nTables created:")
    for table in Base.metadata.tables:
        print(f"  - {table}")


if __name__ == "__main__":
    init_db()
