from django.contrib import admin
from .models import Document, DocumentPermission, DocumentComment, DocumentVersion

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'document_type', 'created_at', 'updated_at')
    list_filter = ('document_type', 'created_at', 'owner')
    search_fields = ('title', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('document__title', 'user__username')

@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'created_at', 'resolved')
    list_filter = ('resolved', 'created_at')
    search_fields = ('document__title', 'user__username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('document', 'version_number', 'created_by', 'created_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('document__title',)
    readonly_fields = ('created_at',)
