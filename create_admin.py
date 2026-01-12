#!/usr/bin/env python3
"""
CLI script to create an admin user for AroTranslate.
Run this script to create the initial admin account.

Usage:
    python create_admin.py
"""

import sys
import getpass
from werkzeug.security import generate_password_hash
from services.db_repository import get_db_repository
from pymongo.errors import DuplicateKeyError


def create_admin_user():
    """Interactive script to create admin user"""
    print("=" * 50)
    print("AroTranslate Admin User Creation")
    print("=" * 50)
    print()

    # Get database repository
    try:
        db_repo = get_db_repository()
        print("✓ Successfully connected to MongoDB")
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        print("\nMake sure MongoDB is running:")
        print("  docker-compose up -d mongodb")
        sys.exit(1)

    # Get username
    while True:
        username = input("Enter admin username: ").strip()
        if not username:
            print("Username cannot be empty. Please try again.")
            continue
        if len(username) < 3:
            print("Username must be at least 3 characters. Please try again.")
            continue
        break

    # Get password with confirmation
    while True:
        password = getpass.getpass("Enter admin password: ")
        if not password:
            print("Password cannot be empty. Please try again.")
            continue
        if len(password) < 8:
            print("Password must be at least 8 characters. Please try again.")
            continue

        password_confirm = getpass.getpass("Confirm admin password: ")
        if password != password_confirm:
            print("Passwords do not match. Please try again.")
            continue
        break

    # Get optional email
    email = input("Enter admin email (optional, press Enter to skip): ").strip()
    email = email if email else None

    # Hash password
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    # Create user in database
    try:
        result = db_repo.create_user(
            username=username,
            password_hash=password_hash,
            email=email
        )
        print()
        print("=" * 50)
        print("✓ Admin user created successfully!")
        print("=" * 50)
        print(f"Username: {result['username']}")
        print(f"User ID: {result['id']}")
        if email:
            print(f"Email: {email}")
        print()
        print("You can now log in at: http://localhost:5000/login")

    except DuplicateKeyError:
        print()
        print(f"✗ Error: Username '{username}' already exists.")
        print("Please try again with a different username.")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"✗ Error creating admin user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_admin_user()
