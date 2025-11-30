from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class Spreadsheet(models.Model):
    """Main spreadsheet model"""
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_spreadsheets')
    title = models.CharField(max_length=255)
    # Stores JSON structure: {"sheets": [{"name": "Sheet1", "data": [[...]]}]}
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='last_edited_spreadsheets')
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title
    
    def has_permission(self, user, required_role='viewer'):
        """Check if user has required permission level"""
        role_hierarchy = {'owner': 4, 'editor': 3, 'commenter': 2, 'viewer': 1}
        
        if self.owner == user:
            return True
        
        try:
            permission = self.permissions.get(user=user)
            user_level = role_hierarchy.get(permission.role, 0)
            required_level = role_hierarchy.get(required_role, 0)
            return user_level >= required_level
        except SpreadsheetPermission.DoesNotExist:
            return False
    
    def get_user_role(self, user):
        """Get the role of a user for this spreadsheet"""
        if self.owner == user:
            return 'owner'
        try:
            permission = self.permissions.get(user=user)
            return permission.role
        except SpreadsheetPermission.DoesNotExist:
            return None


class SpreadsheetPermission(models.Model):
    """Role-based access control for spreadsheets"""
    
    ROLES = [
        ('owner', 'Owner'),
        ('editor', 'Editor'),
        ('commenter', 'Commenter'),
        ('viewer', 'Viewer'),
    ]
    
    spreadsheet = models.ForeignKey(Spreadsheet, on_delete=models.CASCADE, related_name='permissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='spreadsheet_permissions')
    role = models.CharField(max_length=20, choices=ROLES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['spreadsheet', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.role} on {self.spreadsheet.title}"


class SpreadsheetComment(models.Model):
    """Comments on spreadsheet cells"""
    
    spreadsheet = models.ForeignKey(Spreadsheet, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    # Cell location information
    sheet_name = models.CharField(max_length=100, default='Sheet1')
    row = models.IntegerField()
    column = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.spreadsheet.title} ({self.sheet_name}:{self.row},{self.column})"


class SpreadsheetVersion(models.Model):
    """Version history for spreadsheets"""
    
    spreadsheet = models.ForeignKey(Spreadsheet, on_delete=models.CASCADE, related_name='versions')
    data = models.JSONField()  # Snapshot of data
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    version_number = models.IntegerField()
    change_description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ['spreadsheet', 'version_number']
    
    def __str__(self):
        return f"{self.spreadsheet.title} - Version {self.version_number}"
