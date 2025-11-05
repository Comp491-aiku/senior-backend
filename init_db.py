#!/usr/bin/env python3
"""
Initialize database tables and create demo user
"""
import sys
import asyncio
from database.connection import engine
from models.base import Base
from models.user import User
from models.trip import Trip
from models.chat_message import ChatMessage
from models.collaboration import TripShare, TripComment, TripVote
from auth.jwt_handler import get_password_hash
from sqlalchemy.orm import Session
from database.connection import SessionLocal


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")


def create_demo_user():
    """Create a demo user account"""
    print("\nCreating demo user account...")

    db = SessionLocal()
    try:
        # Check if demo user already exists
        existing_user = db.query(User).filter(User.email == "demo@aiku.com").first()
        if existing_user:
            print("✓ Demo user already exists")
            print(f"  Email: demo@aiku.com")
            print(f"  Password: demo1234")
            return

        # Create demo user
        demo_user = User(
            email="demo@aiku.com",
            name="Demo User",
            hashed_password=get_password_hash("demo1234")
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)

        print("✓ Demo user created successfully!")
        print(f"  Email: demo@aiku.com")
        print(f"  Password: demo1234")
        print(f"  User ID: {demo_user.id}")

    except Exception as e:
        print(f"✗ Error creating demo user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    try:
        create_tables()
        create_demo_user()
        print("\n✓ Database initialization complete!")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)
