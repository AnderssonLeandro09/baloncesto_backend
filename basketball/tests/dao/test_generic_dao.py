"""Tests del DAO Genérico."""

from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from django.db import models
from basketball.dao.generic_dao import GenericDAO


class MockModel(models.Model):
    class Meta:
        app_label = "basketball"


class MockDAO(GenericDAO[MockModel]):
    model = MockModel


class GenericDAOTests(SimpleTestCase):
    def setUp(self):
        self.dao = MockDAO()

    @patch.object(MockModel, "objects")
    def test_get_by_id(self, mock_objects):
        mock_instance = MagicMock()
        mock_objects.get.return_value = mock_instance

        result = self.dao.get_by_id(1)

        mock_objects.get.assert_called_with(pk=1)
        self.assertEqual(result, mock_instance)

    @patch.object(MockModel, "objects")
    def test_get_by_id_not_found(self, mock_objects):
        from django.core.exceptions import ObjectDoesNotExist

        mock_objects.get.side_effect = ObjectDoesNotExist()

        result = self.dao.get_by_id(999)

        self.assertIsNone(result)

    @patch.object(MockModel, "objects")
    def test_get_all(self, mock_objects):
        mock_qs = MagicMock()
        mock_objects.all.return_value = mock_qs

        result = self.dao.get_all()

        self.assertEqual(result, mock_qs)

    @patch.object(MockModel, "objects")
    def test_create(self, mock_objects):
        mock_instance = MagicMock()
        mock_objects.create.return_value = mock_instance

        result = self.dao.create(name="test")

        mock_objects.create.assert_called_with(name="test")
        self.assertEqual(result, mock_instance)
