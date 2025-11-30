from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.template.loader import render_to_string
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from notifications.models import Notification
from django.contrib.contenttypes.models import ContentType
import json
from pathlib import Path
from io import BytesIO

from .models import Spreadsheet, SpreadsheetPermission, SpreadsheetComment, SpreadsheetVersion
from .utils import (
    xlsx_to_dict, dict_to_xlsx, dict_to_csv, initialize_spreadsheet,
    evaluate_formula
)


@login_required
@require_http_methods(["GET"])
def spreadsheet_list(request):
    """List all spreadsheets accessible to the user"""
    owned_sheets = Spreadsheet.objects.filter(owner=request.user).order_by('-updated_at')
    shared_sheets = Spreadsheet.objects.filter(
        permissions__user=request.user
    ).exclude(owner=request.user).order_by('-updated_at').distinct()
    
    context = {
        'owned_spreadsheets': owned_sheets,
        'shared_spreadsheets': shared_sheets,
        'total_spreadsheets': owned_sheets.count() + shared_sheets.count(),
    }
    return render(request, 'spreadsheets/list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_spreadsheet(request):
    """Create a new spreadsheet"""
    if request.method == 'POST':
        title = request.POST.get('title', 'Untitled Spreadsheet')
        
        spreadsheet = Spreadsheet.objects.create(
            owner=request.user,
            title=title,
            data=initialize_spreadsheet()
        )
        
        messages.success(request, 'Spreadsheet created successfully!')
        return redirect('spreadsheets:editor', pk=spreadsheet.id)
    
    return render(request, 'spreadsheets/create.html')


@login_required
@require_http_methods(["GET"])
def spreadsheet_editor(request, pk):
    """Main spreadsheet editor view"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission
    if not spreadsheet.has_permission(request.user, 'viewer'):
        messages.error(request, 'You do not have access to this spreadsheet.')
        return redirect('spreadsheets:list')
    
    user_role = spreadsheet.get_user_role(request.user)
    can_edit = spreadsheet.has_permission(request.user, 'editor')
    can_comment = spreadsheet.has_permission(request.user, 'commenter')
    is_owner = spreadsheet.owner == request.user
    
    # Get collaborators
    collaborators = SpreadsheetPermission.objects.filter(spreadsheet=spreadsheet).select_related('user')
    
    # Get comments
    comments = SpreadsheetComment.objects.filter(spreadsheet=spreadsheet).select_related('user').order_by('created_at')
    
    # Get versions
    versions = SpreadsheetVersion.objects.filter(spreadsheet=spreadsheet).order_by('-version_number')
    
    context = {
        'spreadsheet': spreadsheet,
        'user_role': user_role,
        'can_edit': can_edit,
        'can_comment': can_comment,
        'is_owner': is_owner,
        'collaborators': collaborators,
        'comments': comments,
        'versions': versions[:10],
        'spreadsheet_json': json.dumps(spreadsheet.data),
    }
    
    return render(request, 'spreadsheets/editor.html', context)


@login_required
@require_POST
def update_spreadsheet(request, pk):
    """Update spreadsheet data"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission
    if not spreadsheet.has_permission(request.user, 'editor'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.POST.get('data', '{}'))
        spreadsheet.data = data
        spreadsheet.last_edited_by = request.user
        spreadsheet.save(update_fields=['data', 'last_edited_by', 'updated_at'])
        return JsonResponse({'success': True, 'message': 'Spreadsheet saved'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid data format'}, status=400)


@login_required
@require_POST
def delete_spreadsheet(request, pk):
    """Delete a spreadsheet"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission - only owner can delete
    if spreadsheet.owner != request.user:
        return JsonResponse({'error': 'Only owner can delete'}, status=403)
    
    title = spreadsheet.title
    spreadsheet.delete()
    
    messages.success(request, f'Spreadsheet "{title}" deleted successfully.')
    return redirect('spreadsheets:list')


@login_required
@require_http_methods(["GET"])
def share_spreadsheet(request, pk):
    """Get share dialog for spreadsheet"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission - only owner can share
    if spreadsheet.owner != request.user:
        messages.error(request, 'Only owner can share.')
        return redirect('spreadsheets:editor', pk=pk)
    
    permissions = SpreadsheetPermission.objects.filter(spreadsheet=spreadsheet).select_related('user')
    
    context = {
        'spreadsheet': spreadsheet,
        'permissions': permissions,
    }
    
    return render(request, 'spreadsheets/share_dialog.html', context)


@login_required
@require_POST
def add_permission(request, pk):
    """Add or update spreadsheet permission"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission - only owner can share
    if spreadsheet.owner != request.user:
        return JsonResponse({'error': 'Only owner can share'}, status=403)
    
    email = request.POST.get('email')
    role = request.POST.get('role', 'viewer')
    
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    if user == spreadsheet.owner:
        return JsonResponse({'error': 'Cannot share with yourself'}, status=400)
    
    # Create or update permission
    permission, created = SpreadsheetPermission.objects.update_or_create(
        spreadsheet=spreadsheet,
        user=user,
        defaults={'role': role}
    )
    
    # Create notification
    Notification.objects.create(
        recipient=user,
        notification_type='share',
        title='Spreadsheet Shared',
        message=f'{request.user.username} shared "{spreadsheet.title}" with you as {role}',
        content_type=ContentType.objects.get_for_model(Spreadsheet),
        object_id=spreadsheet.id
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
    """Remove spreadsheet permission"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission - only owner can modify
    if spreadsheet.owner != request.user:
        return JsonResponse({'error': 'Only owner can modify permissions'}, status=403)
    
    try:
        permission = SpreadsheetPermission.objects.get(spreadsheet=spreadsheet, user_id=user_id)
        user_name = permission.user.username
        permission.delete()
        messages.success(request, f'Removed access for {user_name}.')
        return JsonResponse({'success': True})
    except SpreadsheetPermission.DoesNotExist:
        return JsonResponse({'error': 'Permission not found'}, status=404)


@login_required
@require_POST
def add_comment(request, pk):
    """Add a comment to spreadsheet cell"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission
    if not spreadsheet.has_permission(request.user, 'commenter'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    content = request.POST.get('content', '').strip()
    sheet_name = request.POST.get('sheet', 'Sheet1')
    row = int(request.POST.get('row', 0))
    col = int(request.POST.get('col', 0))
    
    if not content:
        return JsonResponse({'error': 'Comment cannot be empty'}, status=400)
    
    comment = SpreadsheetComment.objects.create(
        spreadsheet=spreadsheet,
        user=request.user,
        content=content,
        sheet_name=sheet_name,
        row=row,
        column=col
    )
    
    # Notify owner if commenter is not owner
    if spreadsheet.owner != request.user:
        Notification.objects.create(
            recipient=spreadsheet.owner,
            notification_type='comment',
            title='New Comment',
            message=f'{request.user.username} commented on "{spreadsheet.title}"',
            content_type=ContentType.objects.get_for_model(SpreadsheetComment),
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
    """List all comments on a spreadsheet"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission
    if not spreadsheet.has_permission(request.user, 'viewer'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    comments = SpreadsheetComment.objects.filter(
        spreadsheet=spreadsheet,
        resolved=False
    ).select_related('user').values(
        'id', 'content', 'user__username', 'sheet_name', 'row', 'column', 'created_at'
    )
    
    return JsonResponse({
        'comments': list(comments),
        'count': SpreadsheetComment.objects.filter(spreadsheet=spreadsheet).count()
    })


@login_required
@require_POST
def save_version(request, pk):
    """Create a version snapshot"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission
    if not spreadsheet.has_permission(request.user, 'editor'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    description = request.POST.get('description', 'Manual save')
    
    # Get next version number
    last_version = spreadsheet.versions.first()
    version_number = (last_version.version_number + 1) if last_version else 1
    
    version = SpreadsheetVersion.objects.create(
        spreadsheet=spreadsheet,
        data=spreadsheet.data,
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
    """List all versions of a spreadsheet"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission
    if not spreadsheet.has_permission(request.user, 'viewer'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    versions = spreadsheet.versions.values(
        'id', 'version_number', 'created_at', 'created_by__username', 'change_description'
    ).order_by('-version_number')
    
    return JsonResponse({
        'versions': list(versions),
        'count': spreadsheet.versions.count()
    })


@login_required
@require_http_methods(["GET"])
def view_version(request, pk, version_num):
    """View a specific version"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission
    if not spreadsheet.has_permission(request.user, 'viewer'):
        messages.error(request, 'Permission denied')
        return redirect('spreadsheets:list')
    
    version = get_object_or_404(SpreadsheetVersion, spreadsheet=spreadsheet, version_number=version_num)
    is_current = (version.data == spreadsheet.data)
    
    context = {
        'spreadsheet': spreadsheet,
        'version': version,
        'is_current': is_current,
        'version_json': json.dumps(version.data),
    }
    
    return render(request, 'spreadsheets/version_view.html', context)


@login_required
@require_POST
def restore_version(request, pk, version_num):
    """Restore a previous version"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission - only editor or owner can restore
    if not spreadsheet.has_permission(request.user, 'editor'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    version = get_object_or_404(SpreadsheetVersion, spreadsheet=spreadsheet, version_number=version_num)
    
    # Create a new version before restoring
    last_version = spreadsheet.versions.first()
    new_version_num = (last_version.version_number + 1) if last_version else 1
    
    SpreadsheetVersion.objects.create(
        spreadsheet=spreadsheet,
        data=spreadsheet.data,
        created_by=request.user,
        version_number=new_version_num,
        change_description=f'Restored to version {version_num}'
    )
    
    # Restore
    spreadsheet.data = version.data
    spreadsheet.last_edited_by = request.user
    spreadsheet.save()
    
    messages.success(request, f'Restored to version {version_num}')
    return redirect('spreadsheets:editor', pk=pk)


@login_required
@require_POST
def import_spreadsheet(request, pk):
    """Import spreadsheet from file"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission - only owner can import
    if spreadsheet.owner != request.user:
        return JsonResponse({'error': 'Only owner can import'}, status=403)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file_obj = request.FILES['file']
    file_ext = Path(file_obj.name).suffix.lower()
    
    try:
        if file_ext == '.xlsx':
            from io import BytesIO
            content = BytesIO(file_obj.read())
            data = xlsx_to_dict(content)
            spreadsheet.data = data
            spreadsheet.save()
            messages.success(request, 'Spreadsheet imported successfully!')
            return JsonResponse({'success': True, 'message': 'Spreadsheet imported'})
        
        elif file_ext == '.csv':
            import csv
            from io import TextIOWrapper
            
            content = TextIOWrapper(file_obj, encoding='utf-8')
            reader = csv.reader(content)
            rows = list(reader)
            
            spreadsheet.data = {
                'sheets': [{
                    'name': 'Sheet1',
                    'data': rows
                }]
            }
            spreadsheet.save()
            messages.success(request, 'CSV imported successfully!')
            return JsonResponse({'success': True, 'message': 'CSV imported'})
        
        else:
            return JsonResponse({'error': 'Unsupported file format. Use .xlsx or .csv'}, status=400)
    
    except Exception as e:
        return JsonResponse({'error': f'Import failed: {str(e)}'}, status=400)


@login_required
@require_http_methods(["GET"])
def export_spreadsheet(request, pk, format):
    """Export spreadsheet in specified format"""
    spreadsheet = get_object_or_404(Spreadsheet, pk=pk)
    
    # Check permission
    if not spreadsheet.has_permission(request.user, 'viewer'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        if format == 'xlsx':
            xlsx_bytes = dict_to_xlsx(spreadsheet.data)
            response = HttpResponse(
                xlsx_bytes,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{spreadsheet.title}.xlsx"'
            return response
        
        elif format == 'csv':
            csv_content = dict_to_csv(spreadsheet.data, 0)
            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{spreadsheet.title}.csv"'
            return response
        
        else:
            return JsonResponse({'error': 'Unsupported format. Use xlsx or csv'}, status=400)
    
    except Exception as e:
        return JsonResponse({'error': f'Export failed: {str(e)}'}, status=400)

