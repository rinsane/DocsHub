#!/usr/bin/env python
"""
Database Reset Script for DocsHub
This script will delete the database and recreate all tables.
WARNING: This will delete ALL data!
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docshub.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User

def reset_database():
    """Reset the database and create a fresh superuser"""
    
    print("\n" + "="*60)
    print("DocsHub Database Reset")
    print("="*60)
    print("\n⚠️  WARNING: This will DELETE ALL DATA in the database!")
    
    confirm = input("\nType 'YES' to continue or anything else to cancel: ")
    
    if confirm != 'YES':
        print("\n❌ Database reset cancelled.")
        sys.exit(0)
    
    print("\n🗑️  Removing old database...")
    
    # Remove SQLite database file if it exists
    db_file = 'db.sqlite3'
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"   ✓ Deleted {db_file}")
    else:
        print(f"   • No existing database file found")
    
    print("\n📦 Running migrations...")
    call_command('migrate', verbosity=1, interactive=False)
    print("   ✓ Database tables created")
    
    print("\n👤 Creating superuser account...")
    print("\nPlease enter superuser details:")
    
    username = input("Username [admin]: ").strip() or "admin"
    email = input("Email [admin@docshub.local]: ").strip() or "admin@docshub.local"
    
    # Get password with confirmation
    while True:
        password = input("Password: ").strip()
        if len(password) < 4:
            print("   ⚠️  Password too short. Please use at least 4 characters.")
            continue
        password_confirm = input("Password (again): ").strip()
        if password != password_confirm:
            print("   ⚠️  Passwords don't match. Please try again.")
            continue
        break
    
    # Create superuser
    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"\n   ✓ Superuser '{username}' created successfully!")
    except Exception as e:
        print(f"\n   ❌ Error creating superuser: {e}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ Database reset complete!")
    print("="*60)
    print("\n📝 Next steps:")
    print(f"   1. Start Redis:  redis-server")
    print(f"   2. Start Django: python manage.py runserver")
    print(f"   3. Login at:     http://localhost:8000")
    print(f"   4. Admin panel:  http://localhost:8000/admin")
    print(f"\n🔐 Admin Credentials:")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print("\n")

if __name__ == '__main__':
    reset_database()

