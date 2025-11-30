from django.urls import path
from . import api

app_name = 'spreadsheets'

urlpatterns = [
    path('', api.spreadsheet_list, name='list'),
    path('create/', api.spreadsheet_create, name='create'),
    path('<int:id>/', api.spreadsheet_get, name='get'),
    path('<int:id>/update/', api.spreadsheet_update, name='update'),
    path('<int:id>/delete/', api.spreadsheet_delete, name='delete'),
]
