#!/usr/bin/env python
"""
Test script to check connection request acceptance
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from connections.models import Connection
from django.contrib.auth import get_user_model

User = get_user_model()

# Check if connection ID 6 exists
try:
    connection = Connection.objects.get(id=6)
    print(f"✓ Connection ID 6 exists")
    print(f"  Requester: {connection.requester.get_full_name()} ({connection.requester.email})")
    print(f"  Receiver: {connection.receiver.get_full_name()} ({connection.receiver.email})")
    print(f"  Status: {connection.status}")
    print(f"  Created: {connection.created_at}")
except Connection.DoesNotExist:
    print("✗ Connection ID 6 does not exist")
    print("\nAvailable connections:")
    connections = Connection.objects.all()
    if connections.exists():
        for conn in connections[:10]:
            print(f"  ID {conn.id}: {conn.requester.get_full_name()} → {conn.receiver.get_full_name()} ({conn.status})")
    else:
        print("  No connections found in database")

# Check URL pattern
from django.urls import reverse
try:
    url = reverse('connections:accept_request', kwargs={'connection_id': 6})
    print(f"\n✓ URL pattern works: {url}")
except Exception as e:
    print(f"\n✗ URL pattern error: {e}")
