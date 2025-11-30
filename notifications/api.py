from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """List user's notifications"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:50]
    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'read': notif.read,
            'created_at': notif.created_at.isoformat(),
        })
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count(request):
    """Get unread notification count"""
    count = Notification.objects.filter(recipient=request.user, read=False).count()
    return Response({'unread_count': count})
