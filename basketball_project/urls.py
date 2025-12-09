"""
URL configuration for basketball_project project.

URLs del proyecto Basketball
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)
from basketball.auth.jwt_serializers import CustomTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ==========================================================================
    # JWT Authentication Endpoints
    # ==========================================================================
    # POST /api/auth/token/ - Obtener access y refresh tokens (login)
    path('api/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # POST /api/auth/token/refresh/ - Refrescar access token usando refresh token
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # POST /api/auth/token/verify/ - Verificar si un token es válido
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # POST /api/auth/token/blacklist/ - Invalidar refresh token (logout)
    path('api/auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    
    # URLs del módulo Basketball
    path('api/basketball/', include('basketball.urls', namespace='basketball')),
    
    # Documentación API (Swagger/OpenAPI)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
