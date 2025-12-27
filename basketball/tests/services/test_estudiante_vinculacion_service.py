"""Tests del servicio de EstudianteVinculacion usando mocks."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from basketball.services.estudiante_vinculacion_service import (
    EstudianteVinculacionService,
)


class EstudianteVinculacionServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = EstudianteVinculacionService()
        self.service.dao = MagicMock()
        self.service._call_user_module = MagicMock()
        self.service._fetch_persona = MagicMock(
            return_value={"data": {"first_name": "John"}}
        )

    def test_create_requires_persona(self):
        with self.assertRaises(ValidationError):
            self.service.create_estudiante(
                {}, {"carrera": "Ing", "semestre": "1"}, "token"
            )

    def test_create_requires_campos_estudiante(self):
        with self.assertRaises(ValidationError):
            self.service.create_estudiante({"first_name": "A"}, {}, "token")

    def test_create_invalid_email(self):
        with self.assertRaises(ValidationError) as cm:
            self.service.create_estudiante(
                {
                    "first_name": "A",
                    "identification": "123",
                    "email": "test@gmail.com",
                    "password": "123",
                },
                {"carrera": "Ing", "semestre": "1"},
                "token",
            )
        self.assertIn("institucional", str(cm.exception))

    def test_create_success(self):
        # Mock save-account response (empty data)
        self.service._call_user_module.side_effect = [
            {"data": {}},  # save-account response
            {"data": {"external": "abc"}},  # search response
        ]
        self.service.dao.exists.return_value = False
        estudiante_obj = SimpleNamespace(
            id=1,
            persona_external="abc",
            carrera="Ing",
            semestre="1",
            eliminado=False,
        )
        self.service.dao.create.return_value = estudiante_obj

        result = self.service.create_estudiante(
            {
                "first_name": "A",
                "identification": "123",
                "email": "a@unl.edu.ec",
                "password": "123",
            },
            {"carrera": "Ing", "semestre": "1"},
            "token",
        )

        self.assertEqual(result["estudiante"]["persona_external"], "abc")
        self.service.dao.create.assert_called_with(
            persona_external="abc",
            carrera="Ing",
            semestre="1",
            eliminado=False,
        )

    def test_update_not_found(self):
        self.service.dao.get_by_id.return_value = None
        result = self.service.update_estudiante(1, {"external": "x"}, {}, "token")
        self.assertIsNone(result)

    def test_update_success_with_new_external(self):
        estudiante_obj = SimpleNamespace(
            id=1,
            persona_external="old",
            carrera="Ing",
            semestre="1",
            eliminado=False,
        )
        self.service.dao.get_by_id.return_value = estudiante_obj

        # Mock update response (empty) then search response (new external)
        self.service._call_user_module.side_effect = [
            {"data": {}},  # update response
            {"data": {"external": "new"}},  # search response
        ]

        updated_obj = SimpleNamespace(
            id=1,
            persona_external="new",
            carrera="Ing",
            semestre="2",
            eliminado=False,
        )
        self.service.dao.update.return_value = updated_obj
        self.service.dao.exists.return_value = False

        result = self.service.update_estudiante(
            1,
            {"external": "old", "first_name": "A", "identification": "123"},
            {"semestre": "2"},
            "token",
        )

        self.assertEqual(result["estudiante"]["persona_external"], "new")
        self.assertEqual(result["estudiante"]["semestre"], "2")

    def test_delete_marks_eliminado(self):
        self.service.dao.update.return_value = True
        self.assertTrue(self.service.delete_estudiante(1))

    def test_get_returns_combined(self):
        estudiante_obj = SimpleNamespace(
            id=1,
            persona_external="abc",
            carrera="Ing",
            semestre="1",
            eliminado=False,
        )
        self.service.dao.get_by_id.return_value = estudiante_obj

        data = self.service.get_estudiante(1, "token")

        self.assertEqual(data["estudiante"]["persona_external"], "abc")
        self.service._fetch_persona.assert_called_once()

    def test_list_uses_persona_fetch(self):
        estudiante_obj = SimpleNamespace(
            id=1,
            persona_external="abc",
            carrera="Ing",
            semestre="1",
            eliminado=False,
        )
        self.service.dao.get_by_filter.return_value = [estudiante_obj]

        items = self.service.list_estudiantes("token")

        self.assertEqual(len(items), 1)
        self.service._fetch_persona.assert_called()
