from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Spreadsheet, SpreadsheetPermission, SpreadsheetComment, SpreadsheetVersion

@admin.register(Spreadsheet)
class SpreadsheetAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at', 'updated_at', 'permission_count', 'comment_count', 'view_spreadsheet')
    list_filter = ('created_at', 'owner')
    search_fields = ('title', 'owner__username')
    readonly_fields = ('created_at', 'updated_at', 'data', 'last_edited_by')
    
    fieldsets = (
        ('Spreadsheet Information', {
            'fields': ('title', 'owner')
        }),
        ('Data (Read-Only)', {
            'fields': ('data',),
            'description': 'Spreadsheet data is read-only in admin. Edit through the spreadsheet editor.'
        }),
        ('Metadata', {
            'fields': ('last_edited_by', 'created_at', 'updated_at')
        }),
    )
    
    def permission_count(self, obj):
        """Count of users with access"""
        count = obj.permissions.count()
        return format_html('<a href="{}?spreadsheet__id__exact={}">{}</a>',
                          reverse('admin:spreadsheets_spreadsheetpermission_changelist'),
                          obj.id,
                          count)
    permission_count.short_description = 'Shared With'
    
    def comment_count(self, obj):
        """Count of comments"""
        count = obj.comments.count()
        return format_html('<a href="{}?spreadsheet__id__exact={}">{}</a>',
                          reverse('admin:spreadsheets_spreadsheetcomment_changelist'),
                          obj.id,
                          count)
    comment_count.short_description = 'Comments'
    
    def view_spreadsheet(self, obj):
        """Link to view spreadsheet"""
        return format_html('<a href="/spreadsheet/{}" target="_blank">View Spreadsheet</a>', obj.id)
    view_spreadsheet.short_description = 'View'
    
    def get_readonly_fields(self, request, obj=None):
        """Make data and important fields read-only"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('title', 'owner')
        return self.readonly_fields

@admin.register(SpreadsheetPermission)
class SpreadsheetPermissionAdmin(admin.ModelAdmin):
    list_display = ('spreadsheet', 'user', 'role', 'created_at', 'view_spreadsheet')
    list_filter = ('role', 'created_at')
    search_fields = ('spreadsheet__title', 'user__username')
    readonly_fields = ('created_at',)
    
    def view_spreadsheet(self, obj):
        """Link to view the spreadsheet"""
        return format_html('<a href="/spreadsheet/{}" target="_blank">Open</a>', obj.spreadsheet.id)
    view_spreadsheet.short_description = 'Spreadsheet'

@admin.register(SpreadsheetComment)
class SpreadsheetCommentAdmin(admin.ModelAdmin):
    list_display = ('spreadsheet', 'user', 'sheet_name', 'cell_location', 'content_preview', 'created_at', 'resolved', 'view_spreadsheet')
    list_filter = ('resolved', 'created_at', 'sheet_name')
    search_fields = ('spreadsheet__title', 'user__username', 'content')
    readonly_fields = ('created_at', 'updated_at')
    
    def cell_location(self, obj):
        """Display cell location in spreadsheet notation"""
        # Convert column number to letter (0=A, 1=B, etc.)
        col_letter = chr(65 + obj.column) if obj.column < 26 else f"Col{obj.column}"
        return f"{col_letter}{obj.row + 1}"
    cell_location.short_description = 'Cell'
    
    def content_preview(self, obj):
        """Show preview of comment content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Comment'
    
    def view_spreadsheet(self, obj):
        """Link to view the spreadsheet"""
        return format_html('<a href="/spreadsheet/{}" target="_blank">Open</a>', obj.spreadsheet.id)
    view_spreadsheet.short_description = 'Spreadsheet'

@admin.register(SpreadsheetVersion)
class SpreadsheetVersionAdmin(admin.ModelAdmin):
    list_display = ('spreadsheet', 'version_number', 'created_by', 'created_at', 'change_description')
    list_filter = ('created_at', 'created_by')
    search_fields = ('spreadsheet__title', 'change_description')
    readonly_fields = ('created_at', 'data')
    
    fieldsets = (
        ('Version Information', {
            'fields': ('spreadsheet', 'version_number', 'created_by', 'change_description')
        }),
        ('Data Snapshot (Read-Only)', {
            'fields': ('data',),
            'description': 'Historical snapshot of spreadsheet data at this version.'
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
