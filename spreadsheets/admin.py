from django.contrib import admin
from .models import Spreadsheet, SpreadsheetPermission, SpreadsheetComment, SpreadsheetVersion

@admin.register(Spreadsheet)
class SpreadsheetAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at', 'updated_at')
    list_filter = ('created_at', 'owner')
    search_fields = ('title', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(SpreadsheetPermission)
class SpreadsheetPermissionAdmin(admin.ModelAdmin):
    list_display = ('spreadsheet', 'user', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('spreadsheet__title', 'user__username')

@admin.register(SpreadsheetComment)
class SpreadsheetCommentAdmin(admin.ModelAdmin):
    list_display = ('spreadsheet', 'user', 'sheet_name', 'row', 'column', 'created_at', 'resolved')
    list_filter = ('resolved', 'created_at', 'sheet_name')
    search_fields = ('spreadsheet__title', 'user__username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(SpreadsheetVersion)
class SpreadsheetVersionAdmin(admin.ModelAdmin):
    list_display = ('spreadsheet', 'version_number', 'created_by', 'created_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('spreadsheet__title',)
    readonly_fields = ('created_at',)
