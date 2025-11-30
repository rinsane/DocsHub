"""
Comprehensive tests for the collaboration app
Tests WebSocket consumers for real-time collaboration

Note: These tests require Redis to be running and channels.testing to be available.
If channels.testing is not available, these tests will be skipped.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from documents.models import Document, DocumentPermission
from spreadsheets.models import Spreadsheet
import json
import unittest

# Try to import channels.testing, skip tests if not available
try:
    from channels.testing import WebsocketCommunicator
    from docshub.asgi import application
    CHANNELS_TESTING_AVAILABLE = True
except ImportError:
    CHANNELS_TESTING_AVAILABLE = False
    print("Warning: channels.testing not available. WebSocket tests will be skipped.")


@unittest.skipIf(not CHANNELS_TESTING_AVAILABLE, "channels.testing not available")
class DocumentConsumerTests(TransactionTestCase):
    """Test DocumentConsumer WebSocket functionality"""
    
    async def setUp(self):
        """Set up test data"""
        self.owner = await database_sync_to_async(User.objects.create_user)(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.user = await database_sync_to_async(User.objects.create_user)(
            username='user',
            email='user@example.com',
            password='pass123'
        )
        self.document = await database_sync_to_async(Document.objects.create)(
            owner=self.owner,
            title='Test Document',
            content='<p>Initial content</p>'
        )
    
    async def test_connect_authenticated_owner(self):
        """Test WebSocket connection as authenticated owner"""
        communicator = WebsocketCommunicator(
            application,
            f'/ws/document/{self.document.id}/'
        )
        communicator.scope['user'] = self.owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive current content
        response = await communicator.receive_json_from()
        self.assertIn('type', response)
        
        await communicator.disconnect()
    
    async def test_connect_authenticated_with_permission(self):
        """Test WebSocket connection with permission"""
        await database_sync_to_async(DocumentPermission.objects.create)(
            document=self.document,
            user=self.user,
            role='editor'
        )
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/document/{self.document.id}/'
        )
        communicator.scope['user'] = self.user
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.disconnect()
    
    async def test_connect_unauthenticated(self):
        """Test WebSocket connection without authentication"""
        communicator = WebsocketCommunicator(
            application,
            f'/ws/document/{self.document.id}/'
        )
        communicator.scope['user'] = await database_sync_to_async(User.objects.create)(
            username='anonymous',
            is_active=False
        )
        
        connected, subprotocol = await communicator.connect()
        # Should close connection for unauthenticated users
        self.assertFalse(connected)
    
    async def test_connect_no_permission(self):
        """Test WebSocket connection without permission"""
        other_user = await database_sync_to_async(User.objects.create_user)(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/document/{self.document.id}/'
        )
        communicator.scope['user'] = other_user
        
        connected, subprotocol = await communicator.connect()
        # Should close connection for users without permission
        self.assertFalse(connected)
    
    async def test_receive_content_update(self):
        """Test receiving content update message"""
        communicator = WebsocketCommunicator(
            application,
            f'/ws/document/{self.document.id}/'
        )
        communicator.scope['user'] = self.owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send content update
        await communicator.send_json_to({
            'type': 'content_update',
            'content': '<p>Updated content</p>'
        })
        
        # Should receive broadcast
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'content_update')
        self.assertEqual(response['content'], '<p>Updated content</p>')
        
        await communicator.disconnect()
    
    async def test_receive_title_update(self):
        """Test receiving title update message"""
        communicator = WebsocketCommunicator(
            application,
            f'/ws/document/{self.document.id}/'
        )
        communicator.scope['user'] = self.owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send title update
        await communicator.send_json_to({
            'type': 'title_update',
            'title': 'Updated Title'
        })
        
        # Should receive broadcast
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'title_update')
        self.assertEqual(response['title'], 'Updated Title')
        
        await communicator.disconnect()
    
    async def test_user_joined_notification(self):
        """Test that other users are notified when a user joins"""
        # First user connects
        communicator1 = WebsocketCommunicator(
            application,
            f'/ws/document/{self.document.id}/'
        )
        communicator1.scope['user'] = self.owner
        connected1, _ = await communicator1.connect()
        self.assertTrue(connected1)
        
        # Second user connects
        await database_sync_to_async(DocumentPermission.objects.create)(
            document=self.document,
            user=self.user,
            role='viewer'
        )
        
        communicator2 = WebsocketCommunicator(
            application,
            f'/ws/document/{self.document.id}/'
        )
        communicator2.scope['user'] = self.user
        connected2, _ = await communicator2.connect()
        self.assertTrue(connected2)
        
        # First user should receive user_joined notification
        response = await communicator1.receive_json_from()
        # Skip initial content message
        if response['type'] == 'content_update':
            response = await communicator1.receive_json_from()
        
        self.assertEqual(response['type'], 'user_joined')
        self.assertEqual(response['username'], 'user')
        
        await communicator1.disconnect()
        await communicator2.disconnect()


@unittest.skipIf(not CHANNELS_TESTING_AVAILABLE, "channels.testing not available")
class SpreadsheetConsumerTests(TransactionTestCase):
    """Test SpreadsheetConsumer WebSocket functionality"""
    
    async def setUp(self):
        """Set up test data"""
        self.owner = await database_sync_to_async(User.objects.create_user)(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.spreadsheet = await database_sync_to_async(Spreadsheet.objects.create)(
            owner=self.owner,
            title='Test Spreadsheet',
            data={'sheets': [{'name': 'Sheet1', 'data': [[]]}]}
        )
    
    async def test_connect_authenticated_owner(self):
        """Test WebSocket connection as authenticated owner"""
        communicator = WebsocketCommunicator(
            application,
            f'/ws/spreadsheet/{self.spreadsheet.id}/'
        )
        communicator.scope['user'] = self.owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.disconnect()
    
    async def test_receive_data_update(self):
        """Test receiving data update message"""
        communicator = WebsocketCommunicator(
            application,
            f'/ws/spreadsheet/{self.spreadsheet.id}/'
        )
        communicator.scope['user'] = self.owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send data update
        new_data = {'sheets': [{'name': 'Sheet1', 'data': [['A1', 'B1']]}]}
        await communicator.send_json_to({
            'type': 'data_update',
            'data': new_data
        })
        
        # Should receive broadcast
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'data_update')
        self.assertEqual(response['data'], new_data)
        
        await communicator.disconnect()
