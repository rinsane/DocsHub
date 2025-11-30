from django.urls import path
from . import api

app_name = 'documents'

urlpatterns = [
    path('', api.document_list, name='list'),
    path('create/', api.document_create, name='create'),
    path('<int:id>/', api.document_get, name='get'),
    path('<int:id>/update/', api.document_update, name='update'),
    path('<int:id>/delete/', api.document_delete, name='delete'),
    path('<int:id>/permission/add/', api.document_share, name='share'),
    path('<int:id>/remove/', api.document_remove, name='remove'),
]
