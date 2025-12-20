"""Tests del controlador de Administrador usando mocks."""

import jwt
from unittest.mock import MagicMock

from django.core.exceptions import ValidationError
from django.conf import settings
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from basketball.controllers.administrador_controller import AdministradorController


class AdministradorControllerTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        # Configurar la vista para las acciones estándar
        self.view_list_create = AdministradorController.as_view({
            'get': 'list',
            'post': 'create'
        })
        self.view_detail = AdministradorController.as_view({
            'get': 'retrieve',
            'put': 'update',
            'delete': 'destroy'
        })
        self.token = self._get_token('ADMIN')

    def _get_token(self, role):
        payload = {'sub': '123', 'role': role, 'email': 'test@test.com', 'name': 'Test User'}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    def test_list_returns_data(self):
        mock_service = MagicMock()
        # El servicio ahora retorna una lista de diccionarios
        mock_service.get_all_administradores.return_value = [
            {'administrador': {'id': 1}, 'persona': {'name': 'John'}}
        ]
        # Asignar el mock a la clase del controlador (o instancia si fuera posible, pero viewsets son complejos)
        # Al ser ViewSet, 'self.view.cls' accede a la clase.
        # NOTA: Esto afecta a todos los tests si no se restaura, pero al ser SimpleTestCase y re-crear mocks...
        # Mejor asignar a la instancia si pudiéramos, pero DRF instancia por request.
        # Monkey-patching la clase es lo más directo aquí.
        original_service = AdministradorController.service
        AdministradorController.service = mock_service
        
        try:
            request = self.factory.get('/administradores/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
            response = self.view_list_create(request)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 1)
            # El servicio recibe el token tal cual
            mock_service.get_all_administradores.assert_called_with(f'Bearer {self.token}')
        finally:
            AdministradorController.service = original_service

    def test_create_success(self):
        mock_service = MagicMock()
        expected_response = {'administrador': {'id': 2}, 'persona': {'name': 'Jane'}}
        mock_service.create_administrador.return_value = expected_response
        
        original_service = AdministradorController.service
        AdministradorController.service = mock_service

        payload = {
            'persona': {'first_name': 'Jane', 'email': 'j@j.com'},
            'administrador': {'cargo': 'Admin'}
        }

        try:
            request = self.factory.post(
                '/administradores/', 
                payload, 
                format='json', 
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
            response = self.view_list_create(request)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data, expected_response)
            mock_service.create_administrador.assert_called_with(
                payload['persona'], 
                payload['administrador'], 
                f'Bearer {self.token}'
            )
        finally:
            AdministradorController.service = original_service

    def test_create_handles_error(self):
        mock_service = MagicMock()
        mock_service.create_administrador.side_effect = ValidationError('bad')
        
        original_service = AdministradorController.service
        AdministradorController.service = mock_service

        try:
            request = self.factory.post(
                '/administradores/', 
                {}, 
                format='json', 
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
            response = self.view_list_create(request)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)
        finally:
            AdministradorController.service = original_service

    def test_retrieve_not_found(self):
        mock_service = MagicMock()
        mock_service.get_administrador_by_id.return_value = None
        
        original_service = AdministradorController.service
        AdministradorController.service = mock_service

        try:
            request = self.factory.get('/administradores/99/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
            response = self.view_detail(request, pk=99)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            mock_service.get_administrador_by_id.assert_called_with(99, f'Bearer {self.token}')
        finally:
            AdministradorController.service = original_service

    def test_update_success(self):
        mock_service = MagicMock()
        expected_response = {'administrador': {'id': 3, 'cargo': 'Ops'}, 'persona': {'name': 'Jim'}}
        mock_service.update_administrador.return_value = expected_response
        
        original_service = AdministradorController.service
        AdministradorController.service = mock_service

        payload = {
            'persona': {'first_name': 'Jim'},
            'administrador': {'cargo': 'Ops'}
        }

        try:
            request = self.factory.put(
                '/administradores/3/', 
                payload, 
                format='json', 
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
            response = self.view_detail(request, pk=3)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, expected_response)
            mock_service.update_administrador.assert_called_with(
                3, 
                payload['persona'], 
                payload['administrador'], 
                f'Bearer {self.token}'
            )
        finally:
            AdministradorController.service = original_service

    def test_destroy_success(self):
        mock_service = MagicMock()
        mock_service.delete_administrador.return_value = True
        
        original_service = AdministradorController.service
        AdministradorController.service = mock_service

        try:
            request = self.factory.delete('/administradores/3/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
            response = self.view_detail(request, pk=3)

            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            mock_service.delete_administrador.assert_called_with(3)
        finally:
            AdministradorController.service = original_service
