"""
URL configuration for docshub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
import os

def serve_react_app(request, *args, **kwargs):
    """Serve React index.html"""
    try:
        index_path = os.path.join(settings.BASE_DIR, 'static', 'dist', 'index.html')
        with open(index_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("React app not built. Run 'npm run build'", status=500)

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # API URLs
    path("api/accounts/", include("accounts.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/spreadsheets/", include("spreadsheets.urls")),
    path("api/notifications/", include("notifications.urls")),
]

# Serve static files
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Catch-all for React routes - must be last
urlpatterns += [
    path("<path:path>", serve_react_app),
    path("", serve_react_app),
]
