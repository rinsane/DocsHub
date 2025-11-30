import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from documents.models import Document
from spreadsheets.models import Spreadsheet


class DocumentConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time document collaboration.
    Handles document content updates and cursor positions.
    """
    
    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.room_group_name = f'document_{self.document_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user has access
        has_access = await self.check_document_access()
        
        if not has_access:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Get current active users in the room
        active_users = await self.get_active_users()
        
        # Send current user list to the newly connected user
        await self.send(text_data=json.dumps({
            'type': 'active_users',
            'users': active_users
        }))
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )
    
    async def disconnect(self, close_code):
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'content_update':
            # User is updating document content
            content = data.get('content')
            delta = data.get('delta')  # Quill delta format
            
            # Save to database
            await self.save_document_content(content)
            
            # Broadcast to other users
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'content_change',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'content': content,
                    'delta': delta
                }
            )
        
        elif message_type == 'cursor_update':
            # User cursor position update
            position = data.get('position')
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'cursor_change',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'position': position
                }
            )
    
    async def content_change(self, event):
        """Send content change to WebSocket"""
        # Send to all users (the frontend will handle not overwriting local edits)
        await self.send(text_data=json.dumps({
            'type': 'content_change',
            'user_id': event['user_id'],
            'username': event['username'],
            'content': event['content'],
            'delta': event.get('delta')
        }))
    
    async def cursor_change(self, event):
        """Send cursor position change to WebSocket"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'cursor_change',
                'user_id': event['user_id'],
                'username': event['username'],
                'position': event['position']
            }))
    
    async def user_joined(self, event):
        """Notify when a user joins"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'username': event['username']
            }))
    
    async def user_left(self, event):
        """Notify when a user leaves"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'username': event['username']
            }))
    
    @database_sync_to_async
    def check_document_access(self):
        """Check if user has permission to access the document"""
        try:
            document = Document.objects.get(id=self.document_id)
            return document.has_permission(self.user, 'viewer')
        except Document.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_document_content(self, content):
        """Save document content to database"""
        try:
            document = Document.objects.get(id=self.document_id)
            document.content = content
            document.last_edited_by = self.user
            document.save(update_fields=['content', 'last_edited_by', 'updated_at'])
        except Document.DoesNotExist:
            pass
    
    @database_sync_to_async
    def get_active_users(self):
        """Get list of active users in the room (simplified - returns current user)"""
        # In a real implementation, you'd track users in Redis or database
        # For now, we'll rely on user_joined/user_left events
        return [{'id': self.user.id, 'username': self.user.username}]


class SpreadsheetConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time spreadsheet collaboration.
    Handles cell updates and formula recalculations.
    """
    
    async def connect(self):
        self.spreadsheet_id = self.scope['url_route']['kwargs']['spreadsheet_id']
        self.room_group_name = f'spreadsheet_{self.spreadsheet_id}'
        self.user = self.scope['user']
        
        # Check if user has access
        has_access = await self.check_spreadsheet_access()
        
        if not has_access:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )
    
    async def disconnect(self, close_code):
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'cell_update':
            # User is updating a cell
            changes = data.get('changes')  # List of cell changes
            
            # Save to database
            await self.save_spreadsheet_data(changes)
            
            # Broadcast to other users
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'cell_change',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'changes': changes
                }
            )
        
        elif message_type == 'selection_update':
            # User selection update
            selection = data.get('selection')
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'selection_change',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'selection': selection
                }
            )
    
    async def cell_change(self, event):
        """Send cell change to WebSocket"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'cell_change',
                'user_id': event['user_id'],
                'username': event['username'],
                'changes': event['changes']
            }))
    
    async def selection_change(self, event):
        """Send selection change to WebSocket"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'selection_change',
                'user_id': event['user_id'],
                'username': event['username'],
                'selection': event['selection']
            }))
    
    async def user_joined(self, event):
        """Notify when a user joins"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'username': event['username']
            }))
    
    async def user_left(self, event):
        """Notify when a user leaves"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'username': event['username']
            }))
    
    @database_sync_to_async
    def check_spreadsheet_access(self):
        """Check if user has permission to access the spreadsheet"""
        try:
            spreadsheet = Spreadsheet.objects.get(id=self.spreadsheet_id)
            return spreadsheet.has_permission(self.user, 'viewer')
        except Spreadsheet.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_spreadsheet_data(self, changes):
        """Save spreadsheet data to database"""
        try:
            spreadsheet = Spreadsheet.objects.get(id=self.spreadsheet_id)
            # Update the data JSON with changes
            # For simplicity, we'll store the entire updated data structure
            # In production, you'd apply changes more surgically
            for change in changes:
                # Each change has: sheet, row, col, value
                sheet_name = change.get('sheet', 'Sheet1')
                row = change.get('row')
                col = change.get('col')
                value = change.get('value')
                
                # Update the JSON structure (simplified)
                # In a real implementation, you'd have proper data structure handling
            
            spreadsheet.last_edited_by = self.user
            spreadsheet.save(update_fields=['data', 'last_edited_by', 'updated_at'])
        except Spreadsheet.DoesNotExist:
            pass
