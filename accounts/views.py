from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
import json


@api_view(['POST'])
def register(request):
    """User registration API"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return Response({'error': 'Missing fields'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_view(request):
    """User login API"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout_view(request):
    """User logout API"""
    logout(request)
    return Response({'message': 'Logged out successfully'})


@api_view(['GET'])
def profile_view(request):
    """Get user profile"""
    if not request.user.is_authenticated:
        return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email
    })


class UserRegistrationView:
    """Handle user registration"""
    
    @staticmethod
    @csrf_protect
    @require_http_methods(["GET", "POST"])
    def register_old(request):
        """User registration view (legacy)"""
        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            # Validation
            if not all([username, email, password1, password2]):
                messages.error(request, 'All fields are required.')
                return redirect('accounts:register')
            
            if password1 != password2:
                messages.error(request, 'Passwords do not match.')
                return redirect('accounts:register')
            
            if len(password1) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
                return redirect('accounts:register')
            
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('accounts:register')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered.')
                return redirect('accounts:register')
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('accounts:login')
        
        return render(request, 'accounts/register.html')


class UserLoginView:
    """Handle user login"""
    
    @staticmethod
    @csrf_protect
    @require_http_methods(["GET", "POST"])
    def login_view(request):
        """User login view"""
        if request.user.is_authenticated:
            return redirect('dashboard')
        
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
                return redirect('accounts:login')
        
        return render(request, 'accounts/login.html')


@login_required
@require_http_methods(["GET"])
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """User profile view"""
    user = request.user
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        
        # Check if email is already used by another user
        if email != user.email and User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already in use.')
            return redirect('accounts:profile')
        
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')
    
    context = {
        'user': user,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def change_password_view(request):
    """Change password view"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Validate old password
        if not request.user.check_password(old_password):
            messages.error(request, 'Old password is incorrect.')
            return redirect('accounts:change-password')
        
        if new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
            return redirect('accounts:change-password')
        
        if len(new_password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return redirect('accounts:change-password')
        
        request.user.set_password(new_password1)
        request.user.save()
        
        # Re-authenticate the user
        login(request, request.user)
        messages.success(request, 'Password changed successfully.')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/change_password.html')
