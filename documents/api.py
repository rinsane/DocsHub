from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .models import Document, DocumentPermission
from django.contrib.auth.models import User
from notifications.models import Notification
from django.contrib.contenttypes.models import ContentType


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_list(request):
    """List user's documents (owned and shared)"""
    try:
        # Get owned documents
        owned_docs = Document.objects.filter(owner=request.user)
        
        # Get shared documents
        shared_docs = Document.objects.filter(
            permissions__user=request.user
        ).exclude(owner=request.user).distinct()
        
        # Combine and serialize
        data = []
        for doc in owned_docs:
            data.append({
                'id': doc.id,
                'title': doc.title,
                'content': doc.content[:200] if doc.content else '',
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'updated_at': doc.updated_at.isoformat() if doc.updated_at else None,
                'owner': {
                    'id': doc.owner.id,
                    'username': doc.owner.username,
                }
            })
        
        for doc in shared_docs:
            data.append({
                'id': doc.id,
                'title': doc.title,
                'content': doc.content[:200] if doc.content else '',
                    'created_at': doc.created_at.isoformat() if doc.created_at else None,
                    'updated_at': doc.updated_at.isoformat() if doc.updated_at else None,
                    'owner': {
                        'id': doc.owner.id,
                        'username': doc.owner.username,
                    }
                })
        
        return Response(data)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Document list error: {error_detail}")
        return Response({'error': str(e), 'detail': error_detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def document_create(request):
    """Create a new document"""
    try:
        # Use request.data instead of request.body for DRF
        title = request.data.get('title', 'Untitled Document')
        
        doc = Document.objects.create(
            owner=request.user,
            title=title,
            content='<p></p>'
        )
        
        return Response({
            'id': doc.id,
            'title': doc.title,
            'content': doc.content,
            'created_at': doc.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Document create error: {error_detail}")
        return Response({'error': str(e), 'detail': error_detail}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_get(request, id):
    """Get a specific document"""
    try:
        doc = Document.objects.get(id=id)
        # Check if user has permission (owner or has permission)
        if doc.owner != request.user and not doc.has_permission(request.user, 'viewer'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'id': doc.id,
            'title': doc.title,
            'content': doc.content,
            'created_at': doc.created_at.isoformat(),
            'updated_at': doc.updated_at.isoformat(),
        })
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def document_update(request, id):
    """Update a document"""
    try:
        # Use request.data instead of request.body for DRF
        doc = Document.objects.get(id=id)
        
        # Check permission - must be owner or have editor permission
        if doc.owner != request.user and not doc.has_permission(request.user, 'editor'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        doc.title = request.data.get('title', doc.title)
        doc.content = request.data.get('content', doc.content)
        doc.last_edited_by = request.user
        doc.save()
        
        return Response({
            'id': doc.id,
            'title': doc.title,
            'content': doc.content,
            'updated_at': doc.updated_at.isoformat(),
        })
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def document_delete(request, id):
    """Delete a document"""
    try:
        doc = Document.objects.get(id=id, owner=request.user)
        doc.delete()
        return Response({'message': 'Document deleted'})
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def document_share(request, id):
    """Share a document with another user"""
    try:
        doc = Document.objects.get(id=id, owner=request.user)
        
        email = request.data.get('email')
        role = request.data.get('role', 'viewer')
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if user == request.user:
            return Response({'error': 'Cannot share with yourself'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update permission
        permission, created = DocumentPermission.objects.update_or_create(
            document=doc,
            user=user,
            defaults={'role': role}
        )
        
        # Create notification
        Notification.objects.create(
            recipient=user,
            notification_type='share',
            title='Document Shared',
            message=f'{request.user.username} shared "{doc.title}" with you as {role}',
            content_type=ContentType.objects.get_for_model(Document),
            object_id=doc.id
        )
        
        return Response({
            'success': True,
            'message': f'Document shared with {user.username}',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'role': role
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
