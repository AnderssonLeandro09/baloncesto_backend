"""Tests del controlador de Administrador usando mocks."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from basketball.controllers.administrador_controller import AdministradorController


class AdministradorControllerTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = AdministradorController.as_view(
            {
                'get': 'list',
                'post': 'create',
                'put': 'update',
                'delete': 'destroy',
                'patch': 'update',
                'head': 'list',
            }
        )

    def test_list_returns_data(self):
        mock_service = MagicMock()
        mock_service.get_all_administradores.return_value = [SimpleNamespace(id=1, persona_external='abc')]
        self.view.cls.service = mock_service

        request = self.factory.get('/administradores/', HTTP_X_ROLE='ADMIN')
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_success(self):
        mock_admin = SimpleNamespace(id=2, persona_external='def')
        mock_service = MagicMock()
        mock_service.create_administrador.return_value = mock_admin
        self.view.cls.service = mock_service

        request = self.factory.post(
            '/administradores/', {'persona_external': 'def'}, format='json', HTTP_X_ROLE='ADMIN'
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['persona_external'], 'def')

    def test_create_handles_error(self):
        mock_service = MagicMock()
        mock_service.create_administrador.side_effect = Exception('bad')
        self.view.cls.service = mock_service

        request = self.factory.post('/administradores/', {'persona_external': ''}, format='json', HTTP_X_ROLE='ADMIN')
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_retrieve_not_found(self):
        mock_service = MagicMock()
        mock_service.get_administrador_by_id.return_value = None
        view = AdministradorController.as_view({'get': 'retrieve'})
        view.cls.service = mock_service

        request = self.factory.get('/administradores/99/', HTTP_X_ROLE='ADMIN')
        response = view(request, pk=99)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_success(self):
        mock_admin = SimpleNamespace(id=3, persona_external='ghi', cargo='Ops')
        mock_service = MagicMock()
        mock_service.update_administrador.return_value = mock_admin
        view = AdministradorController.as_view({'put': 'update'})
        view.cls.service = mock_service

        request = self.factory.put(
            '/administradores/3/', {'cargo': 'Ops'}, format='json', HTTP_X_ROLE='ADMIN'
        )
        response = view(request, pk=3)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cargo'], 'Ops')

    def test_destroy_success(self):
        mock_service = MagicMock()
        mock_service.delete_administrador.return_value = True
        view = AdministradorController.as_view({'delete': 'destroy'})
        view.cls.service = mock_service

        request = self.factory.delete('/administradores/3/', HTTP_X_ROLE='ADMIN')
        response = view(request, pk=3)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
