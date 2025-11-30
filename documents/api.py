from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .models import Document
import json


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_list(request):
    """List user's documents"""
    documents = Document.objects.filter(owner=request.user)
    data = []
    for doc in documents:
        data.append({
            'id': doc.id,
            'title': doc.title,
            'content': doc.content[:200] if doc.content else '',
            'created_at': doc.created_at.isoformat(),
            'updated_at': doc.updated_at.isoformat(),
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def document_create(request):
    """Create a new document"""
    try:
        data = json.loads(request.body)
        title = data.get('title', 'Untitled Document')
        
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
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_get(request, id):
    """Get a specific document"""
    try:
        doc = Document.objects.get(id=id, owner=request.user)
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
        data = json.loads(request.body)
        doc = Document.objects.get(id=id, owner=request.user)
        
        doc.title = data.get('title', doc.title)
        doc.content = data.get('content', doc.content)
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
