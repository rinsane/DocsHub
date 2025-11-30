from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Spreadsheet
import json


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def spreadsheet_list(request):
    """List user's spreadsheets"""
    spreadsheets = Spreadsheet.objects.filter(owner=request.user)
    data = []
    for sheet in spreadsheets:
        data.append({
            'id': sheet.id,
            'title': sheet.title,
            'created_at': sheet.created_at.isoformat(),
            'updated_at': sheet.updated_at.isoformat(),
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def spreadsheet_create(request):
    """Create a new spreadsheet"""
    try:
        data = json.loads(request.body)
        title = data.get('title', 'Untitled Spreadsheet')
        
        sheet = Spreadsheet.objects.create(
            owner=request.user,
            title=title,
            data=[[]]
        )
        
        return Response({
            'id': sheet.id,
            'title': sheet.title,
            'data': sheet.data,
            'created_at': sheet.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def spreadsheet_get(request, id):
    """Get a specific spreadsheet"""
    try:
        sheet = Spreadsheet.objects.get(id=id, owner=request.user)
        return Response({
            'id': sheet.id,
            'title': sheet.title,
            'data': sheet.data,
            'created_at': sheet.created_at.isoformat(),
            'updated_at': sheet.updated_at.isoformat(),
        })
    except Spreadsheet.DoesNotExist:
        return Response({'error': 'Spreadsheet not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def spreadsheet_update(request, id):
    """Update a spreadsheet"""
    try:
        data = json.loads(request.body)
        sheet = Spreadsheet.objects.get(id=id, owner=request.user)
        
        sheet.title = data.get('title', sheet.title)
        if 'data' in data:
            sheet.data = data.get('data')
        sheet.save()
        
        return Response({
            'id': sheet.id,
            'title': sheet.title,
            'data': sheet.data,
            'updated_at': sheet.updated_at.isoformat(),
        })
    except Spreadsheet.DoesNotExist:
        return Response({'error': 'Spreadsheet not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def spreadsheet_delete(request, id):
    """Delete a spreadsheet"""
    try:
        sheet = Spreadsheet.objects.get(id=id, owner=request.user)
        sheet.delete()
        return Response({'message': 'Spreadsheet deleted'})
    except Spreadsheet.DoesNotExist:
        return Response({'error': 'Spreadsheet not found'}, status=status.HTTP_404_NOT_FOUND)
