"""
Comprehensive tests for the collaboration app
Tests WebSocket consumers for real-time collaboration

Note: These tests require channels.testing to be available.
If channels.testing is not available, these tests will be skipped.
Tests use in-memory channel layer to avoid requiring Redis.
"""

from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from documents.models import Document, DocumentPermission
from spreadsheets.models import Spreadsheet
import json
import unittest

# Try to import channels.testing, skip tests if not available
try:
    from channels.testing import WebsocketCommunicator
    from channels.layers import InMemoryChannelLayer
    CHANNELS_TESTING_AVAILABLE = True
except ImportError:
    CHANNELS_TESTING_AVAILABLE = False
    print("Warning: channels.testing not available. WebSocket tests will be skipped.")

# Create in-memory channel layer for testing
if CHANNELS_TESTING_AVAILABLE:
    # Import ASGI application after setting up channel layer
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docshub.settings')
    import django
    django.setup()
    
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    from django.core.asgi import get_asgi_application
    import collaboration.routing
    
    # Use in-memory channel layer for tests
    test_channel_layer = InMemoryChannelLayer()
    
    # Create test ASGI application with in-memory channel layer
    django_asgi_app = get_asgi_application()
    test_application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                collaboration.routing.websocket_urlpatterns
            )
        ),
    })


@unittest.skipIf(not CHANNELS_TESTING_AVAILABLE, "channels.testing not available")
@override_settings(CHANNEL_LAYERS={
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
})
class DocumentConsumerTests(TransactionTestCase):
    """Test DocumentConsumer WebSocket functionality"""
    
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
            content='<p>Initial content</p>'
        )
    
    async def test_connect_authenticated_owner(self):
        """Test WebSocket connection as authenticated owner"""
        communicator = WebsocketCommunicator(
            test_application,
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
        from channels.db import database_sync_to_async
        
        await database_sync_to_async(DocumentPermission.objects.create)(
            document=self.document,
            user=self.user,
            role='editor'
        )
        
        communicator = WebsocketCommunicator(
            test_application,
            f'/ws/document/{self.document.id}/'
        )
        communicator.scope['user'] = self.user
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.disconnect()
    
    async def test_connect_unauthenticated(self):
        """Test WebSocket connection without authentication"""
        from channels.db import database_sync_to_async
        from django.contrib.auth.models import AnonymousUser
        
        communicator = WebsocketCommunicator(
            test_application,
            f'/ws/document/{self.document.id}/'
        )
        communicator.scope['user'] = AnonymousUser()
        
        connected, subprotocol = await communicator.connect()
        # Should close connection for unauthenticated users
        self.assertFalse(connected)
    
    async def test_connect_no_permission(self):
        """Test WebSocket connection without permission"""
        from channels.db import database_sync_to_async
        
        other_user = await database_sync_to_async(User.objects.create_user)(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        
        communicator = WebsocketCommunicator(
            test_application,
            f'/ws/document/{self.document.id}/'
        )
        communicator.scope['user'] = other_user
        
        connected, subprotocol = await communicator.connect()
        # Should close connection for users without permission
        self.assertFalse(connected)
    


@unittest.skipIf(not CHANNELS_TESTING_AVAILABLE, "channels.testing not available")
@override_settings(CHANNEL_LAYERS={
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
})
class SpreadsheetConsumerTests(TransactionTestCase):
    """Test SpreadsheetConsumer WebSocket functionality"""
    
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
    
    async def test_connect_authenticated_owner(self):
        """Test WebSocket connection as authenticated owner"""
        communicator = WebsocketCommunicator(
            test_application,
            f'/ws/spreadsheet/{self.spreadsheet.id}/'
        )
        communicator.scope['user'] = self.owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.disconnect()
    
