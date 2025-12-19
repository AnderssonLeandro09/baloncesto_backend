"""URLs del módulo Basketball."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .controllers.administrador_controller import AdministradorController

app_name = 'basketball'

router = DefaultRouter()
router.register(r'administradores', AdministradorController, basename='administrador')

urlpatterns = [
    path('', include(router.urls)),
]
