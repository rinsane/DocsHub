from django.urls import path
from . import api

app_name = 'notifications'

urlpatterns = [
    path('', api.notification_list, name='list'),
    path('unread-count/', api.unread_count, name='unread_count'),
]
