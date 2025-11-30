from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse
from .models import Notification


@login_required
@require_http_methods(["GET"])
def notification_list(request):
    """List all notifications for current user"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    # Get unread count
    unread_count = notifications.filter(read=False).count()
    
    context = {
        'notifications': notifications[:50],  # Show last 50
        'unread_count': unread_count,
        'total': notifications.count(),
    }
    
    return render(request, 'notifications/list.html', context)


@login_required
@require_POST
def mark_as_read(request, pk):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=pk, recipient=request.user)
        notification.read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)


@login_required
@require_POST
def mark_all_as_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        recipient=request.user,
        read=False
    ).update(read=True)
    
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["GET"])
def get_unread_count(request):
    """Get count of unread notifications (AJAX)"""
    count = Notification.objects.filter(
        recipient=request.user,
        read=False
    ).count()
    
    return JsonResponse({'unread_count': count})

