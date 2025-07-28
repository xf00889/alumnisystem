from django import template
from django.db import models
from connections.models import Connection

register = template.Library()

@register.simple_tag
def get_connection_status(user1, user2):
    """
    Get the connection status between two users.
    Returns: 'none', 'pending_sent', 'pending_received', 'connected', 'blocked'
    """
    if not user1.is_authenticated or user1 == user2:
        return 'none'
    
    try:
        # Check if user1 sent a request to user2
        connection = Connection.objects.get(
            requester=user1,
            receiver=user2
        )
        if connection.status == 'ACCEPTED':
            return 'connected'
        elif connection.status == 'PENDING':
            return 'pending_sent'
        elif connection.status == 'BLOCKED':
            return 'blocked'
        else:
            return 'none'
    except Connection.DoesNotExist:
        pass
    
    try:
        # Check if user2 sent a request to user1
        connection = Connection.objects.get(
            requester=user2,
            receiver=user1
        )
        if connection.status == 'ACCEPTED':
            return 'connected'
        elif connection.status == 'PENDING':
            return 'pending_received'
        elif connection.status == 'BLOCKED':
            return 'blocked'
        else:
            return 'none'
    except Connection.DoesNotExist:
        pass
    
    return 'none'


@register.filter
def get_other_user(connection, user):
    """Get the other user in a connection"""
    return connection.get_other_user(user)


@register.simple_tag
def are_connected(user1, user2):
    """
    Check if two users are connected (have an accepted connection).
    """
    if not user1.is_authenticated or user1 == user2:
        return False
    
    return Connection.objects.filter(
        models.Q(
            requester=user1,
            receiver=user2,
            status='ACCEPTED'
        ) | models.Q(
            requester=user2,
            receiver=user1,
            status='ACCEPTED'
        )
    ).exists()

@register.simple_tag
def get_pending_requests_count(user):
    """
    Get the count of pending connection requests for a user.
    """
    if not user.is_authenticated:
        return 0
    
    return Connection.objects.filter(
        receiver=user,
        status='PENDING'
    ).count()


@register.simple_tag
def get_connection_object(user1, user2):
    """
    Get the connection object between two users.
    Returns the Connection object or None if no connection exists.
    """
    if not user1.is_authenticated or user1 == user2:
        return None
    
    try:
        # Check if user1 sent a request to user2
        connection = Connection.objects.get(
            requester=user1,
            receiver=user2
        )
        return connection
    except Connection.DoesNotExist:
        pass
    
    try:
        # Check if user2 sent a request to user1
        connection = Connection.objects.get(
            requester=user2,
            receiver=user1
        )
        return connection
    except Connection.DoesNotExist:
        pass
    
    return None