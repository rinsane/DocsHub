from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class Document(models.Model):
    """Main document model for rich text documents"""
    
    DOCUMENT_TYPES = [
        ('docx', 'Word Document'),
        ('txt', 'Plain Text'),
        ('md', 'Markdown'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_documents')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default='')  # Stores HTML content
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES, default='docx')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='last_edited_documents')
    
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
        except DocumentPermission.DoesNotExist:
            return False
    
    def get_user_role(self, user):
        """Get the role of a user for this document"""
        if self.owner == user:
            return 'owner'
        try:
            permission = self.permissions.get(user=user)
            return permission.role
        except DocumentPermission.DoesNotExist:
            return None


class DocumentPermission(models.Model):
    """Role-based access control for documents"""
    
    ROLES = [
        ('owner', 'Owner'),
        ('editor', 'Editor'),
        ('commenter', 'Commenter'),
        ('viewer', 'Viewer'),
    ]
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='permissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_permissions')
    role = models.CharField(max_length=20, choices=ROLES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['document', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.role} on {self.document.title}"


class DocumentComment(models.Model):
    """Comments on documents"""
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    # For storing selection/range information if needed
    selection_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.document.title}"


class DocumentVersion(models.Model):
    """Version history for documents"""
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    content = models.TextField()  # Snapshot of content
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    version_number = models.IntegerField()
    change_description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ['document', 'version_number']
    
    def __str__(self):
        return f"{self.document.title} - Version {self.version_number}"
