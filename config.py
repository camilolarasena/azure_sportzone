"""Configuracion segura de SportZone PostgreSQL / Azure App Service."""
import os

PGHOST = os.environ.get("PGHOST", "tiendavirtualtgs-server.postgres.database.azure.com")
PGPORT = int(os.environ.get("PGPORT", "5432"))
PGDATABASE = os.environ.get("PGDATABASE", "tiendavirtualtgs-database")
PGUSER = os.environ.get("PGUSER", "tcuoaibwzb")
PGPASSWORD = os.environ.get("PGPASSWORD")
PGSSLMODE = os.environ.get("PGSSLMODE", "require")

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Configura SECRET_KEY en Variables de entorno de App Service.")
if not PGPASSWORD:
    raise RuntimeError("Configura PGPASSWORD en Variables de entorno de App Service.")
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() in {"1", "true", "yes"}
SEED_PRODUCTS = os.environ.get("SEED_PRODUCTS", "false").lower() in {"1", "true", "yes"}
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
