from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Document, DocumentPermission, DocumentComment, DocumentVersion

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'document_type', 'created_at', 'updated_at', 'permission_count', 'comment_count', 'view_content')
    list_filter = ('document_type', 'created_at', 'owner')
    search_fields = ('title', 'owner__username', 'content')
    readonly_fields = ('created_at', 'updated_at', 'content', 'last_edited_by')
    
    fieldsets = (
        ('Document Information', {
            'fields': ('title', 'owner', 'document_type')
        }),
        ('Content (Read-Only)', {
            'fields': ('content',),
            'description': 'Document content is read-only in admin. Edit through the document editor.'
        }),
        ('Metadata', {
            'fields': ('last_edited_by', 'created_at', 'updated_at')
        }),
    )
    
    def permission_count(self, obj):
        """Count of users with access"""
        count = obj.permissions.count()
        return format_html('<a href="{}?document__id__exact={}">{}</a>',
                          reverse('admin:documents_documentpermission_changelist'),
                          obj.id,
                          count)
    permission_count.short_description = 'Shared With'
    
    def comment_count(self, obj):
        """Count of comments"""
        count = obj.comments.count()
        return format_html('<a href="{}?document__id__exact={}">{}</a>',
                          reverse('admin:documents_documentcomment_changelist'),
                          obj.id,
                          count)
    comment_count.short_description = 'Comments'
    
    def view_content(self, obj):
        """Link to view content in a popup"""
        return format_html('<a href="/document/{}" target="_blank">View Document</a>', obj.id)
    view_content.short_description = 'View'
    
    def has_change_permission(self, request, obj=None):
        """Allow viewing but make content read-only"""
        return True
    
    def get_readonly_fields(self, request, obj=None):
        """Make content and important fields read-only"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('title', 'owner', 'document_type')
        return self.readonly_fields

@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'role', 'created_at', 'view_document')
    list_filter = ('role', 'created_at')
    search_fields = ('document__title', 'user__username')
    readonly_fields = ('created_at',)
    
    def view_document(self, obj):
        """Link to view the document"""
        return format_html('<a href="/document/{}" target="_blank">Open</a>', obj.document.id)
    view_document.short_description = 'Document'

@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'content_preview', 'created_at', 'resolved', 'view_document')
    list_filter = ('resolved', 'created_at')
    search_fields = ('document__title', 'user__username', 'content')
    readonly_fields = ('created_at', 'updated_at')
    
    def content_preview(self, obj):
        """Show preview of comment content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Comment'
    
    def view_document(self, obj):
        """Link to view the document"""
        return format_html('<a href="/document/{}" target="_blank">Open</a>', obj.document.id)
    view_document.short_description = 'Document'

@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('document', 'version_number', 'created_by', 'created_at', 'change_description')
    list_filter = ('created_at', 'created_by')
    search_fields = ('document__title', 'change_description')
    readonly_fields = ('created_at', 'content')
    
    fieldsets = (
        ('Version Information', {
            'fields': ('document', 'version_number', 'created_by', 'change_description')
        }),
        ('Content Snapshot (Read-Only)', {
            'fields': ('content',),
            'description': 'Historical snapshot of document content at this version.'
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
