import os
import django
import requests
import sys

# Configuración del entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'basketball_project.settings')
django.setup()

from django.conf import settings
from basketball.services.administrador_service import AdministradorService

def create_admin():
    # 1. Obtener credenciales del .env a través de settings
    user_module_url = settings.USER_MODULE_URL.rstrip("/")
    admin_email = settings.USER_MODULE_ADMIN_EMAIL
    admin_password = settings.USER_MODULE_ADMIN_PASSWORD

    print(f"--- Iniciando creación de administrador ---")
    print(f"Conectando a módulo de usuarios: {user_module_url}")

    # 2. Login en el Microservicio de Usuarios para obtener el Token
    try:
        login_resp = requests.post(
            f"{user_module_url}/api/person/login",
            json={"email": admin_email, "password": admin_password},
            timeout=10
        )
        if login_resp.status_code != 200:
            print(f"Error login microservicio: {login_resp.text}")
            return

        token = login_resp.json().get("data", {}).get("token", "")
        token = token.replace("Bearer ", "") if token.startswith("Bearer ") else token
        print("Token de administrador obtenido correctamente.")
    except Exception as e:
        print(f"Error de conexión con microservicio: {e}")
        return

    # 3. Datos del nuevo administrador
    # Puedes cambiar estos datos según necesites
    persona_data = {
        "first_name": "Admin",
        "last_name": "Basketball",
        "email": "admin_basket@test.com",
        "password": "admin_password",
        "identification": "1122334455",
        "type_identification": "CEDULA",
        "type_stament": "ADMINISTRATIVOS",
        "phono": "0999999999",
        "direction": "Quito"
    }

    administrador_data = {
        "cargo": "Administrador Principal"
    }

    # 4. Usar el servicio para crear la persona y el registro local
    service = AdministradorService()
    try:
        result = service.create_administrador(persona_data, administrador_data, token)
        print("\n¡Éxito! Administrador creado:")
        print(f"ID Local: {result['administrador']['id']}")
        print(f"External ID: {result['administrador']['persona_external']}")
        print(f"Email: {persona_data['email']}")
    except Exception as e:
        print(f"\nError al crear administrador: {e}")

if __name__ == "__main__":
    create_admin()
