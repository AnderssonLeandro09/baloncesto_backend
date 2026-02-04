# Basketball Backend - Sistema de Gestión Deportiva

API REST para la gestión de atletas, entrenadores, estudiantes de vinculación y pruebas físicas/antropométricas en un programa de baloncesto.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Requisitos Previos](#requisitos-previos)
- [Tecnologías](#tecnologías)
- [Instalación y Configuración](#instalación-y-configuración)
  - [Opción 1: Instalación Local (sin Docker)](#opción-1-instalación-local-sin-docker)
  - [Opción 2: Instalación con Docker](#opción-2-instalación-con-docker)
- [Ejecución de Tests](#ejecución-de-tests)
- [Documentación de la API](#documentación-de-la-api)
- [Estructura del Proyecto](#estructura-del-proyecto)

---

## 🎯 Características

- Gestión de atletas, entrenadores y estudiantes de vinculación
- Registro de pruebas antropométricas y físicas
- Autenticación JWT delegada a módulo externo de usuarios
- API RESTful con documentación Swagger/OpenAPI
- Tests unitarios con mocks (sin dependencias externas)
- Soporte para SQLite (desarrollo) y PostgreSQL (producción)

---

## 📦 Requisitos Previos

### Para instalación local:
- **Python 3.11 o 3.12** (recomendado): con *Python 3.13* en Windows la instalación de psycopg2-binary puede fallar
- **pip** (gestor de paquetes de Python)
- **Git** (opcional, para clonar el repositorio)

### Para instalación con Docker:
- **Docker Desktop** (Windows/Mac) o **Docker Engine + Docker Compose** (Linux)
- Tener los puertos **8023** (backend) y **55432** (PostgreSQL) disponibles

---

## 🛠️ Tecnologías

- **Django 4.2.7** - Framework web
- **Django REST Framework 3.14.0** - API REST
- **PostgreSQL 15** - Base de datos (producción)
- **SQLite** - Base de datos (desarrollo local)
- **drf-spectacular** - Documentación OpenAPI/Swagger
- **pytest + pytest-django** - Testing
- **Docker + Docker Compose** - Contenedorización

---

## 🚀 Instalación y Configuración

### Clonar el repositorio

> ⚠️ **Importante:** Clonar o descargar el proyecto desde la rama `develop`

```bash
git clone -b develop https://github.com/AnderssonLeandro09/baloncesto_backend.git
cd baloncesto_backend
```

O si ya tienes el repositorio clonado:

```bash
git checkout develop
git pull origin develop
```

---

### Opción 1: Instalación Local (sin Docker)

Esta opción usa **SQLite** como base de datos y no requiere Docker.

#### 1. Crear un entorno virtual

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

#### 3. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto (puede copiar `.env.example`):

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

Editar el archivo `.env` para usar SQLite:

```dotenv
# Environment Configuration
DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-in-production-abc123xyz789

# Database Configuration (usar SQLite)
USE_SQLITE=True

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# User module (Spring) - Opcional para desarrollo
USER_MODULE_URL=http://localhost:8096
USER_MODULE_ADMIN_EMAIL=admin@admin.com
USER_MODULE_ADMIN_PASSWORD=12345678
```

#### 4. Aplicar migraciones

```bash
python manage.py migrate
```

#### 6. Crear superusuario (opcional)

```bash
python manage.py createsuperuser
```

#### 7. Ejecutar el servidor de desarrollo

```bash
python manage.py runserver
```

El servidor estará disponible en: **http://localhost:8000 o http://127.0.0.1:8000/**

---

### Opción 2: Instalación con Docker

Esta opción usa **PostgreSQL** como base de datos y levanta todo el stack en contenedores.

> ⚠️ **Importante:** Asegúrate de estar en la rama `develop` antes de continuar.

#### 1. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

Editar el archivo `.env` para usar PostgreSQL:

```dotenv
# Environment Configuration
DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-in-production-abc123xyz789

# Database Configuration (usar PostgreSQL con Docker)
DB_NAME=basketball_db
DB_USER=basketball_user
DB_PASSWORD=basketball_pass_2024
DB_HOST=db
DB_PORT=5432
USE_SQLITE=False

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# User module (Spring)
USER_MODULE_URL=http://host.docker.internal:8096
USER_MODULE_ADMIN_EMAIL=admin@admin.com
USER_MODULE_ADMIN_PASSWORD=12345678
```

#### 2. Construir y levantar los contenedores

```bash
docker-compose up --build
```

O en segundo plano:

```bash
docker-compose up -d --build
```

#### 3. Verificar que los contenedores estén corriendo

```bash
docker-compose ps
```

Deberías ver algo como:

```
NAME                 IMAGE                    STATUS         PORTS
basketball_db        postgres:15-alpine       Up (healthy)   0.0.0.0:55432->5432/tcp
basketball_web       baloncesto_backend-web   Up             0.0.0.0:8023->8000/tcp
```

#### 4. Acceder a la aplicación

El servidor estará disponible en: **http://localhost:8023**

#### 5. Crear superusuario (opcional)

```bash
docker-compose exec web python manage.py createsuperuser
```

#### 6. Ver logs

```bash
docker-compose logs -f web
```

#### 7. Detener los contenedores

```bash
docker-compose down
```

Para eliminar también los volúmenes (base de datos):

```bash
docker-compose down -v
```

---

## 🧪 Ejecución de Tests

El proyecto incluye tests unitarios en las carpetas `basketball/tests/test_aprobados/` y `basketball/tests/tests_aprobados/`. Los tests utilizan **mocks** para evitar dependencias externas (base de datos, módulo de usuarios).

### Ejecutar TODOS los tests

**Instalación Local:**

```bash
# Activar el entorno virtual primero
# Asegúrate de tener el archivo pytest.ini creado
pytest basketball/tests -v
```

**Con Docker:**

```bash
docker-compose exec web sh -c "export DJANGO_SETTINGS_MODULE=basketball_project.settings && pytest basketball/tests"
```

### Ejecutar solo los tests aprobados

**Instalación Local:**

```bash
pytest basketball/tests/test_aprobados basketball/tests/tests_aprobados -v
```

**Con Docker:**

```bash
docker-compose exec web sh -c "export DJANGO_SETTINGS_MODULE=basketball_project.settings && pytest basketball/tests/test_aprobados basketball/tests/tests_aprobados -v"
```

## 📚 Documentación de la API

### Swagger UI (Interactivo)

Accede a la documentación interactiva de la API:

- **Local:** http://localhost:8000/docs/ o http://127.0.0.1:8000/docs/
- **Docker:** http://localhost:8023/docs/

### Panel de Administración Django

**Local:** http://localhost:8000/admin/  
**Docker:** http://localhost:8023/admin/

---

## 📁 Estructura del Proyecto

```
baloncesto_backend/
├── basketball/                      # Aplicación principal
│   ├── controllers/                 # Controladores (ViewSets)
│   │   ├── administrador_controller.py
│   │   ├── atleta_controller.py
│   │   ├── entrenador_controller.py
│   │   ├── prueba_antropometrica_controller.py
│   │   └── prueba_fisica_controller.py
│   ├── dao/                         # Data Access Objects
│   │   ├── administrador_dao.py
│   │   ├── atleta_dao.py
│   │   └── generic_dao.py
│   ├── services/                    # Lógica de negocio
│   ├── connection/                  # Conexiones (módulo de usuarios)
│   ├── serializar/                  # Serializers
│   ├── tests/                       # Tests
│   │   └── tests_aprobados/         # Tests aprobados y funcionales
│   │       ├── test_entrenador.py
│   │       └── test_prueba_antropometrica.py
│   ├── migrations/                  # Migraciones de base de datos
│   ├── models.py                    # Modelos de Django
│   ├── urls.py                      # Rutas de la API
│   ├── views.py                     # Vistas
│   ├── authentication.py            # Autenticación JWT
│   └── permissions.py               # Permisos personalizados
├── basketball_project/              # Configuración del proyecto
│   ├── settings.py                  # Configuración de Django
│   ├── urls.py                      # URLs principales
│   └── wsgi.py                      # WSGI application
├── docker/                          # Archivos Docker
│   └── init.sql                     # Script inicial de PostgreSQL
├── manage.py                        # CLI de Django
├── requirements.txt                 # Dependencias Python
├── pyproject.toml                   # Configuración de herramientas
├── Dockerfile                       # Definición de imagen Docker
├── docker-compose.yml               # Orquestación de contenedores
├── .env.example                     # Ejemplo de variables de entorno
└── README.md                        # Este archivo
```

---

## 🔧 Comandos Útiles

### Django Management Commands

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recopilar archivos estáticos
python manage.py collectstatic

# Abrir shell de Django
python manage.py shell

# Ver todas las migraciones
python manage.py showmigrations
```

### Docker Commands

```bash
# Ver contenedores activos
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f

# Ejecutar comando en contenedor
docker-compose exec web python manage.py migrate

# Reconstruir sin cache
docker-compose build --no-cache

# Eliminar todo (contenedores, redes, volúmenes)
docker-compose down -v
```

---

## 🐛 Solución de Problemas

### Error: Puerto 8023 ya está en uso

```bash
# Windows
netstat -ano | findstr :8023
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8023 | xargs kill -9
```

### Error: Base de datos no existe

```bash
# Recrear base de datos con Docker
docker-compose down -v
docker-compose up --build
```

### Error: Módulo no encontrado

```bash
# Reinstalar dependencias
pip install -r requirements.txt --upgrade
```

### Tests fallan con errores de conexión

Los tests en `tests_aprobados/` usan mocks y **NO deben requerir** base de datos ni servicios externos. Si fallan, verificar que:
- pytest y pytest-django estén instalados
- Los mocks estén correctamente configurados

---
