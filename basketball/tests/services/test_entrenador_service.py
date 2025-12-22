"""Tests del servicio de Entrenador usando mocks."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from basketball.services.entrenador_service import EntrenadorService


class EntrenadorServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = EntrenadorService()
        self.service.dao = MagicMock()
        self.service._call_user_module = MagicMock()
        self.service._fetch_persona = MagicMock(
            return_value={"data": {"first_name": "John"}}
        )

    def test_create_requires_persona(self):
        with self.assertRaises(ValidationError):
            self.service.create_entrenador(
                {}, {"especialidad": "Baloncesto"}, "token"
            )

    def test_create_requires_campos_entrenador(self):
        with self.assertRaises(ValidationError):
            self.service.create_entrenador({"first_name": "A"}, {}, "token")

    def test_create_success(self):
        # Mock save-account response (empty data)
        self.service._call_user_module.side_effect = [
            {"data": {}},  # save-account response
            {"data": {"external": "abc"}},  # search response
        ]
        self.service.dao.exists.return_value = False
        entrenador_obj = SimpleNamespace(
            id=1,
            persona_external="abc",
            especialidad="Baloncesto",
            club_asignado="Club A",
            eliminado=False,
        )
        self.service.dao.create.return_value = entrenador_obj

        result = self.service.create_entrenador(
            {
                "first_name": "A",
                "identification": "123",
                "email": "a@a.com",
                "password": "123",
            },
            {"especialidad": "Baloncesto", "club_asignado": "Club A"},
            "token",
        )

        self.assertEqual(result["entrenador"]["persona_external"], "abc")
        self.service.dao.create.assert_called_with(
            persona_external="abc",
            especialidad="Baloncesto",
            club_asignado="Club A",
            eliminado=False,
        )

    def test_update_not_found(self):
        self.service.dao.get_by_id.return_value = None
        result = self.service.update_entrenador(1, {"external": "x"}, {}, "token")
        self.assertIsNone(result)

    def test_update_success_with_new_external(self):
        entrenador_obj = SimpleNamespace(
            id=1,
            persona_external="old",
            especialidad="Baloncesto",
            club_asignado="Club A",
            eliminado=False,
        )
        # Mock refresh_from_db to update persona_external and especialidad
        def refresh_mock():
            entrenador_obj.persona_external = "new"
            entrenador_obj.especialidad = "Voleibol"
        entrenador_obj.refresh_from_db = refresh_mock
        
        self.service.dao.get_by_id.return_value = entrenador_obj

        # Mock update response (empty) then search response (new external)
        self.service._call_user_module.side_effect = [
            {"data": {}},  # update response
            {"data": {"external": "new"}},  # search response
        ]

        updated_obj = SimpleNamespace(
            id=1,
            persona_external="new",
            especialidad="Voleibol",
            club_asignado="Club A",
            eliminado=False,
        )
        self.service.dao.update.return_value = updated_obj
        self.service.dao.exists.return_value = False

        result = self.service.update_entrenador(
            1,
            {"external": "old", "first_name": "A", "identification": "123"},
            {"especialidad": "Voleibol"},
            "token",
        )

        self.assertEqual(result["entrenador"]["persona_external"], "new")
        self.assertEqual(result["entrenador"]["especialidad"], "Voleibol")

    def test_delete_marks_eliminado(self):
        self.service.dao.update.return_value = True
        self.assertTrue(self.service.delete_entrenador(1))

    def test_get_returns_combined(self):
        entrenador_obj = SimpleNamespace(
            id=1,
            persona_external="abc",
            especialidad="Baloncesto",
            club_asignado="Club A",
            eliminado=False,
        )
        self.service.dao.get_by_id.return_value = entrenador_obj

        data = self.service.get_entrenador(1, "token")

        self.assertEqual(data["entrenador"]["persona_external"], "abc")
        self.service._fetch_persona.assert_called_once()

    def test_list_uses_persona_fetch(self):
        entrenador_obj = SimpleNamespace(
            id=1,
            persona_external="abc",
            especialidad="Baloncesto",
            club_asignado="Club A",
            eliminado=False,
        )
        self.service.dao.get_activos.return_value = [entrenador_obj]

        items = self.service.list_entrenadores("token")

        self.assertEqual(len(items), 1)
        self.service._fetch_persona.assert_called()