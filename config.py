"""Configuración de EDUDEBUG. Todo lo sensible se lee de variables de entorno (o del archivo .env)."""
import os

try:  # carga el archivo .env si existe (pruebas locales)
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv es opcional
    pass


class Config:
    # Clave para firmar los tokens de sesión. En Render debe ser una cadena larga y secreta.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-cambia-esto-en-produccion")

    # Base relacional (SQLite): las tablas del diagrama de la Fase inicial.
    SQLITE_PATH = os.environ.get("SQLITE_PATH", "instance/edudebug_v2.db")

    # MongoDB (opcional): la aplicación NO depende de él. Si defines MONGO_URI la conexión queda
    # lista (se ve en /api/salud) para usarla más adelante. "mongomock://" simula una base en memoria.
    MONGO_URI = os.environ.get("MONGO_URI", "")
    MONGO_DB = os.environ.get("MONGO_DB", "edudebug")

    # Orígenes permitidos para el frontend (separados por coma). "*" = cualquiera.
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # Crea las cuentas de prueba (estudiante@edudebug.com y profesor@edudebug.com, contraseña 123456).
    SEED_DEMO = os.environ.get("SEED_DEMO", "1") == "1"

    TOKEN_MAX_AGE = 7 * 24 * 3600  # 7 días, en segundos
    MAX_CODIGO_HTML = 20000        # caracteres máximos por envío al depurador
