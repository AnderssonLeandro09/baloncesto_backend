"""Tests del controlador de EstudianteVinculacion usando mocks."""

from unittest.mock import MagicMock

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from basketball.controllers.estudiante_vinculacion_controller import EstudianteVinculacionController


class EstudianteVinculacionControllerTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EstudianteVinculacionController.as_view(
            {
                'get': 'list',
                'post': 'create',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy',
            }
        )

    def test_list_returns_data(self):
        mock_service = MagicMock()
        mock_service.list_estudiantes.return_value = [{'estudiante': {'id': 1}}]
        self.view.cls.service = mock_service

        request = self.factory.get('/estudiantes-vinculacion/', HTTP_X_ROLE='ADMIN', HTTP_AUTHORIZATION='Bearer t')
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_success(self):
        mock_service = MagicMock()
        mock_service.create_estudiante.return_value = {'estudiante': {'id': 1}}
        self.view.cls.service = mock_service

        request = self.factory.post(
            '/estudiantes-vinculacion/',
            {'persona': {'first_name': 'A'}, 'estudiante': {'carrera': 'Ing', 'semestre': '1'}},
            format='json',
            HTTP_X_ROLE='ADMIN',
            HTTP_AUTHORIZATION='Bearer t',
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('estudiante', response.data)

    def test_create_handles_error(self):
        mock_service = MagicMock()
        mock_service.create_estudiante.side_effect = Exception('bad')
        self.view.cls.service = mock_service

        request = self.factory.post(
            '/estudiantes-vinculacion/',
            {'persona': {}, 'estudiante': {}},
            format='json',
            HTTP_X_ROLE='ADMIN',
            HTTP_AUTHORIZATION='Bearer t',
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_retrieve_not_found(self):
        view = EstudianteVinculacionController.as_view({'get': 'retrieve'})
        mock_service = MagicMock()
        mock_service.get_estudiante.return_value = None
        view.cls.service = mock_service

        request = self.factory.get('/estudiantes-vinculacion/9/', HTTP_X_ROLE='ADMIN', HTTP_AUTHORIZATION='Bearer t')
        response = view(request, pk=9)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_success(self):
        view = EstudianteVinculacionController.as_view({'put': 'update'})
        mock_service = MagicMock()
        mock_service.update_estudiante.return_value = {'estudiante': {'id': 2, 'semestre': '2'}}
        view.cls.service = mock_service

        request = self.factory.put(
            '/estudiantes-vinculacion/2/',
            {'persona': {'external': 'x'}, 'estudiante': {'semestre': '2'}},
            format='json',
            HTTP_X_ROLE='ADMIN',
            HTTP_AUTHORIZATION='Bearer t',
        )
        response = view(request, pk=2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estudiante']['semestre'], '2')

    def test_destroy_success(self):
        view = EstudianteVinculacionController.as_view({'delete': 'destroy'})
        mock_service = MagicMock()
        mock_service.delete_estudiante.return_value = True
        view.cls.service = mock_service

        request = self.factory.delete('/estudiantes-vinculacion/3/', HTTP_X_ROLE='ADMIN', HTTP_AUTHORIZATION='Bearer t')
        response = view(request, pk=3)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
