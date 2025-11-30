"""
Comprehensive tests for the accounts app
Tests user registration, login, logout, and profile management
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
import json


class UserModelTests(TestCase):
    """Test User model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation(self):
        """Test that a user can be created"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_str(self):
        """Test user string representation"""
        self.assertEqual(str(self.user), 'testuser')


class UserRegistrationAPITests(TestCase):
    """Test user registration API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
        self.register_url = '/api/accounts/register/'
    
    def test_registration_success(self):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['email'], 'newuser@example.com')
        
        # Verify user was created in database
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_registration_missing_fields(self):
        """Test registration with missing fields"""
        data = {'username': 'newuser'}
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_duplicate_username(self):
        """Test registration with duplicate username"""
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='pass123'
        )
        
        data = {
            'username': 'existing',
            'email': 'new@example.com',
            'password': 'pass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class UserLoginAPITests(TestCase):
    """Test user login API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.login_url = '/api/accounts/login/'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_login_success(self):
        """Test successful login"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_missing_fields(self):
        """Test login with missing fields"""
        data = {'username': 'testuser'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLogoutAPITests(TestCase):
    """Test user logout API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.logout_url = '/api/accounts/logout/'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_logout_success(self):
        """Test successful logout"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.logout_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_logout_unauthenticated(self):
        """Test logout without authentication"""
        response = self.client.post(self.logout_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileAPITests(TestCase):
    """Test user profile API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.profile_url = '/api/accounts/profile/'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_get_profile_authenticated(self):
        """Test getting profile when authenticated"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_get_profile_unauthenticated(self):
        """Test getting profile without authentication"""
        response = self.client.get(self.profile_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
