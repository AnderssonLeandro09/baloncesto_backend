# Guía: Cómo Agregar Nuevos Módulos al Proyecto

## 📋 Resumen Rápido

Para agregar un nuevo CRUD (ej: Atleta), necesitas:
1. **DAO** - Acceso a datos
2. **Service** - Lógica de negocio
3. **Controller** - API HTTP
4. **URL Routes** - Registrar endpoints
5. **Tests** - Validar funcionamiento

---

## 1️⃣ Crear el DAO (Capa de Datos)

### Ubicación: `basketball/dao/model_daos.py`

### Plantilla:

```python
class AtletaDAO(GenericDAO[Atleta]):
    """
    DAO específico para el modelo Atleta.
    Proporciona operaciones CRUD y métodos auxiliares específicos para atletas.
    """

    model = Atleta

    def get_by_dni(self, dni: str) -> Optional[Atleta]:
        """Obtiene un atleta por DNI."""
        return self.get_first(dni=dni)

    def get_activos(self) -> QuerySet[Atleta]:
        """Obtiene todos los atletas activos."""
        return self.get_by_filter(estado=True)

    def get_by_grupo(self, grupo_id: int) -> QuerySet[Atleta]:
        """Obtiene atletas por grupo."""
        return self.get_by_filter(grupos__id=grupo_id, estado=True)

    def search_atletas(self, search_term: str) -> QuerySet[Atleta]:
        """Busca atletas por nombre, apellido, email o DNI."""
        return self.search(
            search_fields=['nombre', 'apellido', 'email', 'dni'],
            search_term=search_term
        ).filter(estado=True)
```

### Métodos Heredados de GenericDAO:

```python
# CRUD Básico
self.get_by_id(pk)
self.create(**kwargs)
self.update(pk, **kwargs)
self.soft_delete(pk)  # Cambia estado a False

# Lectura
self.get_all()
self.get_by_filter(**kwargs)
self.get_first(**kwargs)

# Búsqueda
self.search(search_fields=['nombre', 'apellido'], search_term='Juan')
```

---

## 2️⃣ Crear el Service (Lógica de Negocio)

### Ubicación: `basketball/services/atleta_service.py`

### Plantilla:

```python
from typing import Dict, Any, Optional, List
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from basketball.services.base_service import BaseService, ServiceResult
from basketball.dao.model_daos import AtletaDAO
from basketball.models import Atleta


class AtletaService(BaseService[Atleta]):
    """
    Servicio para gestionar atletas.
    Implementa la lógica de negocio, validaciones y manejo de errores.
    """

    REQUIRED_FIELDS = ['nombre', 'apellido', 'email', 'dni', 'clave', 'sexo']

    def __init__(self):
        self.dao = AtletaDAO()

    def _validate_dni(self, dni: str) -> Optional[str]:
        """Valida que el DNI tenga 10 dígitos."""
        if not dni:
            return "El DNI es obligatorio"
        if len(dni) != 10 or not dni.isdigit():
            return "El DNI debe tener 10 dígitos numéricos"
        return None

    def crear_atleta(self, data: Dict[str, Any]) -> ServiceResult:
        """Crea un nuevo atleta con validaciones."""
        errors: List[str] = []

        # Validar campos requeridos
        required_errors = self.validate_required_fields(data, self.REQUIRED_FIELDS)
        errors.extend(required_errors)
        if errors:
            return ServiceResult.validation_error("Error de validación", errors)

        # Validar DNI
        dni = data.get('dni', '').strip()
        dni_err = self._validate_dni(dni)
        if dni_err:
            errors.append(dni_err)

        if errors:
            return ServiceResult.validation_error("Error de validación", errors)

        # Verificar unicidad
        if self.dao.get_by_dni(dni):
            return ServiceResult.conflict("El DNI ya está registrado")

        try:
            atleta = self.dao.create(
                nombre=data.get('nombre').strip(),
                apellido=data.get('apellido').strip(),
                email=data.get('email').lower().strip(),
                dni=dni,
                clave=data.get('clave'),
                sexo=data.get('sexo'),
                rol='ATLETA',
            )
            return ServiceResult.success(
                data=self._atleta_to_dict(atleta),
                message="Atleta creado exitosamente"
            )
        except Exception as e:
            return ServiceResult.error("Error inesperado al crear atleta", [str(e)])

    def obtener_atleta(self, pk: int) -> ServiceResult:
        """Obtiene los detalles de un atleta."""
        atleta = self.dao.get_by_id(pk)
        if not atleta:
            return ServiceResult.not_found("Atleta no encontrado")
        return ServiceResult.success(
            data=self._atleta_to_dict(atleta),
            message="Atleta encontrado"
        )

    def listar_atletas(self, solo_activos: bool = True) -> ServiceResult:
        """Lista todos los atletas."""
        if solo_activos:
            atletas = self.dao.get_activos()
        else:
            atletas = self.dao.get_all()

        data = [self._atleta_to_dict(a) for a in atletas]
        return ServiceResult.success(
            data=data,
            message=f"Se encontraron {len(data)} atletas"
        )

    def actualizar_atleta(self, pk: int, data: Dict[str, Any]) -> ServiceResult:
        """Actualiza un atleta existente."""
        atleta = self.dao.get_by_id(pk)
        if not atleta:
            return ServiceResult.not_found("Atleta no encontrado")

        update_data: Dict[str, Any] = {}

        # Solo actualizar campos permitidos
        ALLOWED_FIELDS = ['nombre', 'apellido', 'email', 'sexo']
        for field in ALLOWED_FIELDS:
            if field in data:
                update_data[field] = data[field]

        try:
            actualizado = self.dao.update(pk, **update_data)
            if not actualizado:
                return ServiceResult.not_found("Atleta no encontrado para actualizar")
            return ServiceResult.success(
                data=self._atleta_to_dict(actualizado),
                message="Atleta actualizado"
            )
        except Exception as e:
            return ServiceResult.error("Error inesperado al actualizar atleta", [str(e)])

    def dar_de_baja(self, pk: int) -> ServiceResult:
        """Da de baja un atleta (soft delete)."""
        atleta = self.dao.get_by_id(pk)
        if not atleta:
            return ServiceResult.not_found("Atleta no encontrado")
        if not atleta.estado:
            return ServiceResult.conflict("El atleta ya está dado de baja")

        success = self.dao.soft_delete(pk, field='estado')
        if success:
            return ServiceResult.success(message="Atleta dado de baja")
        return ServiceResult.error("No se pudo dar de baja al atleta")

    def reactivar_atleta(self, pk: int) -> ServiceResult:
        """Reactiva un atleta dado de baja."""
        atleta = self.dao.get_by_id(pk)
        if not atleta:
            return ServiceResult.not_found("Atleta no encontrado")
        if atleta.estado:
            return ServiceResult.conflict("El atleta ya está activo")

        try:
            actualizado = self.dao.update(pk, estado=True)
            if actualizado:
                return ServiceResult.success(message="Atleta reactivado")
            return ServiceResult.error("No se pudo reactivar el atleta")
        except Exception as e:
            return ServiceResult.error("Error inesperado al reactivar atleta", [str(e)])

    def _atleta_to_dict(self, atleta: Atleta) -> Dict[str, Any]:
        """Convierte un atleta a diccionario."""
        return {
            'id': atleta.pk,
            'nombre': atleta.nombre,
            'apellido': atleta.apellido,
            'email': atleta.email,
            'dni': atleta.dni,
            'sexo': getattr(atleta, 'sexo', None),
            'foto_perfil': atleta.foto_perfil,
            'rol': getattr(atleta, 'rol', 'ATLETA'),
            'estado': atleta.estado,
            'fecha_registro': atleta.fecha_registro.isoformat() if atleta.fecha_registro else None,
        }
```

---

## 3️⃣ Crear el Controller (API HTTP)

### Ubicación: `basketball/controllers/atleta_controller.py`

### Plantilla:

```python
from rest_framework.response import Response
from rest_framework import status, serializers, permissions
from drf_spectacular.utils import extend_schema

from basketball.controllers.base_controller import BaseController
from basketball.services.atleta_service import AtletaService
from basketball.services.base_service import ResultStatus


class AtletaInputSerializer(serializers.Serializer):
    """Serializer para crear atleta."""
    nombre = serializers.CharField(max_length=100)
    apellido = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    dni = serializers.CharField(max_length=10)
    clave = serializers.CharField(max_length=255)
    sexo = serializers.CharField(max_length=1)
    foto_perfil = serializers.CharField(max_length=255, required=False, allow_null=True)


class AtletaUpdateSerializer(serializers.Serializer):
    """Serializer para actualizar atleta."""
    nombre = serializers.CharField(max_length=100, required=False)
    apellido = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)
    sexo = serializers.CharField(max_length=1, required=False)
    foto_perfil = serializers.CharField(max_length=255, required=False, allow_null=True)


class AtletaOutputSerializer(serializers.Serializer):
    """Serializer para respuesta de atleta."""
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    email = serializers.EmailField()
    dni = serializers.CharField()
    sexo = serializers.CharField()
    foto_perfil = serializers.CharField(allow_null=True)
    rol = serializers.CharField()
    estado = serializers.BooleanField()
    fecha_registro = serializers.CharField(allow_null=True)


class AtletaListController(BaseController):
    """Controlador para listar y crear atletas."""
    permission_classes = [permissions.AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = AtletaService()

    @extend_schema(
        tags=['Atletas'],
        summary='Listar atletas',
        responses={200: AtletaOutputSerializer(many=True)}
    )
    def get(self, request):
        """Lista todos los atletas."""
        solo_activos = request.query_params.get('solo_activos', 'true').lower() == 'true'
        result = self.service.listar_atletas(solo_activos=solo_activos)
        return Response(result.to_dict(), status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Atletas'],
        summary='Crear atleta',
        request=AtletaInputSerializer,
        responses={201: AtletaOutputSerializer, 400: serializers.Serializer}
    )
    def post(self, request):
        """Crea un nuevo atleta."""
        serializer = AtletaInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'status': 'validation_error', 'errors': list(serializer.errors.values())},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = self.service.crear_atleta(serializer.validated_data)
        if result.is_success:
            return Response(result.to_dict(), status=status.HTTP_201_CREATED)
        if result.status == ResultStatus.VALIDATION_ERROR:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        if result.status == ResultStatus.CONFLICT:
            return Response(result.to_dict(), status=status.HTTP_409_CONFLICT)
        return Response(result.to_dict(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AtletaDetailController(BaseController):
    """Controlador para operaciones sobre un atleta específico."""
    permission_classes = [permissions.AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = AtletaService()

    @extend_schema(tags=['Atletas'], summary='Obtener atleta', responses={200: AtletaOutputSerializer})
    def get(self, request, pk: int):
        """Obtiene un atleta por ID."""
        result = self.service.obtener_atleta(pk)
        if result.is_success:
            return Response(result.to_dict(), status=status.HTTP_200_OK)
        if result.status == ResultStatus.NOT_FOUND:
            return Response(result.to_dict(), status=status.HTTP_404_NOT_FOUND)
        return Response(result.to_dict(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(tags=['Atletas'], summary='Actualizar atleta', request=AtletaUpdateSerializer)
    def put(self, request, pk: int):
        """Actualiza un atleta."""
        serializer = AtletaUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'status': 'validation_error', 'errors': list(serializer.errors.values())},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = self.service.actualizar_atleta(pk, serializer.validated_data)
        if result.is_success:
            return Response(result.to_dict(), status=status.HTTP_200_OK)
        if result.status == ResultStatus.NOT_FOUND:
            return Response(result.to_dict(), status=status.HTTP_404_NOT_FOUND)
        return Response(result.to_dict(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(tags=['Atletas'], summary='Dar de baja atleta')
    def delete(self, request, pk: int):
        """Da de baja un atleta."""
        result = self.service.dar_de_baja(pk)
        if result.is_success:
            return Response(result.to_dict(), status=status.HTTP_200_OK)
        if result.status == ResultStatus.NOT_FOUND:
            return Response(result.to_dict(), status=status.HTTP_404_NOT_FOUND)
        return Response(result.to_dict(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AtletaReactivarController(BaseController):
    """Controlador para reactivar atletas."""
    permission_classes = [permissions.AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = AtletaService()

    @extend_schema(tags=['Atletas'], summary='Reactivar atleta')
    def post(self, request, pk: int):
        """Reactiva un atleta dado de baja."""
        result = self.service.reactivar_atleta(pk)
        if result.is_success:
            return Response(result.to_dict(), status=status.HTTP_200_OK)
        if result.status == ResultStatus.NOT_FOUND:
            return Response(result.to_dict(), status=status.HTTP_404_NOT_FOUND)
        return Response(result.to_dict(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

## 4️⃣ Registrar las Rutas

### Ubicación: `basketball/urls.py`

```python
from basketball.controllers.atleta_controller import (
    AtletaListController,
    AtletaDetailController,
    AtletaReactivarController,
)

urlpatterns = [
    # ... rutas existentes ...

    # Atletas
    path('atletas/', AtletaListController.as_view(), name='atleta-list'),
    path('atletas/<int:pk>/', AtletaDetailController.as_view(), name='atleta-detail'),
    path('atletas/<int:pk>/reactivar/', AtletaReactivarController.as_view(), name='atleta-reactivar'),
]
```

---

## 5️⃣ Crear Tests

### Tests de Controller

**Ubicación: `basketball/tests/controllers/test_atleta.py`**

```python
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from basketball.services.atleta_service import AtletaService
from basketball.services.base_service import ServiceResult


class AtletaAPITests(APITestCase):
    """Tests para los endpoints de Atleta."""

    def setUp(self):
        self.base_url = '/api/basketball/atletas/'
        self.valid_data = {
            'nombre': 'Carlos',
            'apellido': 'López',
            'email': 'carlos.lopez@unl.edu.ec',
            'clave': 'password123',
            'dni': '1234567890',
            'sexo': 'M'
        }

    @patch('basketball.controllers.atleta_controller.AtletaService')
    def test_listar_atletas(self, MockService):
        mock_service = MockService.return_value
        mock_service.listar_atletas.return_value = ServiceResult.success([])

        response = self.client.get(self.base_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('basketball.controllers.atleta_controller.AtletaService')
    def test_crear_atleta_exitoso(self, MockService):
        mock_service = MockService.return_value
        mock_data = {'id': 1, 'nombre': 'Carlos', **self.valid_data}
        mock_service.crear_atleta.return_value = ServiceResult.success(mock_data)

        response = self.client.post(self.base_url, self.valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # ... más tests ...
```

### Tests de Service

**Ubicación: `basketball/tests/services/test_atleta_service.py`**

```python
from django.test import TestCase
from unittest.mock import Mock, patch

from basketball.models import Atleta
from basketball.dao.model_daos import AtletaDAO
from basketball.services.atleta_service import AtletaService
from basketball.services.base_service import ResultStatus


class AtletaServiceTests(TestCase):
    """Tests para el servicio de Atleta."""

    def setUp(self):
        self.service = AtletaService()
        self.valid_data = {
            'nombre': 'Carlos',
            'apellido': 'López',
            'email': 'carlos.lopez@unl.edu.ec',
            'clave': 'password123',
            'dni': '1234567890',
            'sexo': 'M'
        }

    @patch.object(AtletaDAO, 'get_by_dni')
    @patch.object(AtletaDAO, 'create')
    def test_crear_atleta_exitoso(self, mock_create, mock_get_by_dni):
        mock_get_by_dni.return_value = None
        mock_atleta = Mock(spec=Atleta)
        mock_atleta.pk = 1
        mock_atleta.nombre = 'Carlos'
        mock_create.return_value = mock_atleta

        result = self.service.crear_atleta(self.valid_data)

        self.assertTrue(result.is_success)
        self.assertEqual(result.data['nombre'], 'Carlos')

    # ... más tests ...
```

---

## 🚀 Checklist de Implementación

- [ ] Crear DAO en `basketball/dao/model_daos.py`
- [ ] Crear Service en `basketball/services/[modelo]_service.py`
- [ ] Crear Controller en `basketball/controllers/[modelo]_controller.py`
- [ ] Registrar rutas en `basketball/urls.py`
- [ ] Crear tests de controller en `basketball/tests/controllers/test_[modelo].py`
- [ ] Crear tests de service en `basketball/tests/services/test_[modelo]_service.py`
- [ ] Crear tests de DAO en `basketball/tests/dao/test_[modelo]_dao.py`
- [ ] Ejecutar tests: `docker-compose exec web python manage.py test basketball.tests`
- [ ] Verificar endpoints en `/docs/`
- [ ] Commit: `git commit -m "feat: implementar CRUD para [Modelo]"`

---

## 📝 Ejemplo: Flujo Completo para Atleta

```bash
# 1. Crear DAO
# Editar: basketball/dao/model_daos.py

# 2. Crear Service
# Crear: basketball/services/atleta_service.py

# 3. Crear Controller
# Crear: basketball/controllers/atleta_controller.py

# 4. Registrar rutas
# Editar: basketball/urls.py

# 5. Crear tests
# Crear: basketball/tests/controllers/test_atleta.py
# Crear: basketball/tests/services/test_atleta_service.py
# Crear: basketball/tests/dao/test_atleta_dao.py

# 6. Ejecutar tests
docker-compose exec web python manage.py test basketball.tests --verbosity=2

# 7. Ver endpoints
open http://localhost:8000/docs/

# 8. Commit
git add .
git commit -m "feat: implementar CRUD para Atleta"
git push origin feature/christian
```

---

## 🎯 Patrones Importantes

### 1. **Siempre validar en Service, no en Controller**

```python
# ❌ INCORRECTO - Validación en Controller
if not email.endswith('@unl.edu.ec'):
    return Response(..., status=400)

# ✅ CORRECTO - Validación en Service
def _validate_email(self, email: str) -> Optional[str]:
    if not email.endswith('@unl.edu.ec'):
        return "Email debe ser institucional"
    return None
```

### 2. **Usar ServiceResult para consistencia**

```python
# ✅ CORRECTO
return ServiceResult.success(data=atleta_dict, message="Atleta creado")
return ServiceResult.validation_error("Error", errors_list)
return ServiceResult.not_found("Atleta no encontrado")

# Mapeará automáticamente a:
# success → 200/201
# validation_error → 400
# not_found → 404
# conflict → 409
# error → 500
```

### 3. **Usar DAO genérico para operaciones comunes**

```python
# Heredar de GenericDAO
class AtletaDAO(GenericDAO[Atleta]):
    model = Atleta
    
    # Métodos del genérico disponibles
    self.get_by_id(1)
    self.create(nombre='Juan')
    self.update(1, nombre='Juan')
    self.soft_delete(1)
```

### 4. **Soft Delete siempre**

```python
# ❌ INCORRECTO - Borrar permanentemente
self.dao.delete(pk)

# ✅ CORRECTO - Soft delete con estado=False
self.dao.soft_delete(pk, field='estado')
```

---

## 🔗 Referencias Rápidas

- Entrenador: Implementación completa ✅
- EstudianteVinculacion: Implementación completa ✅
- Base: `GenericDAO`, `BaseService`, `BaseController`

Usa estos como referencia para nuevos módulos.

