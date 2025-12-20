"""URLs del módulo Basketball."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .controllers.administrador_controller import AdministradorController
from .controllers.estudiante_vinculacion_controller import EstudianteVinculacionController

app_name = 'basketball'

router = DefaultRouter()
router.register(r'administradores', AdministradorController, basename='administrador')
router.register(r'estudiantes-vinculacion', EstudianteVinculacionController, basename='estudiante_vinculacion')

urlpatterns = [
    path('', include(router.urls)),
]
