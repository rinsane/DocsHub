from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from documents.models import Document, DocumentPermission
from spreadsheets.models import Spreadsheet, SpreadsheetPermission
from notifications.models import Notification

# Unregister the default User admin
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced User admin with related documents and spreadsheets"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'document_count', 'spreadsheet_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    
    def document_count(self, obj):
        """Count of documents owned by user"""
        return obj.owned_documents.count()
    document_count.short_description = 'Documents'
    
    def spreadsheet_count(self, obj):
        """Count of spreadsheets owned by user"""
        return obj.owned_spreadsheets.count()
    spreadsheet_count.short_description = 'Spreadsheets'
    
    actions = ['activate_users', 'deactivate_users', 'delete_user_data']
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) activated successfully.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated successfully.')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def delete_user_data(self, request, queryset):
        """Delete all documents and spreadsheets owned by selected users"""
        doc_count = 0
        sheet_count = 0
        for user in queryset:
            doc_count += user.owned_documents.count()
            sheet_count += user.owned_spreadsheets.count()
            user.owned_documents.all().delete()
            user.owned_spreadsheets.all().delete()
        self.message_user(request, f'Deleted {doc_count} document(s) and {sheet_count} spreadsheet(s).')
    delete_user_data.short_description = 'Delete all data owned by selected users'
