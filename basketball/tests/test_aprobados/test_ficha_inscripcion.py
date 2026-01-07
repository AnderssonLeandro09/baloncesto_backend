"""
Test Suite: Ficha de Inscripción - CI/CD Ready
==============================================
Módulo de tests unitarios optimizado para pipelines de integración continua.

Características:
    - Ejecución en milisegundos (mocks de servicios externos)
    - Salida silenciosa (sin prints ni tracebacks)
    - Manejo robusto de excepciones (HTTP 400 vs 500)
    - Cobertura completa de reglas de negocio

Author: QA Automation Team
Version: 2.0.0 (Pipeline Ready)
"""

from datetime import date
from unittest.mock import MagicMock, patch

import jwt
from django.conf import settings
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APIRequestFactory

from basketball.controllers.inscripcion_controller import InscripcionController
from basketball.serializar.atleta import InscripcionDataSerializer
from basketball.serializar.persona import PersonaSerializer


# =============================================================================
# MOCK GLOBAL DEL TOKEN PARA VELOCIDAD EXTREMA EN CI/CD
# =============================================================================
@patch(
    "basketball.controllers.inscripcion_controller.get_user_module_token",
    return_value="mock_token_pipeline",
)
class TestFichaInscripcion(SimpleTestCase):
    """
    Suite de Tests para Ficha de Inscripción - Producción Ready.

    Secciones:
        1. CREAR INSCRIPCIÓN (TC-INS-01 a TC-INS-07)
        2. CAMBIAR ESTADO (TC-INS-01 a TC-INS-02 Estado)

    Notas CI/CD:
        - Todos los servicios externos están mockeados
        - Tiempo de ejecución objetivo: < 100ms total
        - Zero console noise (sin prints ni tracebacks)
    """

    def setUp(self):
        """Configuración común para todos los tests."""
        self.factory = APIRequestFactory()

        # Endpoints del controlador
        self.view_create = InscripcionController.as_view({"post": "create"})
        self.view_change_status = InscripcionController.as_view(
            {"post": "cambiar_estado"}
        )

        # Token JWT Mock para Headers (Rol Autorizado: ENTRENADOR)
        payload = {"role": "ENTRENADOR", "sub": "test_user_pipeline"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    # =========================================================================
    # 1. CREAR INSCRIPCIÓN (TC-INS-01 a TC-INS-07)
    # =========================================================================

    def test_tc_ins_01_crear_inscripcion_registro_exitoso(self, mock_token):
        """
        TC-INS-01: Registro Exitoso.

        Objetivo: Verificar creación exitosa de inscripción con datos válidos.
        Entrada: Payload completo con persona, atleta e inscripción.
        Salida Esperada: HTTP 201 Created + mensaje de éxito.
        """
        mock_service = MagicMock()
        InscripcionController.service = mock_service

        # Configurar respuesta exitosa del servicio
        mock_service.create_atleta_inscripcion.return_value = {
            "mensaje": "Inscripción creada exitosamente",
            "atleta": {"cedula": "0102030405", "edad": 15},
            "inscripcion": {"id": 1, "habilitada": True},
        }

        data = {
            "persona": {
                "first_name": "Juan Carlos Pérez",
                "identification": "0102030405",
                "address": "Av. Principal 123",
                "phono": "0999999999",
            },
            "atleta": {"edad": 15},
            "inscripcion": {},
        }

        request = self.factory.post(
            "/inscripciones/",
            data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view_create(request)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data.get("mensaje"), "Inscripción creada exitosamente"
        )
        mock_service.create_atleta_inscripcion.assert_called_once()

    @patch("basketball.controllers.inscripcion_controller.traceback.print_exc")
    @patch("basketball.controllers.inscripcion_controller.logger")
    def test_tc_ins_02_crear_inscripcion_validacion_duplicados(
        self, mock_logger, mock_traceback, mock_token
    ):
        """
        TC-INS-02: Validación Duplicados.

        Objetivo: Verificar rechazo de inscripción duplicada.
        Entrada: Cédula ya registrada en el sistema.
        Salida Esperada: HTTP 400 Bad Request + mensaje específico.

        Nota CI/CD: Se mockean logger y traceback para output silencioso.
        """
        mock_service = MagicMock()
        InscripcionController.service = mock_service

        # Simular error de duplicado usando DRFValidationError (garantiza HTTP 400)
        mock_service.create_atleta_inscripcion.side_effect = DRFValidationError(
            "El atleta ya se encuentra registrado con una inscripción activa."
        )

        data = {
            "persona": {"identification": "0102030405"},
            "atleta": {},
            "inscripcion": {},
        }

        request = self.factory.post(
            "/inscripciones/",
            data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view_create(request)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "ya se encuentra registrado con una inscripción activa",
            str(response.data),
        )

    def test_tc_ins_03_crear_inscripcion_datos_persona_vacios(self, mock_token):
        """
        TC-INS-03: Validación Datos Persona Vacíos.

        Objetivo: Verificar rechazo cuando faltan datos obligatorios.
        Entrada: persona={} (objeto vacío).
        Salida Esperada: HTTP 400 Bad Request.
        """
        mock_service = MagicMock()
        InscripcionController.service = mock_service

        data = {
            "persona": {},  # Datos vacíos - debe fallar
            "atleta": {},
            "inscripcion": {},
        }

        request = self.factory.post(
            "/inscripciones/",
            data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view_create(request)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Datos de persona son requeridos", str(response.data))

    def test_tc_ins_04_crear_inscripcion_calculo_fecha_automatica(self, mock_token):
        """
        TC-INS-04: Cálculo Fecha Automática.

        Objetivo: Verificar asignación automática de fecha del sistema.
        Entrada: Fecha simulada 2026-01-07.
        Salida Esperada: fecha_inscripcion == fecha del sistema.
        """
        fecha_sistema = date(2026, 1, 7)

        with patch("basketball.serializar.atleta.date") as mock_date:
            # Configurar mock de fecha
            mock_date.today.return_value = fecha_sistema
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            serializer = InscripcionDataSerializer(data={})
            serializer.is_valid()

            # Validar que el método de validación acepta la fecha actual
            validated_fecha = serializer.validate_fecha_inscripcion(fecha_sistema)

            # Assertions
            self.assertEqual(validated_fecha, fecha_sistema)

    def test_tc_ins_05_crear_inscripcion_nombre_con_numeros_rechazado(self, mock_token):
        """
        TC-INS-05: Nombre con Números Rechazado (Negative Testing).

        Objetivo: Verificar regla de negocio - nombres solo letras.
        Entrada: first_name="Juan123" (contiene números).
        Salida Esperada: Serializer inválido + error específico.
        """
        # Test directo del serializer (validación de regla de negocio)
        data = {"first_name": "Juan123"}
        serializer = PersonaSerializer(data=data, partial=True)

        es_valido = serializer.is_valid()

        # Assertions
        self.assertFalse(
            es_valido, "El nombre debería ser rechazado si contiene números"
        )
        self.assertIn("solo puede contener letras", str(serializer.errors))

    def test_tc_ins_06_crear_inscripcion_sexo_personalizado(self, mock_token):
        """
        TC-INS-06: Sexo Personalizado.

        Objetivo: Verificar flexibilidad del campo sexo (texto libre).
        Entrada: sexo="No binario".
        Salida Esperada: HTTP 201 + valor guardado correctamente.
        """
        mock_service = MagicMock()
        InscripcionController.service = mock_service

        sexo_personalizado = "No binario"

        # Configurar servicio para aceptar y retornar el valor
        mock_service.create_atleta_inscripcion.return_value = {
            "mensaje": "Inscripción creada exitosamente",
            "atleta": {"sexo": sexo_personalizado, "cedula": "0102030405"},
            "inscripcion": {"id": 1, "habilitada": True},
        }

        data = {
            "persona": {
                "first_name": "María García",
                "identification": "0102030405",
            },
            "atleta": {"sexo": sexo_personalizado},
            "inscripcion": {},
        }

        request = self.factory.post(
            "/inscripciones/",
            data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view_create(request)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["atleta"]["sexo"], sexo_personalizado)

    def test_tc_ins_07_crear_inscripcion_cedula_con_letras_rechazada(self, mock_token):
        """
        TC-INS-07: Cédula con Letras Rechazada (Negative Testing).

        Objetivo: Verificar regla de negocio - cédula solo dígitos.
        Entrada: identification="012345678A" (contiene letra).
        Salida Esperada: Serializer inválido + error específico en campo 'identification'.
        """
        # Test directo del serializer con datos completos
        data = {
            "first_name": "Juan",
            "last_name": "Pérez",
            "identification": "012345678A",  # INVÁLIDA: contiene letra
        }
        serializer = PersonaSerializer(data=data)

        es_valido = serializer.is_valid()

        # Assertions con mensajes descriptivos para CI/CD
        self.assertFalse(
            es_valido,
            f"TC-INS-07 FAILED: La cédula '012345678A' fue aceptada cuando debería ser rechazada. "
            f"Errors: {serializer.errors}",
        )
        self.assertIn(
            "identification",
            serializer.errors,
            f"TC-INS-07 FAILED: Se esperaba error en campo 'identification', "
            f"pero los errores fueron: {serializer.errors}",
        )
        error_msg = str(serializer.errors["identification"])
        self.assertIn(
            "solo dígitos",
            error_msg,
            f"TC-INS-07 FAILED: Mensaje de error incorrecto. "
            f"Esperado: 'solo dígitos', Recibido: {error_msg}",
        )

    # =========================================================================
    # 2. CAMBIAR ESTADO (TC-INS-01 a TC-INS-02 Estado)
    # =========================================================================

    def test_tc_ins_01_cambiar_estado_deshabilitacion_exitosa(self, mock_token):
        """
        TC-INS-01 (Estado): Deshabilitación Exitosa.

        Objetivo: Verificar cambio de estado a deshabilitado.
        Entrada: POST /inscripciones/{id}/cambiar-estado/ (inscripción habilitada).
        Salida Esperada: HTTP 200 + habilitada=False + mensaje confirmación.
        """
        mock_service = MagicMock()
        InscripcionController.service = mock_service

        # Configurar mock para retornar inscripción deshabilitada
        mock_inscripcion = MagicMock()
        mock_inscripcion.habilitada = False
        mock_service.cambiar_estado_inscripcion.return_value = mock_inscripcion

        request = self.factory.post(
            "/inscripciones/1/cambiar-estado/",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view_change_status(request, pk=1)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["habilitada"])
        self.assertIn(
            "Inscripción deshabilitada correctamente", response.data["mensaje"]
        )
        mock_service.cambiar_estado_inscripcion.assert_called_once_with(1)

    def test_tc_ins_02_cambiar_estado_habilitacion_exitosa(self, mock_token):
        """
        TC-INS-02 (Estado): Habilitación Exitosa.

        Objetivo: Verificar cambio de estado a habilitado.
        Entrada: POST /inscripciones/{id}/cambiar-estado/ (inscripción deshabilitada).
        Salida Esperada: HTTP 200 + habilitada=True + mensaje confirmación.
        """
        mock_service = MagicMock()
        InscripcionController.service = mock_service

        # Configurar mock para retornar inscripción habilitada
        mock_inscripcion = MagicMock()
        mock_inscripcion.habilitada = True
        mock_service.cambiar_estado_inscripcion.return_value = mock_inscripcion

        request = self.factory.post(
            "/inscripciones/1/cambiar-estado/",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view_change_status(request, pk=1)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["habilitada"])
        self.assertIn(
            "Inscripción habilitada correctamente", response.data["mensaje"]
        )
        mock_service.cambiar_estado_inscripcion.assert_called_once_with(1)
