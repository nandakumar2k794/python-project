#!/usr/bin/env python
"""
Seed Data Script for Civic Issue Reporting System
=================================================
Populates MongoDB collections with realistic sample data for testing/demo.

Usage:
    cd civic-report/django_app
    python seed_data.py

Or inside Docker:
    docker-compose exec django python seed_data.py
"""

import os
import sys
from datetime import datetime, timedelta
from uuid import uuid4

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from apps.accounts.models import User
from apps.issues.models import Ward, Issue, Comment
from apps.notifications.models import Notification
from apps.audit.models import AuditLog
import bcrypt


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def seed_users():
    """Create sample users if they don't exist."""
    if User.objects.count() >= 4:
        print("  Users already exist, skipping...")
        return

    users_data = [
        {
            "email": "citizen1@civic.local",
            "name": "Rajesh Kumar",
            "password_hash": hash_password("password123"),
            "supabase_uid": "local_citizen1@civic.local",
            "role": "citizen",
            "ward": "Ward 12",
            "phone": "9876543210",
        },
        {
            "email": "citizen2@civic.local",
            "name": "Priya Sharma",
            "password_hash": hash_password("password123"),
            "supabase_uid": "local_citizen2@civic.local",
            "role": "citizen",
            "ward": "Ward 5",
            "phone": "9876543211",
        },
        {
            "email": "officer1@civic.local",
            "name": "Amit Singh",
            "password_hash": hash_password("password123"),
            "supabase_uid": "local_officer1@civic.local",
            "role": "officer",
            "ward": "Ward 12",
            "phone": "9876543212",
        },
        {
            "email": "admin@civic.local",
            "name": "System Admin",
            "password_hash": hash_password("password123"),
            "supabase_uid": "local_admin@civic.local",
            "role": "admin",
            "phone": "9876543213",
        },
    ]

    for user_data in users_data:
        if not User.objects(email=user_data["email"]).first():
            User(**user_data).save()
            print(f"  Created user: {user_data['name']} ({user_data['role']})")


def seed_wards():
    """Create sample wards."""
    if Ward.objects.count() > 0:
        print("  Wards already exist, skipping...")
        return

    wards_data = [
        {"name": "Ward 12", "district": "Central District", "officer_ids": []},
        {"name": "Ward 5", "district": "North District", "officer_ids": []},
        {"name": "Ward 8", "district": "South District", "officer_ids": []},
        {"name": "Ward 15", "district": "East District", "officer_ids": []},
    ]

    for ward_data in wards_data:
        Ward(**ward_data).save()
        print(f"  Created ward: {ward_data['name']}")


def seed_issues():
    """Create sample civic issues."""
    if Issue.objects.count() >= 5:
        print("  Issues already exist, skipping...")
        return

    users = list(User.objects(role="citizen"))
    if not users:
        print("  No citizens found, skipping issues...")
        return

    issues_data = [
        {
            "title": "Pothole on Main Road",
            "description": "Large pothole near the bus stop causing accidents during rains. Needs immediate repair.",
            "category": "Roads",
            "sub_category": "Pothole",
            "status": "Submitted",
            "priority": 2,
            "location": {"lat": 12.9716, "lng": 77.5946, "address": "Main Road, Near Bus Stop"},
            "reported_by": str(users[0].id),
        },
        {
            "title": "Street Light Not Working",
            "description": "Street light pole #45 on 5th Cross Road has been non-functional for 3 weeks. Area is very dark at night.",
            "category": "Street Lights",
            "sub_category": "Not Working",
            "status": "In Progress",
            "priority": 3,
            "location": {"lat": 12.9750, "lng": 77.6000, "address": "5th Cross Road, Pole #45"},
            "reported_by": str(users[1].id),
            "timeline": [
                {"status": "Submitted", "timestamp": datetime.utcnow() - timedelta(days=5), "note": "Issue reported"},
                {"status": "In Progress", "timestamp": datetime.utcnow() - timedelta(days=2), "note": "Electrician assigned"},
            ],
        },
        {
            "title": "Garbage Dumping in Park",
            "description": "Illegal garbage dumping happening daily in the community park near the lake. Foul smell and health hazard.",
            "category": "Sanitation",
            "sub_category": "Illegal Dumping",
            "status": "Resolved",
            "priority": 1,
            "location": {"lat": 12.9800, "lng": 77.5900, "address": "Community Park, Lake Side"},
            "reported_by": str(users[0].id),
            "resolved_at": datetime.utcnow() - timedelta(days=1),
            "timeline": [
                {"status": "Submitted", "timestamp": datetime.utcnow() - timedelta(days=10), "note": "Issue reported"},
                {"status": "In Progress", "timestamp": datetime.utcnow() - timedelta(days=7), "note": "Cleanup team dispatched"},
                {"status": "Resolved", "timestamp": datetime.utcnow() - timedelta(days=1), "note": "Area cleaned and signboards installed"},
            ],
        },
        {
            "title": "Broken Water Pipeline",
            "description": "Water pipeline burst near the market area. Water wastage and supply disruption to nearby houses.",
            "category": "Water Supply",
            "sub_category": "Pipeline Leak",
            "status": "Submitted",
            "priority": 1,
            "location": {"lat": 12.9650, "lng": 77.5850, "address": "Market Road, Near Post Office"},
            "reported_by": str(users[1].id),
        },
        {
            "title": "Unauthorized Construction",
            "description": "Illegal construction of a commercial building in a residential zone without proper permits.",
            "category": "Building Violation",
            "sub_category": "Unauthorized Construction",
            "status": "In Progress",
            "priority": 2,
            "location": {"lat": 12.9720, "lng": 77.5980, "address": "12th Main, Residential Zone B"},
            "reported_by": str(users[0].id),
            "timeline": [
                {"status": "Submitted", "timestamp": datetime.utcnow() - timedelta(days=8), "note": "Complaint filed"},
                {"status": "In Progress", "timestamp": datetime.utcnow() - timedelta(days=3), "note": "Inspection team visited site"},
            ],
        },
    ]

    for issue_data in issues_data:
        issue = Issue(**issue_data)
        issue.save()
        print(f"  Created issue: {issue.title} ({issue.status})")


def seed_comments():
    """Create sample comments on issues."""
    if Comment.objects.count() >= 3:
        print("  Comments already exist, skipping...")
        return

    issues = list(Issue.objects())
    users = list(User.objects())
    if not issues or not users:
        print("  No issues or users found, skipping comments...")
        return

    comments_data = [
        {
            "issue_id": str(issues[0].id),
            "author_id": str(users[0].id),
            "text": "This pothole caused me to fall from my bike yesterday. Please fix it urgently!",
            "is_internal": False,
        },
        {
            "issue_id": str(issues[0].id),
            "author_id": str(users[2].id) if len(users) > 2 else str(users[0].id),
            "text": "Team has been assigned. Expected completion: 2 days.",
            "is_internal": True,
        },
        {
            "issue_id": str(issues[2].id),
            "author_id": str(users[1].id),
            "text": "Thank you for resolving this so quickly! The park looks clean now.",
            "is_internal": False,
        },
    ]

    for comment_data in comments_data:
        Comment(**comment_data).save()
        print(f"  Created comment on issue: {comment_data['issue_id'][:8]}...")


def seed_notifications():
    """Create sample notifications."""
    if Notification.objects.count() >= 3:
        print("  Notifications already exist, skipping...")
        return

    users = list(User.objects())
    issues = list(Issue.objects())
    if not users:
        print("  No users found, skipping notifications...")
        return

    notifications_data = [
        {
            "user_id": str(users[0].id),
            "type": "issue_update",
            "message": "Your issue 'Pothole on Main Road' has been assigned to an officer.",
            "issue_id": str(issues[0].id) if issues else None,
            "is_read": False,
        },
        {
            "user_id": str(users[0].id),
            "type": "issue_resolved",
            "message": "Your issue 'Garbage Dumping in Park' has been resolved.",
            "issue_id": str(issues[2].id) if len(issues) > 2 else None,
            "is_read": True,
        },
        {
            "user_id": str(users[1].id) if len(users) > 1 else str(users[0].id),
            "type": "new_comment",
            "message": "New comment on your issue 'Street Light Not Working'.",
            "issue_id": str(issues[1].id) if len(issues) > 1 else None,
            "is_read": False,
        },
    ]

    for notif_data in notifications_data:
        Notification(**notif_data).save()
        print(f"  Created notification for user: {notif_data['user_id'][:8]}...")


def seed_audit_logs():
    """Create sample audit logs."""
    if AuditLog.objects.count() > 0:
        print("  Audit logs already exist, skipping...")
        return

    users = list(User.objects())
    issues = list(Issue.objects())
    if not users or not issues:
        print("  No users or issues found, skipping audit logs...")
        return

    audit_logs_data = [
        {
            "actor_id": str(users[0].id),
            "action": "CREATE",
            "resource": "Issue",
            "resource_id": str(issues[0].id),
            "new_value": {"title": issues[0].title, "status": issues[0].status},
            "ip": "192.168.1.100",
        },
        {
            "actor_id": str(users[2].id) if len(users) > 2 else str(users[0].id),
            "action": "UPDATE",
            "resource": "Issue",
            "resource_id": str(issues[0].id),
            "old_value": {"status": "Submitted"},
            "new_value": {"status": "In Progress"},
            "ip": "192.168.1.101",
        },
        {
            "actor_id": str(users[0].id),
            "action": "CREATE",
            "resource": "Comment",
            "resource_id": str(Comment.objects.first().id) if Comment.objects.first() else "comment-1",
            "new_value": {"text": "Sample comment"},
            "ip": "192.168.1.100",
        },
    ]

    for audit_data in audit_logs_data:
        AuditLog(**audit_data).save()
        print(f"  Created audit log: {audit_data['action']} {audit_data['resource']}")


def print_summary():
    """Print final collection counts."""
    print("\n" + "=" * 40)
    print("SEED DATA SUMMARY")
    print("=" * 40)
    print(f"  Users:        {User.objects.count()}")
    print(f"  Wards:        {Ward.objects.count()}")
    print(f"  Issues:       {Issue.objects.count()}")
    print(f"  Comments:     {Comment.objects.count()}")
    print(f"  Notifications: {Notification.objects.count()}")
    print(f"  Audit Logs:   {AuditLog.objects.count()}")
    print("=" * 40)


if __name__ == "__main__":
    print("Seeding MongoDB collections...")
    print("-" * 40)
    seed_users()
    seed_wards()
    seed_issues()
    seed_comments()
    seed_notifications()
    seed_audit_logs()
    print_summary()

