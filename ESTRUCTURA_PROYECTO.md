# Estructura Completa del Proyecto baloncesto_backend

## 📋 Índice
1. [Descripción General](#descripción-general)
2. [Estructura de Directorios](#estructura-de-directorios)
3. [Componentes Principales](#componentes-principales)
4. [Base de Datos](#base-de-datos)
5. [Autenticación y Permisos](#autenticación-y-permisos)
6. [API Endpoints](#api-endpoints)
7. [Tecnologías Utilizadas](#tecnologías-utilizadas)
8. [Configuración](#configuración)

---

## 📝 Descripción General

**baloncesto_backend** es un API REST construido con Django y Django REST Framework para la gestión de:
- 🏋️ Atletas y sus pruebas (antropométricas y físicas)
- 👨‍🏫 Entrenadores
- 📚 Estudiantes de Vinculación (pasantes)
- 🏆 Inscripciones al club
- 📊 Datos antropométricos y pruebas físicas

**Características:**
- Autenticación JWT (Simple JWT)
- Documentación automática con Swagger/OpenAPI
- PostgreSQL como base de datos
- Arquitectura de 3 capas (Controller → Service → DAO)
- Tests automatizados con pytest
- Dockerizado para desarrollo

---

## 📁 Estructura de Directorios

```
baloncesto_backend/
├── basketball_project/          # Configuración principal de Django
│   ├── settings.py             # Configuraciones de Django, BD, JWT, CORS
│   ├── urls.py                 # Rutas principales del proyecto
│   ├── wsgi.py                 # WSGI para producción
│   └── asgi.py                 # ASGI para WebSockets
│
├── basketball/                  # Aplicación principal
│   ├── models.py               # Modelos de BD (ORM Django)
│   ├── admin.py                # Admin de Django
│   ├── apps.py                 # Configuración de la app
│   ├── urls.py                 # Rutas de basketball
│   │
│   ├── controllers/            # Capa de Controladores (HTTP)
│   │   ├── base_controller.py
│   │   ├── entrenador_controller.py      # ✅ IMPLEMENTADO
│   │   ├── estudiante_vinculacion_controller.py  # ✅ IMPLEMENTADO
│   │   ├── atleta_controller.py          # TODO
│   │   ├── grupo_atleta_controller.py    # TODO
│   │   ├── inscripcion_controller.py     # TODO
│   │   ├── prueba_antropometrica_controller.py  # TODO
│   │   └── prueba_fisica_controller.py   # TODO
│   │
│   ├── services/               # Capa de Servicios (Lógica de Negocio)
│   │   ├── base_service.py
│   │   ├── entrenador_service.py         # ✅ IMPLEMENTADO
│   │   ├── estudiante_vinculacion_service.py  # ✅ IMPLEMENTADO
│   │   ├── model_services.py
│   │   └── [otros servicios]
│   │
│   ├── dao/                    # Capa de Acceso a Datos
│   │   ├── generic_dao.py      # Base DAO genérica
│   │   └── model_daos.py       # DAOs específicos (EntrenadorDAO, etc.)
│   │
│   ├── connection/             # Conexión a BD
│   │   └── db_connection.py
│   │
│   ├── auth/                   # Autenticación JWT
│   │   └── jwt_serializers.py
│   │
│   ├── permissions.py          # Permisos personalizados
│   │
│   ├── migrations/             # Migraciones de BD
│   │   └── 0001_initial.py
│   │
│   └── tests/                  # Tests automatizados
│       ├── controllers/        # Tests de controladores
│       ├── services/           # Tests de servicios
│       └── dao/                # Tests de DAO
│
├── docker/                      # Configuración de Docker
│   └── init.sql                # Script de inicialización BD
│
├── static/                      # Archivos estáticos (CSS, JS)
├── templates/                   # Plantillas HTML
├── manage.py                    # CLI de Django
├── docker-compose.yml          # Orquestación de contenedores
├── Dockerfile                  # Imagen Docker del proyecto
├── requirements.txt            # Dependencias Python
└── README.md                   # Documentación

```

---

## 🔧 Componentes Principales

### 1. **Models (Base de Datos)**

#### Jerarquía de Herencia:
```
Usuario (Base)
├── Entrenador
└── EstudianteVinculacion
```

#### Modelos Principales:

| Modelo | Descripción | Estado |
|--------|-------------|--------|
| **Usuario** | Base para todos los usuarios | Referencia |
| **Entrenador** | Extiende Usuario, especialidad y club | ✅ Implementado |
| **EstudianteVinculacion** | Extiende Usuario, carrera y semestre | ✅ Implementado |
| **Atleta** | Información de atletas | Modelo sí, CRUD no |
| **GrupoAtleta** | Grupos de atletas | Modelo sí, CRUD no |
| **Inscripcion** | Registros en competiciones | Modelo sí, CRUD no |
| **PruebaAntropometrica** | Medidas físicas (IMC, estatura, etc.) | Modelo sí, CRUD no |
| **PruebaFisica** | Pruebas de desempeño (velocidad, fuerza, etc.) | Modelo sí, CRUD no |

### 2. **Arquitectura en 3 Capas**

```
HTTP Request
    ↓
┌─────────────────────────────────┐
│ CONTROLLER (HTTP)               │
│ - Recibe requests               │
│ - Valida serializers            │
│ - Mapea a HTTP status codes     │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ SERVICE (Lógica de Negocio)     │
│ - Validaciones complejas        │
│ - Reglas de negocio             │
│ - Manejo de errores             │
│ - ServiceResult pattern         │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ DAO (Acceso a Datos)            │
│ - Queries a BD                  │
│ - CRUD operations               │
│ - Filtering, searching          │
└─────────────────────────────────┘
    ↓
  DATABASE (PostgreSQL)
```

### 3. **Patrón ServiceResult**

Todas las respuestas siguen este patrón:

```python
{
    "status": "success|error|validation_error|not_found|conflict",
    "message": "Descripción del resultado",
    "data": {...},  # Información principal
    "errors": [...]  # Errores de validación
}
```

**Mapeo a HTTP Status:**
- `success` → 200 OK / 201 Created
- `validation_error` → 400 Bad Request
- `not_found` → 404 Not Found
- `conflict` → 409 Conflict
- `error` → 500 Internal Server Error

### 4. **DAO Genérico (GenericDAO)**

Proporciona operaciones CRUD reutilizables:

```python
class GenericDAO(Generic[T]):
    - get_by_id(pk)
    - create(**kwargs)
    - update(pk, **kwargs)
    - soft_delete(pk, field='estado')
    - get_all()
    - get_by_filter(**kwargs)
    - search(search_fields, search_term)
```

---

## 💾 Base de Datos

### Conexión:
- **Motor**: PostgreSQL 15-alpine
- **Host**: `localhost:5432` (en Docker: `db:5432`)
- **Usuario**: `basketball_user`
- **Contraseña**: `basketball_pass_2024`
- **BD**: `basketball_db`

### Tablas Creadas:
```sql
-- Principales
usuario
entrenador
estudiante_vinculacion
atleta
grupo_atleta
inscripcion
prueba_antropometrica
prueba_fisica

-- Django Auth
auth_user
auth_group
auth_permission
django_migrations
django_session
django_admin_log
django_content_type
```

### Características:
- **Soft Delete**: Campo `estado` (True=activo, False=inactivo)
- **Timestamps**: `fecha_registro` (auto_now_add)
- **Validaciones**: MinValueValidator, MaxValueValidator
- **Relaciones**: ForeignKey con CASCADE

---

## 🔐 Autenticación y Permisos

### JWT (JSON Web Tokens)

**Endpoints:**
- `POST /api/auth/token/` → Obtener tokens (login)
- `POST /api/auth/token/refresh/` → Refrescar token
- `POST /api/auth/token/verify/` → Verificar validez
- `POST /api/auth/token/blacklist/` → Logout

**Estructura del Token:**
```python
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "username": "user",
        "email": "user@unl.edu.ec",
        "rol": "ENTRENADOR"
    }
}
```

### Permisos Implementados:

| Permiso | Descripción |
|---------|-------------|
| `AllowAny` | Acceso sin autenticación (desarrollo) |
| `IsAuthenticated` | Requiere autenticación (producción) |
| `IsAdminUser` | Solo administradores |
| `CanManageAtletas` | Admins y Entrenadores |
| `IsAuthenticatedOrReadOnly` | Lectura pública, escritura autenticada |

### Validaciones Personalizadas:

**Email Institucional:**
- Patrón: `nombre@unl.edu.ec`
- Validación: Regex + dominio específico

**DNI:**
- Longitud: Exactamente 10 dígitos
- Formato: Numérico

---

## 🌐 API Endpoints

### Entrenadores ✅ Implementado

```
GET    /api/basketball/entrenadores/
       - Listar entrenadores activos
       - Query param: ?solo_activos=true|false

POST   /api/basketball/entrenadores/
       - Crear nuevo entrenador
       - Body: {nombre, apellido, email, dni, clave, especialidad, club_asignado}

GET    /api/basketball/entrenadores/{id}/
       - Obtener detalles de un entrenador

PUT    /api/basketball/entrenadores/{id}/
       - Actualizar entrenador
       - Body: {nombre, apellido, email, especialidad, club_asignado}

DELETE /api/basketball/entrenadores/{id}/
       - Dar de baja entrenador (soft delete)

POST   /api/basketball/entrenadores/{id}/reactivar/
       - Reactivar entrenador dado de baja
```

### Estudiantes de Vinculación ✅ Implementado

```
GET    /api/basketball/estudiantes-vinculacion/
       - Listar estudiantes activos
       - Query param: ?solo_activos=true|false

POST   /api/basketball/estudiantes-vinculacion/
       - Crear nuevo estudiante
       - Body: {nombre, apellido, email, dni, clave, carrera, semestre}

GET    /api/basketball/estudiantes-vinculacion/{id}/
       - Obtener detalles de un estudiante

PUT    /api/basketball/estudiantes-vinculacion/{id}/
       - Actualizar estudiante
       - Body: {nombre, apellido, email, carrera, semestre}

DELETE /api/basketball/estudiantes-vinculacion/{id}/
       - Dar de baja estudiante (soft delete)

POST   /api/basketball/estudiantes-vinculacion/{id}/reactivar/
       - Reactivar estudiante dado de baja
```

### Otros Endpoints (TODO)

```
# Atletas
/api/basketball/atletas/
/api/basketball/atletas/{id}/

# Grupos de Atletas
/api/basketball/grupos/
/api/basketball/grupos/{id}/

# Inscripciones
/api/basketball/inscripciones/
/api/basketball/inscripciones/{id}/

# Pruebas Antropométricas
/api/basketball/pruebas-antropometricas/
/api/basketball/pruebas-antropometricas/{id}/

# Pruebas Físicas
/api/basketball/pruebas-fisicas/
/api/basketball/pruebas-fisicas/{id}/
```

---

## 🛠 Tecnologías Utilizadas

### Backend
- **Django** 4.2.7 - Framework web
- **Django REST Framework** 3.14.0 - API REST
- **Simple JWT** 5.3.1 - Autenticación JWT
- **drf-spectacular** 0.27.0 - Documentación Swagger/OpenAPI
- **CORS Headers** 4.3.1 - Manejo de CORS

### Base de Datos
- **PostgreSQL** 15-alpine - BD relacional
- **psycopg2-binary** 2.9.9 - Driver PostgreSQL

### Testing
- **pytest** 7.4.3 - Framework de testing
- **pytest-django** 4.7.0 - Integración pytest-Django
- **coverage** 7.3.2 - Cobertura de código

### Code Quality
- **Black** 23.11.0 - Formateador de código
- **Flake8** 6.1.0 - Linter

### Deployment
- **Docker** - Containerización
- **Docker Compose** - Orquestación

---

## ⚙️ Configuración

### Environment Variables

```bash
# Django
DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Base de Datos
USE_SQLITE=False
DB_HOST=db
DB_NAME=basketball_db
DB_USER=basketball_user
DB_PASSWORD=basketball_pass_2024
DB_PORT=5432

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Instalación Local

```bash
# 1. Clonar repositorio
git clone <repo>
cd baloncesto_backend

# 2. Crear virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows
source .venv/bin/activate       # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Migrar BD
python manage.py migrate

# 5. Crear superusuario
python manage.py createsuperuser

# 6. Ejecutar servidor
python manage.py runserver
```

### Con Docker

```bash
# 1. Levantar contenedores
docker-compose up -d

# 2. Crear superusuario
docker-compose exec web python manage.py createsuperuser

# 3. Acceder
# API: http://localhost:8000/api/basketball/
# Docs: http://localhost:8000/docs/
# Admin: http://localhost:8000/admin/
```

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
docker-compose exec web python manage.py test basketball.tests --verbosity=2

# Solo Entrenador
docker-compose exec web python manage.py test basketball.tests.controllers.test_entrenador --verbosity=2

# Solo EstudianteVinculación
docker-compose exec web python manage.py test basketball.tests.controllers.test_estudiante_vinculacion --verbosity=2

# Con cobertura
coverage run --source='basketball' manage.py test basketball.tests
coverage report
```

### Tests Actuales

- ✅ 10 tests - Entrenador (Controller, DAO, Service)
- ✅ 27 tests - EstudianteVinculacion (Controller, DAO, Service)
- **Total**: 38 tests pasando

---

## 📚 Próximas Implementaciones

- [ ] DAO + Service para Atleta
- [ ] DAO + Service para GrupoAtleta
- [ ] DAO + Service para Inscripcion
- [ ] DAO + Service para PruebaAntropometrica
- [ ] DAO + Service para PruebaFisica
- [ ] Controladores para todos los modelos
- [ ] Tests para nuevos endpoints
- [ ] Integración con módulo de Usuarios

---

## 📖 Documentación

- **Swagger UI**: http://localhost:8000/docs/
- **ReDoc**: http://localhost:8000/redoc/
- **Admin Django**: http://localhost:8000/admin/
- **API Schema**: http://localhost:8000/api/schema/

---

## 👨‍💻 Rama Actual

- **Branch**: `feature/christian`
- **Últimos Commits**: 
  - CRUD Entrenador implementado
  - Tests (68 total) pasando
  - AllowAny permissions agregados
  - PostgreSQL configurado

---

## 🔗 Relaciones de Modelos

```
Usuario (Base)
  ├─ Entrenador
  │  └─ especialidad
  │     club_asignado
  │
  └─ EstudianteVinculacion
     ├─ carrera
     └─ semestre

Atleta
  ├─ FK → GrupoAtleta (many-to-many)
  ├─ FK → Usuario (many-to-one) [trainer info]
  ├─ OneToMany → Inscripcion
  ├─ OneToMany → PruebaAntropometrica
  └─ OneToMany → PruebaFisica

Inscripcion
  ├─ FK → Atleta
  └─ Tipos: FEDERADO, NO_FEDERADO, INVITADO

PruebaAntropometrica
  └─ FK → Atleta

PruebaFisica
  └─ FK → Atleta
     └─ Tipos: VELOCIDAD, RESISTENCIA, FUERZA, etc.
```

---

## 📞 Contacto / Información

- **Proyecto**: Sistema de Gestión de Basketball
- **Lenguaje**: Python + Django
- **BD**: PostgreSQL
- **Año**: 2025

