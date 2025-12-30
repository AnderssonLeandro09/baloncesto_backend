"""URLs del módulo Basketball."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .controllers.administrador_controller import AdministradorController
from .controllers.estudiante_vinculacion_controller import (
    EstudianteVinculacionController,
)
from .controllers.entrenador_controller import EntrenadorController
from .controllers.auth_controller import AuthController
from .controllers.inscripcion_controller import InscripcionController
from .controllers.prueba_fisica_controller import PruebaFisicaController
from .controllers.profile_controller import ProfileController

app_name = "basketball"

router = DefaultRouter()
router.register(r"administradores", AdministradorController, basename="administrador")
router.register(
    r"estudiantes-vinculacion",
    EstudianteVinculacionController,
    basename="estudiante_vinculacion",
)
router.register(r"entrenadores", EntrenadorController, basename="entrenador")
# Registramos el AuthController, aunque solo usaremos la acción 'login'
router.register(r"auth", AuthController, basename="auth")
router.register(r"inscripciones", InscripcionController, basename="inscripcion")
router.register(r"pruebas-fisicas", PruebaFisicaController, basename="prueba_fisica")
router.register(r"profile", ProfileController, basename="profile")

urlpatterns = [
    path("", include(router.urls)),
]
