"""Pruebas unitarias para ProfileService."""

from unittest.mock import MagicMock
from django.test import SimpleTestCase
from basketball.services.profile_service import ProfileService
from basketball.authentication import AuthenticatedUser


class TestProfileService(SimpleTestCase):
    def setUp(self):
        self.service = ProfileService()
        self.service.admin_service = MagicMock()
        self.service.entrenador_service = MagicMock()
        self.service.estudiante_service = MagicMock()
        
        self.user = AuthenticatedUser(pk="ext-123", role="ADMIN", payload={})
        self.user.email = "admin@test.com"
        self.user.name = "Admin User"
        self.token = "fake-token"

    def test_get_profile_data_admin(self):
        """Test obtener perfil de administrador."""
        self.user.role = "ADMIN"
        mock_admin = MagicMock()
        mock_admin.id = 1
        self.service.admin_service.dao.get_by_persona_external.return_value = mock_admin
        self.service.admin_service.get_administrador_by_id.return_value = {"cargo": "Jefe"}
        
        result = self.service.get_profile_data(self.user, self.token)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["role"], "ADMIN")
        self.assertEqual(result["data"], {"cargo": "Jefe"})
        self.service.admin_service.dao.get_by_persona_external.assert_called_with("ext-123")
