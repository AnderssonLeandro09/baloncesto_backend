"""
Módulo de conexión a la base de datos PostgreSQL

Este módulo proporciona funcionalidades adicionales para la conexión
y gestión de la base de datos.
"""

import logging
from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Clase para gestionar la conexión a la base de datos PostgreSQL.
    Proporciona métodos utilitarios para verificar y gestionar conexiones.
    """

    @staticmethod
    def check_connection(database="default"):
        """
        Verifica si la conexión a la base de datos está activa.

        Args:
            database (str): Nombre de la base de datos en settings.DATABASES

        Returns:
            bool: True si la conexión está activa, False en caso contrario
        """
        try:
            db_conn = connections[database]
            db_conn.cursor()
            logger.info(
                f"Conexión a la base de datos '{database}' establecida correctamente."
            )
            return True
        except OperationalError as e:
            logger.error(f"Error al conectar a la base de datos '{database}': {e}")
            return False

    @staticmethod
    def get_connection_info(database="default"):
        """
        Obtiene información de la conexión actual.

        Args:
            database (str): Nombre de la base de datos en settings.DATABASES

        Returns:
            dict: Diccionario con información de la conexión
        """
        from django.conf import settings

        db_settings = settings.DATABASES.get(database, {})
        return {
            "engine": db_settings.get("ENGINE", "N/A"),
            "name": db_settings.get("NAME", "N/A"),
            "host": db_settings.get("HOST", "N/A"),
            "port": db_settings.get("PORT", "N/A"),
            "user": db_settings.get("USER", "N/A"),
        }

    @staticmethod
    def execute_raw_query(query, params=None, database="default"):
        """
        Ejecuta una consulta SQL cruda.

        Args:
            query (str): Consulta SQL a ejecutar
            params (tuple): Parámetros para la consulta
            database (str): Nombre de la base de datos

        Returns:
            list: Resultados de la consulta
        """
        try:
            with connections[database].cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                return []
        except Exception as e:
            logger.error(f"Error al ejecutar consulta: {e}")
            raise

    @staticmethod
    def close_connection(database="default"):
        """
        Cierra la conexión a la base de datos.

        Args:
            database (str): Nombre de la base de datos
        """
        try:
            connections[database].close()
            logger.info(f"Conexión a '{database}' cerrada correctamente.")
        except Exception as e:
            logger.error(f"Error al cerrar conexión: {e}")


class ConnectionPool:
    """
    Clase para gestionar un pool de conexiones (wrapper sobre Django).
    Django maneja automáticamente el pool de conexiones, pero esta clase
    proporciona una interfaz adicional para gestión avanzada.
    """

    @staticmethod
    def get_pool_status():
        """
        Obtiene el estado del pool de conexiones.

        Returns:
            dict: Estado de las conexiones
        """
        status = {}
        for alias in connections:
            conn = connections[alias]
            status[alias] = {
                "is_usable": conn.is_usable() if hasattr(conn, "is_usable") else "N/A",
                "vendor": conn.vendor if hasattr(conn, "vendor") else "N/A",
            }
        return status

    @staticmethod
    def close_all_connections():
        """
        Cierra todas las conexiones activas.
        """
        connections.close_all()
        logger.info("Todas las conexiones han sido cerradas.")
