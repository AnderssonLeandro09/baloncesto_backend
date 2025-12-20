"""Tests del servicio de Administrador usando mocks."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from basketball.services.administrador_service import AdministradorService


class AdministradorServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = AdministradorService()
        self.service.dao = MagicMock()
        self.service._call_user_module = MagicMock()
        self.service._fetch_persona = MagicMock(return_value={'data': {'first_name': 'John'}})

    def test_create_requires_persona(self):
        with self.assertRaises(ValidationError):
            self.service.create_administrador({}, {'cargo': 'Admin'}, 'token')

    def test_create_requires_email_password(self):
        # Missing email
        with self.assertRaises(ValidationError):
            self.service.create_administrador(
                {'first_name': 'A', 'password': 'pwd'}, 
                {'cargo': 'Admin'}, 
                'token'
            )
        # Missing password
        with self.assertRaises(ValidationError):
            self.service.create_administrador(
                {'first_name': 'A', 'email': 'a@b.com'}, 
                {'cargo': 'Admin'}, 
                'token'
            )

    def test_create_success(self):
        # Mock save-account response (empty data)
        self.service._call_user_module.side_effect = [
            {'data': {}},  # save-account response
            {'data': {'external': 'abc'}}  # search response
        ]
        self.service.dao.exists.return_value = False
        admin_obj = SimpleNamespace(id=1, persona_external='abc', cargo='Admin', estado=True)
        self.service.dao.create.return_value = admin_obj

        result = self.service.create_administrador(
            {'first_name': 'A', 'identification': '123', 'email': 'test@test.com', 'password': 'pass'}, 
            {'cargo': 'Admin'}, 
            'token'
        )

        self.assertEqual(result['administrador']['persona_external'], 'abc')
        self.service.dao.create.assert_called_with(persona_external='abc', cargo='Admin', estado=True)

    def test_create_recovers_from_duplicate_error(self):
        # Simulate save-account failing with ValidationError
        self.service._call_user_module.side_effect = [
            ValidationError("Duplicate entry"), # save-account fails
            {'data': {'external': 'existing_ext'}} # search succeeds
        ]
        self.service.dao.exists.return_value = False
        admin_obj = SimpleNamespace(id=1, persona_external='existing_ext', cargo='Admin', estado=True)
        self.service.dao.create.return_value = admin_obj

        result = self.service.create_administrador(
            {'first_name': 'A', 'identification': '123', 'email': 'test@test.com', 'password': 'pass'}, 
            {'cargo': 'Admin'}, 
            'token'
        )

        self.assertEqual(result['administrador']['persona_external'], 'existing_ext')
        # Verify search was called
        self.service._call_user_module.assert_any_call('get', '/api/person/search_identification/123', 'token')

    def test_update_not_found(self):
        self.service.dao.get_by_id.return_value = None
        result = self.service.update_administrador(1, {'external': 'x'}, {}, 'token')
        self.assertIsNone(result)

    def test_update_success_with_new_external(self):
        admin_obj = SimpleNamespace(id=1, persona_external='old', cargo='Admin', estado=True)
        self.service.dao.get_by_id.return_value = admin_obj
        
        # Mock update response (empty) then search response (new external)
        self.service._call_user_module.side_effect = [
            {'data': {}}, # update response
            {'data': {'external': 'new'}} # search response
        ]
        
        updated_obj = SimpleNamespace(id=1, persona_external='new', cargo='SuperAdmin', estado=True)
        self.service.dao.update.return_value = updated_obj
        self.service.dao.exists.return_value = False

        result = self.service.update_administrador(1, {'external': 'old', 'first_name': 'A', 'identification': '123'}, {'cargo': 'SuperAdmin'}, 'token')

        self.assertEqual(result['administrador']['persona_external'], 'new')
        self.assertEqual(result['administrador']['cargo'], 'SuperAdmin')

    def test_delete_marks_estado_false(self):
        self.service.dao.update.return_value = True
        self.assertTrue(self.service.delete_administrador(1))
        self.service.dao.update.assert_called_with(1, estado=False)

    def test_get_returns_combined(self):
        admin_obj = SimpleNamespace(id=1, persona_external='abc', cargo='Admin', estado=True)
        self.service.dao.get_by_id.return_value = admin_obj

        data = self.service.get_administrador_by_id(1, 'token')

        self.assertEqual(data['administrador']['persona_external'], 'abc')
        self.service._fetch_persona.assert_called_once()

    def test_list_uses_persona_fetch(self):
        admin_obj = SimpleNamespace(id=1, persona_external='abc', cargo='Admin', estado=True)
        self.service.dao.get_by_filter.return_value = [admin_obj]

        data = self.service.get_all_administradores('token')

        self.assertEqual(len(data), 1)
        self.service._fetch_persona.assert_called_once()
