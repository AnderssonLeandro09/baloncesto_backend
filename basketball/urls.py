"""URLs del módulo Basketball."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .controllers.administrador_controller import AdministradorController
from .controllers.entrenador_controller import EntrenadorController
from .controllers.estudiante_vinculacion_controller import (
    EstudianteVinculacionController,
)
from .controllers.auth_controller import AuthController

app_name = "basketball"

router = DefaultRouter()
router.register(r"administradores", AdministradorController, basename="administrador")
router.register(r"entrenadores", EntrenadorController, basename="entrenador")
router.register(
    r"estudiantes-vinculacion",
    EstudianteVinculacionController,
    basename="estudiante_vinculacion",
)
# Registramos el AuthController, aunque solo usaremos la acción 'login'
router.register(r"auth", AuthController, basename="auth")

urlpatterns = [
    path("", include(router.urls)),
]
