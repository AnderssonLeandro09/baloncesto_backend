"""
URLs del módulo Basketball

Definición de rutas para el módulo.
TODO: Agregar las rutas cuando los controladores estén implementados
"""

from django.urls import path

app_name = 'basketball'

urlpatterns = [
    # TODO: Rutas de Atleta
    # path('atletas/', AtletaController.as_view(), name='atleta-list'),
    # path('atletas/<int:pk>/', AtletaController.as_view(), name='atleta-detail'),
    
    # TODO: Rutas de GrupoAtleta
    # path('grupos/', GrupoAtletaController.as_view(), name='grupo-list'),
    # path('grupos/<int:pk>/', GrupoAtletaController.as_view(), name='grupo-detail'),
    
    # TODO: Rutas de Inscripcion
    # path('inscripciones/', InscripcionController.as_view(), name='inscripcion-list'),
    # path('inscripciones/<int:pk>/', InscripcionController.as_view(), name='inscripcion-detail'),
    
    # TODO: Rutas de PruebaAntropometrica
    # path('pruebas-antropometricas/', PruebaAntropometricaController.as_view(), name='prueba-antropometrica-list'),
    # path('pruebas-antropometricas/<int:pk>/', PruebaAntropometricaController.as_view(), name='prueba-antropometrica-detail'),
    
    # TODO: Rutas de PruebaFisica
    # path('pruebas-fisicas/', PruebaFisicaController.as_view(), name='prueba-fisica-list'),
    # path('pruebas-fisicas/<int:pk>/', PruebaFisicaController.as_view(), name='prueba-fisica-detail'),
    
    # TODO: Rutas de Entrenador
    # path('entrenadores/', EntrenadorController.as_view(), name='entrenador-list'),
    # path('entrenadores/<int:pk>/', EntrenadorController.as_view(), name='entrenador-detail'),
    
    # TODO: Rutas de EstudianteVinculacion
    # path('estudiantes/', EstudianteVinculacionController.as_view(), name='estudiante-list'),
    # path('estudiantes/<int:pk>/', EstudianteVinculacionController.as_view(), name='estudiante-detail'),
]
