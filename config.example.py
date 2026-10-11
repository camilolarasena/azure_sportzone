"""Configuracion local de SportZone (NO publicar en GitHub)."""

# Conexion MySQL de XAMPP: ajusta estos valores segun tu instalacion.
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DB = "tienda_deportiva"
MYSQL_USER = "root"
MYSQL_PASSWORD = ""

# Seguridad de Flask. Mantener privada esta clave y no cambiarla a diario.
SECRET_KEY = "REEMPLAZA_CON_UNA_CLAVE_SECRETA_LARGA_Y_ALEATORIA"
SESSION_COOKIE_SECURE = False  # Cambiar a True cuando utilices HTTPS.

# Configuracion opcional.
SEED_PRODUCTS = False  # No insertar productos de ejemplo si ya importaste los datos.
ADMIN_EMAIL = ""
ADMIN_PASSWORD = ""  # Se recomienda crear el admin con el comando Flask.
