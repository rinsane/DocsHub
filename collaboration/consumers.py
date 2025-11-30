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
        
        # Check if document exists and user has access
        document = await self.get_document()
        if not document:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current document content to the new user
        await self.send_current_content()
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'username': self.user.username,
                'user_id': self.user.id,
            }
        )
        
        # Send list of active users
        await self.send_active_users()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'username': self.user.username,
                'user_id': self.user.id,
            }
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'content_update':
                # Broadcast IMMEDIATELY to all users - no database save here
                # Database saves are handled by frontend with debouncing
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'content_update',
                        'content': data.get('content', ''),
                        'document_id': self.document_id,
                        'user_id': self.user.id,
                        'username': self.user.username,
                    }
                )
                # No database save here - frontend handles it with debouncing
                
            elif message_type == 'title_update':
                # Broadcast IMMEDIATELY to all users - no database save here
                # Database saves are handled by frontend
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'title_update',
                        'title': data.get('title', ''),
                        'document_id': self.document_id,
                        'user_id': self.user.id,
                        'username': self.user.username,
                    }
                )
                # No database save here - frontend handles it
                
        except json.JSONDecodeError:
            pass
    
    async def content_update(self, event):
        # Don't send back to the sender
        if event.get('user_id') != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'content_update',
                'content': event.get('content', ''),
            }))
    
    async def title_update(self, event):
        # Don't send back to the sender
        if event.get('user_id') != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'title_update',
                'title': event.get('title', ''),
            }))
    
    async def user_joined(self, event):
        # Send to all users except the one who joined
        if event.get('user_id') != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'username': event.get('username', ''),
            }))
    
    async def user_left(self, event):
        # Send to all users except the one who left
        if event.get('user_id') != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'username': event.get('username', ''),
            }))
    
    async def send_current_content(self):
        """Send current document content to the newly connected user"""
        document = await self.get_document()
        if document:
            await self.send(text_data=json.dumps({
                'type': 'content_update',
                'content': document.content or '<p></p>',
            }))
            await self.send(text_data=json.dumps({
                'type': 'title_update',
                'title': document.title or 'Untitled Document',
            }))
    
    async def send_active_users(self):
        """Send list of active users in the room"""
        # Get active users from channel layer (simplified - in production, track this properly)
        await self.send(text_data=json.dumps({
            'type': 'active_users',
            'users': [self.user.username],
        }))
    
    @database_sync_to_async
    def get_document(self):
        """Get document and check permissions"""
        try:
            document = Document.objects.get(id=self.document_id)
            # Check if user has access
            if document.owner == self.user:
                return document
            # Check if user has permission
            from documents.models import DocumentPermission
            if DocumentPermission.objects.filter(document=document, user=self.user).exists():
                return document
            return None
        except Document.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_document_content(self, content):
        """Save document content to database"""
        try:
            document = Document.objects.get(id=self.document_id)
            # Only save if user has edit permission
            if document.owner == self.user:
                document.content = content
                document.save()
            else:
                from documents.models import DocumentPermission
                permission = DocumentPermission.objects.filter(
                    document=document, 
                    user=self.user
                ).first()
                if permission and permission.role in ['owner', 'editor']:
                    document.content = content
                    document.save()
        except Document.DoesNotExist:
            pass
    
    @database_sync_to_async
    def save_document_title(self, title):
        """Save document title to database"""
        try:
            document = Document.objects.get(id=self.document_id)
            # Only save if user has edit permission
            if document.owner == self.user:
                document.title = title
                document.save()
            else:
                from documents.models import DocumentPermission
                permission = DocumentPermission.objects.filter(
                    document=document, 
                    user=self.user
                ).first()
                if permission and permission.role in ['owner', 'editor']:
                    document.title = title
                    document.save()
        except Document.DoesNotExist:
            pass


class SpreadsheetConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time spreadsheet collaboration.
    Handles cell updates and formula recalculations.
    """
    
    async def connect(self):
        self.spreadsheet_id = self.scope['url_route']['kwargs']['spreadsheet_id']
        self.room_group_name = f'spreadsheet_{self.spreadsheet_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if spreadsheet exists and user has access
        spreadsheet = await self.get_spreadsheet()
        if not spreadsheet:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current spreadsheet data to the new user
        await self.send_current_data()
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'username': self.user.username,
                'user_id': self.user.id,
            }
        )
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'username': self.user.username,
                'user_id': self.user.id,
            }
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'cell_update':
                # Broadcast cell update to all users in the room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'cell_change',
                        'changes': data.get('changes', []),
                        'spreadsheet_id': self.spreadsheet_id,
                        'user_id': self.user.id,
                        'username': self.user.username,
                    }
                )
                
                # Save to database
                await self.save_spreadsheet_data(data.get('changes', []))
                
            elif message_type == 'selection_update':
                # Broadcast selection update to all users in the room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'selection_change',
                        'selection': data.get('selection', {}),
                        'user_id': self.user.id,
                        'username': self.user.username,
                    }
                )
                
        except json.JSONDecodeError:
            pass
    
    async def cell_change(self, event):
        # Don't send back to the sender
        if event.get('user_id') != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'cell_change',
                'changes': event.get('changes', []),
            }))
    
    async def selection_change(self, event):
        # Don't send back to the sender
        if event.get('user_id') != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'selection_change',
                'selection': event.get('selection', {}),
            }))
    
    async def user_joined(self, event):
        # Send to all users except the one who joined
        if event.get('user_id') != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'username': event.get('username', ''),
            }))
    
    async def user_left(self, event):
        # Send to all users except the one who left
        if event.get('user_id') != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'username': event.get('username', ''),
            }))
    
    async def send_current_data(self):
        """Send current spreadsheet data to the newly connected user"""
        spreadsheet = await self.get_spreadsheet()
        if spreadsheet:
            await self.send(text_data=json.dumps({
                'type': 'data_update',
                'data': spreadsheet.data or {'sheets': [{'name': 'Sheet1', 'data': [[]]}]},
            }))
    
    @database_sync_to_async
    def get_spreadsheet(self):
        """Get spreadsheet and check permissions"""
        try:
            spreadsheet = Spreadsheet.objects.get(id=self.spreadsheet_id)
            # Check if user has access
            if spreadsheet.owner == self.user:
                return spreadsheet
            # Check if user has permission
            from spreadsheets.models import SpreadsheetPermission
            if SpreadsheetPermission.objects.filter(spreadsheet=spreadsheet, user=self.user).exists():
                return spreadsheet
            return None
        except Spreadsheet.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_spreadsheet_data(self, changes):
        """Save spreadsheet data to database"""
        try:
            spreadsheet = Spreadsheet.objects.get(id=self.spreadsheet_id)
            # Only save if user has edit permission
            if spreadsheet.owner == self.user:
                # Apply changes to spreadsheet data
                # For simplicity, we'll update the entire data structure
                # In production, you'd apply changes more surgically
                if changes:
                    # Update the data JSON with changes
                    # This is a simplified version - in production, handle this more carefully
                    spreadsheet.last_edited_by = self.user
                    spreadsheet.save()
            else:
                from spreadsheets.models import SpreadsheetPermission
                permission = SpreadsheetPermission.objects.filter(
                    spreadsheet=spreadsheet, 
                    user=self.user
                ).first()
                if permission and permission.role in ['owner', 'editor']:
                    spreadsheet.last_edited_by = self.user
                    spreadsheet.save()
        except Spreadsheet.DoesNotExist:
            pass
