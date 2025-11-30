"""
Comprehensive tests for the notifications app
Tests models and API endpoints
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Notification
from documents.models import Document
from django.contrib.contenttypes.models import ContentType


class NotificationModelTests(TestCase):
    """Test Notification model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='pass123'
        )
        self.notification = Notification.objects.create(
            recipient=self.user,
            notification_type='share',
            title='Document Shared',
            message='A document was shared with you'
        )
    
    def test_notification_creation(self):
        """Test that a notification can be created"""
        self.assertEqual(self.notification.recipient, self.user)
        self.assertEqual(self.notification.notification_type, 'share')
        self.assertEqual(self.notification.title, 'Document Shared')
        self.assertFalse(self.notification.read)
    
    def test_notification_mark_as_read(self):
        """Test marking notification as read"""
        self.assertFalse(self.notification.read)
        self.notification.read = True
        self.notification.save()
        self.assertTrue(self.notification.read)
    
    def test_notification_with_content_object(self):
        """Test notification with related content object"""
        owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        document = Document.objects.create(
            owner=owner,
            title='Test Document',
            content='<p>Test</p>'
        )
        
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='share',
            title='Document Shared',
            message='A document was shared with you',
            content_type=ContentType.objects.get_for_model(Document),
            object_id=document.id
        )
        
        self.assertEqual(notification.content_object, document)


class NotificationAPITests(TestCase):
    """Test Notification API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='pass123'
        )
        # Create some notifications
        Notification.objects.create(
            recipient=self.user,
            notification_type='share',
            title='Document Shared 1',
            message='Message 1',
            read=False
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type='comment',
            title='New Comment',
            message='Message 2',
            read=True
        )
        # Create notification for another user
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        Notification.objects.create(
            recipient=other_user,
            notification_type='share',
            title='Document Shared',
            message='Message 3',
            read=False
        )
    
    def test_notification_list_authenticated(self):
        """Test listing notifications when authenticated"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/notifications/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        # Should only return notifications for the authenticated user
        self.assertEqual(len(response.data), 2)
        # Should be ordered by created_at descending
        self.assertEqual(response.data[0]['title'], 'New Comment')
    
    def test_notification_list_unauthenticated(self):
        """Test listing notifications without authentication"""
        response = self.client.get('/api/notifications/', format='json')
        # DRF returns 403 Forbidden for unauthenticated requests with IsAuthenticated permission
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unread_count_authenticated(self):
        """Test getting unread count when authenticated"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/notifications/unread-count/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('unread_count', response.data)
        # Should have 1 unread notification
        self.assertEqual(response.data['unread_count'], 1)
    
    def test_unread_count_unauthenticated(self):
        """Test getting unread count without authentication"""
        response = self.client.get('/api/notifications/unread-count/', format='json')
        # DRF returns 403 Forbidden for unauthenticated requests with IsAuthenticated permission
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_notification_list_limit(self):
        """Test that notification list is limited to 50"""
        # Create 60 notifications
        for i in range(60):
            Notification.objects.create(
                recipient=self.user,
                notification_type='share',
                title=f'Notification {i}',
                message=f'Message {i}'
            )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/notifications/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be limited to 50
        self.assertLessEqual(len(response.data), 50)
