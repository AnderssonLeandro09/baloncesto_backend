"""Tests del servicio de Administrador con DAO mockeado."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from basketball.services.administrador_service import AdministradorService


class AdministradorServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = AdministradorService()
        self.service.dao = MagicMock()

    def test_create_requires_persona_external(self):
        with self.assertRaises(ValidationError):
            self.service.create_administrador({})

    def test_create_duplicate_raises(self):
        self.service.dao.exists.return_value = True
        with self.assertRaises(ValidationError):
            self.service.create_administrador({'persona_external': 'abc'})

    def test_create_success(self):
        admin_obj = SimpleNamespace(id=1, persona_external='abc')
        self.service.dao.exists.return_value = False
        self.service.dao.create.return_value = admin_obj

        result = self.service.create_administrador({'persona_external': 'abc'})

        self.assertEqual(result, admin_obj)
        self.service.dao.create.assert_called_with(persona_external='abc')

    def test_update_passthrough(self):
        updated = SimpleNamespace(id=1, cargo='Ops')
        self.service.dao.update.return_value = updated
        result = self.service.update_administrador(1, {'cargo': 'Ops'})
        self.assertEqual(result.cargo, 'Ops')

    def test_delete_returns_bool(self):
        self.service.dao.update.return_value = True
        self.assertTrue(self.service.delete_administrador(1))

    def test_getters(self):
        self.service.dao.get_by_id.return_value = 'obj'
        self.service.dao.get_by_filter.return_value = ['a', 'b']
        self.service.dao.get_by_persona_external = MagicMock(return_value='ext')

        self.assertEqual(self.service.get_administrador_by_id(1), 'obj')
        self.assertEqual(len(self.service.get_all_administradores()), 2)
        self.assertEqual(self.service.get_by_persona_external('x'), 'ext')
