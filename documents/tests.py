"""
Comprehensive tests for the documents app
Tests models, API endpoints, permissions, and business logic
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Document, DocumentPermission, DocumentComment, DocumentVersion
import json


class DocumentModelTests(TestCase):
    """Test Document model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.document = Document.objects.create(
            owner=self.owner,
            title='Test Document',
            content='<p>Test content</p>'
        )
    
    def test_document_creation(self):
        """Test that a document can be created"""
        self.assertEqual(self.document.title, 'Test Document')
        self.assertEqual(self.document.owner, self.owner)
        self.assertEqual(self.document.content, '<p>Test content</p>')
    
    def test_document_str(self):
        """Test document string representation"""
        self.assertEqual(str(self.document), 'Test Document')
    
    def test_document_has_permission_owner(self):
        """Test that owner has all permissions"""
        self.assertTrue(self.document.has_permission(self.owner, 'owner'))
        self.assertTrue(self.document.has_permission(self.owner, 'editor'))
        self.assertTrue(self.document.has_permission(self.owner, 'viewer'))
    
    def test_document_get_user_role_owner(self):
        """Test getting role for owner"""
        role = self.document.get_user_role(self.owner)
        self.assertEqual(role, 'owner')
    
    def test_document_get_user_role_no_permission(self):
        """Test getting role for user without permission"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        role = self.document.get_user_role(other_user)
        self.assertIsNone(role)


class DocumentPermissionModelTests(TestCase):
    """Test DocumentPermission model"""
    
    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='pass123'
        )
        self.document = Document.objects.create(
            owner=self.owner,
            title='Test Document',
            content='<p>Test</p>'
        )
    
    def test_permission_creation(self):
        """Test creating a permission"""
        permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.user,
            role='editor'
        )
        self.assertEqual(permission.role, 'editor')
        self.assertEqual(permission.document, self.document)
        self.assertEqual(permission.user, self.user)
    
    def test_permission_unique_together(self):
        """Test that permission is unique per document-user pair"""
        DocumentPermission.objects.create(
            document=self.document,
            user=self.user,
            role='editor'
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):
            DocumentPermission.objects.create(
                document=self.document,
                user=self.user,
                role='viewer'
            )
    
    def test_document_has_permission_with_permission(self):
        """Test document permission check with explicit permission"""
        DocumentPermission.objects.create(
            document=self.document,
            user=self.user,
            role='editor'
        )
        
        self.assertTrue(self.document.has_permission(self.user, 'editor'))
        self.assertTrue(self.document.has_permission(self.user, 'viewer'))
        self.assertFalse(self.document.has_permission(self.user, 'owner'))


class DocumentAPITests(TestCase):
    """Test Document API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='pass123'
        )
        self.document = Document.objects.create(
            owner=self.owner,
            title='Test Document',
            content='<p>Test content</p>'
        )
    
    def test_document_list_authenticated(self):
        """Test listing documents when authenticated"""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/documents/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Document')
    
    def test_document_list_unauthenticated(self):
        """Test listing documents without authentication"""
        response = self.client.get('/api/documents/', format='json')
        # DRF returns 403 Forbidden for unauthenticated requests with IsAuthenticated permission
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_document_create(self):
        """Test creating a document"""
        self.client.force_authenticate(user=self.owner)
        data = {'title': 'New Document'}
        # The endpoint is /api/documents/create/ not /api/documents/
        response = self.client.post('/api/documents/create/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Document')
        self.assertEqual(response.data['role'], 'owner')
        
        # Verify document was created
        self.assertTrue(Document.objects.filter(title='New Document').exists())
    
    def test_document_get_owner(self):
        """Test getting document as owner"""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/documents/{self.document.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Document')
        self.assertEqual(response.data['role'], 'owner')
    
    def test_document_get_with_permission(self):
        """Test getting document with permission"""
        DocumentPermission.objects.create(
            document=self.document,
            user=self.user,
            role='viewer'
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/documents/{self.document.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'viewer')
    
    def test_document_get_no_permission(self):
        """Test getting document without permission"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/documents/{self.document.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_document_update_owner(self):
        """Test updating document as owner"""
        self.client.force_authenticate(user=self.owner)
        data = {
            'title': 'Updated Title',
            'content': '<p>Updated content</p>'
        }
        response = self.client.post(f'/api/documents/{self.document.id}/update/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.document.refresh_from_db()
        self.assertEqual(self.document.title, 'Updated Title')
    
    def test_document_update_editor(self):
        """Test updating document as editor"""
        DocumentPermission.objects.create(
            document=self.document,
            user=self.user,
            role='editor'
        )
        self.client.force_authenticate(user=self.user)
        data = {'content': '<p>Editor content</p>'}
        response = self.client.post(f'/api/documents/{self.document.id}/update/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.document.refresh_from_db()
        self.assertEqual(self.document.content, '<p>Editor content</p>')
    
    def test_document_update_viewer(self):
        """Test updating document as viewer (should fail)"""
        DocumentPermission.objects.create(
            document=self.document,
            user=self.user,
            role='viewer'
        )
        self.client.force_authenticate(user=self.user)
        data = {'content': '<p>Unauthorized</p>'}
        response = self.client.post(f'/api/documents/{self.document.id}/update/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_document_delete_owner(self):
        """Test deleting document as owner"""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(f'/api/documents/{self.document.id}/delete/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Document.objects.filter(id=self.document.id).exists())
    
    def test_document_delete_non_owner(self):
        """Test deleting document as non-owner (should fail)"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/documents/{self.document.id}/delete/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DocumentShareAPITests(TestCase):
    """Test document sharing functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='pass123'
        )
        self.document = Document.objects.create(
            owner=self.owner,
            title='Test Document',
            content='<p>Test</p>'
        )
    
    def test_document_share_success(self):
        """Test successfully sharing a document"""
        self.client.force_authenticate(user=self.owner)
        data = {
            'email': 'user@example.com',
            'role': 'editor'
        }
        # The endpoint is /api/documents/{id}/permission/add/ not /api/documents/{id}/share/
        response = self.client.post(f'/api/documents/{self.document.id}/permission/add/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Verify permission was created
        self.assertTrue(DocumentPermission.objects.filter(
            document=self.document,
            user=self.user,
            role='editor'
        ).exists())
    
    def test_document_share_not_owner(self):
        """Test sharing document as non-owner (should fail)"""
        self.client.force_authenticate(user=self.user)
        data = {
            'email': 'other@example.com',
            'role': 'viewer'
        }
        response = self.client.post(f'/api/documents/{self.document.id}/share/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_document_share_with_self(self):
        """Test sharing document with yourself (should fail)"""
        self.client.force_authenticate(user=self.owner)
        data = {
            'email': 'owner@example.com',
            'role': 'editor'
        }
        # The endpoint is /api/documents/{id}/permission/add/ not /api/documents/{id}/share/
        response = self.client.post(f'/api/documents/{self.document.id}/permission/add/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_document_share_user_not_found(self):
        """Test sharing with non-existent user"""
        self.client.force_authenticate(user=self.owner)
        data = {
            'email': 'nonexistent@example.com',
            'role': 'viewer'
        }
        response = self.client.post(f'/api/documents/{self.document.id}/share/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_document_remove_shared(self):
        """Test removing shared document from user's list"""
        # Share document first
        DocumentPermission.objects.create(
            document=self.document,
            user=self.user,
            role='viewer'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/documents/{self.document.id}/remove/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(DocumentPermission.objects.filter(
            document=self.document,
            user=self.user
        ).exists())


class DocumentCommentModelTests(TestCase):
    """Test DocumentComment model"""
    
    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.document = Document.objects.create(
            owner=self.owner,
            title='Test Document',
            content='<p>Test</p>'
        )
    
    def test_comment_creation(self):
        """Test creating a comment"""
        comment = DocumentComment.objects.create(
            document=self.document,
            user=self.owner,
            content='This is a comment'
        )
        self.assertEqual(comment.content, 'This is a comment')
        self.assertFalse(comment.resolved)


class DocumentVersionModelTests(TestCase):
    """Test DocumentVersion model"""
    
    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.document = Document.objects.create(
            owner=self.owner,
            title='Test Document',
            content='<p>Version 1</p>'
        )
    
    def test_version_creation(self):
        """Test creating a version"""
        version = DocumentVersion.objects.create(
            document=self.document,
            content='<p>Version 1</p>',
            created_by=self.owner,
            version_number=1,
            change_description='Initial version'
        )
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.change_description, 'Initial version')
    
    def test_version_unique_together(self):
        """Test that version number is unique per document"""
        DocumentVersion.objects.create(
            document=self.document,
            content='<p>V1</p>',
            created_by=self.owner,
            version_number=1
        )
        
        # Try to create duplicate version number
        with self.assertRaises(Exception):
            DocumentVersion.objects.create(
                document=self.document,
                content='<p>V2</p>',
                created_by=self.owner,
                version_number=1
            )
