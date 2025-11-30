"""
Comprehensive tests for the spreadsheets app
Tests models, API endpoints, and business logic
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Spreadsheet, SpreadsheetPermission, SpreadsheetComment, SpreadsheetVersion
import json


class SpreadsheetModelTests(TestCase):
    """Test Spreadsheet model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.spreadsheet = Spreadsheet.objects.create(
            owner=self.owner,
            title='Test Spreadsheet',
            data={'sheets': [{'name': 'Sheet1', 'data': [['A1', 'B1'], ['A2', 'B2']]}]}
        )
    
    def test_spreadsheet_creation(self):
        """Test that a spreadsheet can be created"""
        self.assertEqual(self.spreadsheet.title, 'Test Spreadsheet')
        self.assertEqual(self.spreadsheet.owner, self.owner)
        self.assertIsInstance(self.spreadsheet.data, dict)
        self.assertIn('sheets', self.spreadsheet.data)
    
    def test_spreadsheet_str(self):
        """Test spreadsheet string representation"""
        self.assertEqual(str(self.spreadsheet), 'Test Spreadsheet')
    
    def test_spreadsheet_has_permission_owner(self):
        """Test that owner has all permissions"""
        self.assertTrue(self.spreadsheet.has_permission(self.owner, 'owner'))
        self.assertTrue(self.spreadsheet.has_permission(self.owner, 'editor'))
        self.assertTrue(self.spreadsheet.has_permission(self.owner, 'viewer'))
    
    def test_spreadsheet_get_user_role_owner(self):
        """Test getting role for owner"""
        role = self.spreadsheet.get_user_role(self.owner)
        self.assertEqual(role, 'owner')
    
    def test_spreadsheet_get_user_role_no_permission(self):
        """Test getting role for user without permission"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        role = self.spreadsheet.get_user_role(other_user)
        self.assertIsNone(role)


class SpreadsheetPermissionModelTests(TestCase):
    """Test SpreadsheetPermission model"""
    
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
        self.spreadsheet = Spreadsheet.objects.create(
            owner=self.owner,
            title='Test Spreadsheet',
            data={'sheets': [{'name': 'Sheet1', 'data': [[]]}]}
        )
    
    def test_permission_creation(self):
        """Test creating a permission"""
        permission = SpreadsheetPermission.objects.create(
            spreadsheet=self.spreadsheet,
            user=self.user,
            role='editor'
        )
        self.assertEqual(permission.role, 'editor')
        self.assertEqual(permission.spreadsheet, self.spreadsheet)
        self.assertEqual(permission.user, self.user)
    
    def test_permission_unique_together(self):
        """Test that permission is unique per spreadsheet-user pair"""
        SpreadsheetPermission.objects.create(
            spreadsheet=self.spreadsheet,
            user=self.user,
            role='editor'
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):
            SpreadsheetPermission.objects.create(
                spreadsheet=self.spreadsheet,
                user=self.user,
                role='viewer'
            )
    
    def test_spreadsheet_has_permission_with_permission(self):
        """Test spreadsheet permission check with explicit permission"""
        SpreadsheetPermission.objects.create(
            spreadsheet=self.spreadsheet,
            user=self.user,
            role='editor'
        )
        
        self.assertTrue(self.spreadsheet.has_permission(self.user, 'editor'))
        self.assertTrue(self.spreadsheet.has_permission(self.user, 'viewer'))
        self.assertFalse(self.spreadsheet.has_permission(self.user, 'owner'))


class SpreadsheetAPITests(TestCase):
    """Test Spreadsheet API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.spreadsheet = Spreadsheet.objects.create(
            owner=self.owner,
            title='Test Spreadsheet',
            data={'sheets': [{'name': 'Sheet1', 'data': [[]]}]}
        )
    
    def test_spreadsheet_list_authenticated(self):
        """Test listing spreadsheets when authenticated"""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/spreadsheets/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Spreadsheet')
    
    def test_spreadsheet_list_unauthenticated(self):
        """Test listing spreadsheets without authentication"""
        response = self.client.get('/api/spreadsheets/', format='json')
        # DRF returns 403 Forbidden for unauthenticated requests with IsAuthenticated permission
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_spreadsheet_create(self):
        """Test creating a spreadsheet"""
        self.client.force_authenticate(user=self.owner)
        data = {'title': 'New Spreadsheet'}
        # The endpoint is /api/spreadsheets/create/ not /api/spreadsheets/
        response = self.client.post('/api/spreadsheets/create/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Spreadsheet')
        self.assertIn('data', response.data)
        
        # Verify spreadsheet was created
        self.assertTrue(Spreadsheet.objects.filter(title='New Spreadsheet').exists())
    
    def test_spreadsheet_get_owner(self):
        """Test getting spreadsheet as owner"""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/spreadsheets/{self.spreadsheet.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Spreadsheet')
        self.assertIn('data', response.data)
    
    def test_spreadsheet_get_non_owner(self):
        """Test getting spreadsheet as non-owner (should fail)"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.get(f'/api/spreadsheets/{self.spreadsheet.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_spreadsheet_update_owner(self):
        """Test updating spreadsheet as owner"""
        self.client.force_authenticate(user=self.owner)
        new_data = {'sheets': [{'name': 'Sheet1', 'data': [['Updated']]}]}
        data = {
            'title': 'Updated Title',
            'data': new_data
        }
        response = self.client.post(f'/api/spreadsheets/{self.spreadsheet.id}/update/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.spreadsheet.refresh_from_db()
        self.assertEqual(self.spreadsheet.title, 'Updated Title')
        self.assertEqual(self.spreadsheet.data, new_data)
    
    def test_spreadsheet_delete_owner(self):
        """Test deleting spreadsheet as owner"""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(f'/api/spreadsheets/{self.spreadsheet.id}/delete/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Spreadsheet.objects.filter(id=self.spreadsheet.id).exists())
    
    def test_spreadsheet_delete_non_owner(self):
        """Test deleting spreadsheet as non-owner (should fail)"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.post(f'/api/spreadsheets/{self.spreadsheet.id}/delete/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SpreadsheetCommentModelTests(TestCase):
    """Test SpreadsheetComment model"""
    
    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.spreadsheet = Spreadsheet.objects.create(
            owner=self.owner,
            title='Test Spreadsheet',
            data={'sheets': [{'name': 'Sheet1', 'data': [[]]}]}
        )
    
    def test_comment_creation(self):
        """Test creating a comment"""
        comment = SpreadsheetComment.objects.create(
            spreadsheet=self.spreadsheet,
            user=self.owner,
            content='This is a comment',
            sheet_name='Sheet1',
            row=0,
            column=0
        )
        self.assertEqual(comment.content, 'This is a comment')
        self.assertEqual(comment.sheet_name, 'Sheet1')
        self.assertEqual(comment.row, 0)
        self.assertEqual(comment.column, 0)
        self.assertFalse(comment.resolved)


class SpreadsheetVersionModelTests(TestCase):
    """Test SpreadsheetVersion model"""
    
    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.spreadsheet = Spreadsheet.objects.create(
            owner=self.owner,
            title='Test Spreadsheet',
            data={'sheets': [{'name': 'Sheet1', 'data': [[]]}]}
        )
    
    def test_version_creation(self):
        """Test creating a version"""
        version = SpreadsheetVersion.objects.create(
            spreadsheet=self.spreadsheet,
            data={'sheets': [{'name': 'Sheet1', 'data': [[]]}]},
            created_by=self.owner,
            version_number=1,
            change_description='Initial version'
        )
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.change_description, 'Initial version')
    
    def test_version_unique_together(self):
        """Test that version number is unique per spreadsheet"""
        SpreadsheetVersion.objects.create(
            spreadsheet=self.spreadsheet,
            data={'sheets': [{'name': 'Sheet1', 'data': [[]]}]},
            created_by=self.owner,
            version_number=1
        )
        
        # Try to create duplicate version number
        with self.assertRaises(Exception):
            SpreadsheetVersion.objects.create(
                spreadsheet=self.spreadsheet,
                data={'sheets': [{'name': 'Sheet1', 'data': [[]]}]},
                created_by=self.owner,
                version_number=1
            )
