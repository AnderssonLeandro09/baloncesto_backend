"""
URL configuration for basketball_project project.

URLs del proyecto Basketball
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # URLs del módulo Basketball
    path('api/basketball/', include('basketball.urls', namespace='basketball')),
]
