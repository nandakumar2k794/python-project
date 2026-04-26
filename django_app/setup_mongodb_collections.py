#!/usr/bin/env python
"""
MongoDB Collection Setup Script
===============================
This script ensures all mongoengine Document collections are created in MongoDB
along with their indexes. Mongoengine creates collections lazily (only when a
document is inserted), so this script forces early creation by calling
ensure_indexes() on each model.

Usage:
    cd civic-report/django_app
    python setup_mongodb_collections.py

Or inside Docker:
    docker-compose exec django python setup_mongodb_collections.py
"""

import os
import sys

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

# Import mongoengine to get the default connection
import mongoengine

# Import all mongoengine Document models so their collections can be created
from apps.accounts.models import User
from apps.issues.models import Ward, Issue, Comment
from apps.notifications.models import Notification
from apps.audit.models import AuditLog


def setup_collections():
    """Ensure all collections and indexes exist in MongoDB."""
    models = [
        ("user", User),
        ("ward", Ward),
        ("issue", Issue),
        ("comment", Comment),
        ("notification", Notification),
        ("audit_log", AuditLog),
    ]

    # Get the pymongo database object from mongoengine's default connection
    db = mongoengine.connection.get_db()

    print("Setting up MongoDB collections...")
    print("-" * 40)

    for collection_name, model_class in models:
        try:
            # Step 1: ensure_indexes() creates indexes (and may create collection)
            model_class.ensure_indexes()

            # Step 2: If collection still doesn't exist, force-create it with pymongo
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                print(f"  [{model_class.__name__}] -> '{collection_name}' collection created (forced).")
            else:
                print(f"  [{model_class.__name__}] -> '{collection_name}' collection ensured.")
        except Exception as exc:
            print(f"  [ERROR] {model_class.__name__}: {exc}")

    # Final verification
    print("-" * 40)
    existing = db.list_collection_names()
    print(f"Collections in DB: {existing}")
    missing = [name for name, _ in models if name not in existing]
    if missing:
        print(f"WARNING: Still missing: {missing}")
    else:
        print("SUCCESS: All collections are now visible in MongoDB Compass.")


if __name__ == "__main__":
    setup_collections()

