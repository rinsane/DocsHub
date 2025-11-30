from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_protect
from django.utils.html import strip_tags
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from notifications.models import Notification
from django.contrib.contenttypes.models import ContentType
import json
import os
from datetime import datetime
from pathlib import Path
import mimetypes

from .models import Document, DocumentPermission, DocumentComment, DocumentVersion
from .utils import (
    HTMLToDocxConverter, html_to_markdown, html_to_text, 
    markdown_to_html, text_to_html
)


@login_required
@require_http_methods(["GET"])
def document_list(request):
    """List all documents accessible to the user"""
    owned_docs = Document.objects.filter(owner=request.user).order_by('-updated_at')
    shared_docs = Document.objects.filter(
        permissions__user=request.user
    ).exclude(owner=request.user).order_by('-updated_at').distinct()
    
    context = {
        'owned_documents': owned_docs,
        'shared_documents': shared_docs,
        'total_documents': owned_docs.count() + shared_docs.count(),
    }
    return render(request, 'documents/list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_document(request):
    """Create a new document"""
    if request.method == 'POST':
        title = request.POST.get('title', 'Untitled Document')
        doc_type = request.POST.get('type', 'docx')
        
        document = Document.objects.create(
            owner=request.user,
            title=title,
            document_type=doc_type,
            content='<p></p>'
        )
        
        messages.success(request, 'Document created successfully!')
        return redirect('documents:editor', pk=document.id)
    
    return render(request, 'documents/create.html')


@login_required
@require_http_methods(["GET"])
def document_editor(request, pk):
    """Main document editor view"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission
    if not document.has_permission(request.user, 'viewer'):
        messages.error(request, 'You do not have access to this document.')
        return redirect('documents:list')
    
    user_role = document.get_user_role(request.user)
    can_edit = document.has_permission(request.user, 'editor')
    can_comment = document.has_permission(request.user, 'commenter')
    is_owner = document.owner == request.user
    
    # Get collaborators
    collaborators = DocumentPermission.objects.filter(document=document).select_related('user')
    
    # Get comments
    comments = DocumentComment.objects.filter(document=document).select_related('user').order_by('created_at')
    
    # Get versions
    versions = DocumentVersion.objects.filter(document=document).order_by('-version_number')
    
    context = {
        'document': document,
        'user_role': user_role,
        'can_edit': can_edit,
        'can_comment': can_comment,
        'is_owner': is_owner,
        'collaborators': collaborators,
        'comments': comments,
        'versions': versions[:10],  # Show last 10 versions
    }
    
    return render(request, 'documents/editor.html', context)


@login_required
@require_POST
def update_document(request, pk):
    """Update document content"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission
    if not document.has_permission(request.user, 'editor'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    content = request.POST.get('content', '')
    document.content = content
    document.last_edited_by = request.user
    document.save(update_fields=['content', 'last_edited_by', 'updated_at'])
    
    return JsonResponse({'success': True, 'message': 'Document saved'})


@login_required
@require_POST
def delete_document(request, pk):
    """Delete a document"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission - only owner can delete
    if document.owner != request.user:
        return JsonResponse({'error': 'Only owner can delete'}, status=403)
    
    title = document.title
    document.delete()
    
    messages.success(request, f'Document "{title}" deleted successfully.')
    return redirect('documents:list')


@login_required
@require_http_methods(["GET"])
def share_document(request, pk):
    """Get share dialog for document"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission - only owner can share
    if document.owner != request.user:
        messages.error(request, 'Only owner can share.')
        return redirect('documents:editor', pk=pk)
    
    permissions = DocumentPermission.objects.filter(document=document).select_related('user')
    
    context = {
        'document': document,
        'permissions': permissions,
    }
    
    return render(request, 'documents/share_dialog.html', context)


@login_required
@require_POST
def add_permission(request, pk):
    """Add or update document permission"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission - only owner can share
    if document.owner != request.user:
        return JsonResponse({'error': 'Only owner can share'}, status=403)
    
    email = request.POST.get('email')
    role = request.POST.get('role', 'viewer')
    
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    if user == document.owner:
        return JsonResponse({'error': 'Cannot share with yourself'}, status=400)
    
    # Create or update permission
    permission, created = DocumentPermission.objects.update_or_create(
        document=document,
        user=user,
        defaults={'role': role}
    )
    
    # Create notification
    Notification.objects.create(
        recipient=user,
        notification_type='share',
        title='Document Shared',
        message=f'{request.user.username} shared "{document.title}" with you as {role}',
        content_type=ContentType.objects.get_for_model(Document),
        object_id=document.id
    )
    
    action = 'updated' if not created else 'added'
    messages.success(request, f'Permission {action} successfully.')
    
    return JsonResponse({
        'success': True,
        'message': f'Permission {action}',
        'user': user.username,
        'role': role
    })


@login_required
@require_POST
def remove_permission(request, pk, user_id):
    """Remove document permission"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission - only owner can modify
    if document.owner != request.user:
        return JsonResponse({'error': 'Only owner can modify permissions'}, status=403)
    
    try:
        permission = DocumentPermission.objects.get(document=document, user_id=user_id)
        user_name = permission.user.username
        permission.delete()
        messages.success(request, f'Removed access for {user_name}.')
        return JsonResponse({'success': True})
    except DocumentPermission.DoesNotExist:
        return JsonResponse({'error': 'Permission not found'}, status=404)


@login_required
@require_POST
def add_comment(request, pk):
    """Add a comment to document"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission
    if not document.has_permission(request.user, 'commenter'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Comment cannot be empty'}, status=400)
    
    comment = DocumentComment.objects.create(
        document=document,
        user=request.user,
        content=content,
        selection_data=request.POST.get('selection_data')
    )
    
    # Notify owner if commenter is not owner
    if document.owner != request.user:
        Notification.objects.create(
            recipient=document.owner,
            notification_type='comment',
            title='New Comment',
            message=f'{request.user.username} commented on "{document.title}"',
            content_type=ContentType.objects.get_for_model(DocumentComment),
            object_id=comment.id
        )
    
    return JsonResponse({
        'success': True,
        'comment_id': comment.id,
        'message': 'Comment added successfully'
    })


@login_required
@require_http_methods(["GET"])
def list_comments(request, pk):
    """List all comments on a document"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission
    if not document.has_permission(request.user, 'viewer'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    comments = DocumentComment.objects.filter(
        document=document,
        resolved=False
    ).select_related('user').values('id', 'content', 'user__username', 'created_at')
    
    return JsonResponse({
        'comments': list(comments),
        'count': DocumentComment.objects.filter(document=document).count()
    })


@login_required
@require_POST
def save_version(request, pk):
    """Create a version snapshot"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission
    if not document.has_permission(request.user, 'editor'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    description = request.POST.get('description', 'Manual save')
    
    # Get next version number
    last_version = document.versions.first()
    version_number = (last_version.version_number + 1) if last_version else 1
    
    version = DocumentVersion.objects.create(
        document=document,
        content=document.content,
        created_by=request.user,
        version_number=version_number,
        change_description=description
    )
    
    return JsonResponse({
        'success': True,
        'version_number': version_number,
        'message': 'Version saved successfully'
    })


@login_required
@require_http_methods(["GET"])
def list_versions(request, pk):
    """List all versions of a document"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission
    if not document.has_permission(request.user, 'viewer'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    versions = document.versions.values(
        'id', 'version_number', 'created_at', 'created_by__username', 'change_description'
    ).order_by('-version_number')
    
    return JsonResponse({
        'versions': list(versions),
        'count': document.versions.count()
    })


@login_required
@require_http_methods(["GET"])
def view_version(request, pk, version_num):
    """View a specific version"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission
    if not document.has_permission(request.user, 'viewer'):
        messages.error(request, 'Permission denied')
        return redirect('documents:list')
    
    version = get_object_or_404(DocumentVersion, document=document, version_number=version_num)
    is_current = (version.content == document.content)
    
    context = {
        'document': document,
        'version': version,
        'is_current': is_current,
    }
    
    return render(request, 'documents/version_view.html', context)


@login_required
@require_POST
def restore_version(request, pk, version_num):
    """Restore a previous version"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission - only editor or owner can restore
    if not document.has_permission(request.user, 'editor'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    version = get_object_or_404(DocumentVersion, document=document, version_number=version_num)
    
    # Create a new version before restoring
    last_version = document.versions.first()
    new_version_num = (last_version.version_number + 1) if last_version else 1
    
    DocumentVersion.objects.create(
        document=document,
        content=document.content,
        created_by=request.user,
        version_number=new_version_num,
        change_description=f'Restored to version {version_num}'
    )
    
    # Restore
    document.content = version.content
    document.last_edited_by = request.user
    document.save()
    
    messages.success(request, f'Restored to version {version_num}')
    return redirect('documents:editor', pk=pk)


@login_required
@require_POST
def import_document(request, pk):
    """Import document from file"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission - only owner can import
    if document.owner != request.user:
        return JsonResponse({'error': 'Only owner can import'}, status=403)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file_obj = request.FILES['file']
    file_ext = Path(file_obj.name).suffix.lower()
    
    try:
        content = file_obj.read()
        
        if file_ext == '.docx':
            from docx import Document as DocxDocument
            from io import BytesIO
            docx_doc = DocxDocument(BytesIO(content))
            # Convert to HTML
            html = '<div>'
            for para in docx_doc.paragraphs:
                html += f'<p>{para.text}</p>'
            html += '</div>'
            document.content = html
        
        elif file_ext == '.txt':
            text = content.decode('utf-8', errors='ignore')
            document.content = text_to_html(text)
        
        elif file_ext == '.md':
            text = content.decode('utf-8', errors='ignore')
            document.content = markdown_to_html(text)
        
        else:
            return JsonResponse({'error': 'Unsupported file format'}, status=400)
        
        document.save()
        messages.success(request, 'Document imported successfully!')
        return JsonResponse({'success': True, 'message': 'Document imported'})
    
    except Exception as e:
        return JsonResponse({'error': f'Import failed: {str(e)}'}, status=400)


@login_required
@require_http_methods(["GET"])
def export_document(request, pk, format):
    """Export document in specified format"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission
    if not document.has_permission(request.user, 'viewer'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        if format == 'docx':
            docx_doc = HTMLToDocxConverter.convert(document.content)
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = f'attachment; filename="{document.title}.docx"'
            docx_doc.save(response)
            return response
        
        elif format == 'txt':
            text = html_to_text(document.content)
            response = HttpResponse(text, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="{document.title}.txt"'
            return response
        
        elif format == 'md':
            markdown_content = html_to_markdown(document.content)
            response = HttpResponse(markdown_content, content_type='text/markdown')
            response['Content-Disposition'] = f'attachment; filename="{document.title}.md"'
            return response
        
        elif format == 'pdf':
            try:
                from weasyprint import HTML, CSS
                from io import BytesIO
                
                html_string = render_to_string('documents/export_pdf.html', {
                    'document': document,
                    'content': document.content
                })
                
                html = HTML(string=html_string)
                pdf_bytes = html.write_pdf()
                
                response = HttpResponse(pdf_bytes, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{document.title}.pdf"'
                return response
            except Exception as e:
                return JsonResponse({'error': f'PDF generation failed: {str(e)}'}, status=400)
        
        else:
            return JsonResponse({'error': 'Unsupported format'}, status=400)
    
    except Exception as e:
        return JsonResponse({'error': f'Export failed: {str(e)}'}, status=400)


@login_required
@require_POST
def spellcheck(request, pk):
    """Check document for spelling/grammar"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permission
    if not document.has_permission(request.user, 'viewer'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    text = html_to_text(document.content)
    language = request.POST.get('language', 'en-US')
    
    try:
        import language_tool_python
        tool = language_tool_python.LanguageTool(language)
        matches = tool.check(text)
        
        suggestions = []
        for match in matches[:20]:  # Limit to first 20 issues
            suggestions.append({
                'message': match.message,
                'offset': match.offset,
                'length': match.errorLength,
                'replacements': match.replacements[:3] if match.replacements else [],
                'type': match.ruleIssueType
            })
        
        return JsonResponse({
            'suggestions': suggestions,
            'total': len(suggestions)
        })
    
    except Exception as e:
        return JsonResponse({'error': f'Spell check failed: {str(e)}'}, status=400)
