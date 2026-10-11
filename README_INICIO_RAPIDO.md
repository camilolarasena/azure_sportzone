# SportZone con flask_mysqldb + XAMPP

## Configuracion solicitada

Toda la conexion esta en `config.py`, no en `.env`. Flask usa:

```python
app.config["MYSQL_HOST"] = MYSQL_HOST
app.config["MYSQL_USER"] = MYSQL_USER
app.config["MYSQL_PASSWORD"] = MYSQL_PASSWORD
app.config["MYSQL_DB"] = MYSQL_DB
mysql = MySQL()
mysql.init_app(app)
```

Los valores se leen desde `config.py`:

```python
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DB = "tienda_deportiva"
MYSQL_PORT = 3306
```

**IMPORTANTE:** en la version anterior importaste la base `sportzone`. Si esa base sigue siendo la que contiene tus tablas, cambia `MYSQL_DB = "sportzone"` en `config.py`. No necesitas importar los datos otra vez. El nombre debe coincidir exactamente con phpMyAdmin.

## Ejecucion en Windows / VS Code

1. Inicia MySQL desde XAMPP.
2. Abre la carpeta del proyecto en VS Code.
3. Ajusta `config.py` al nombre real de la base y a tu contrasena.
4. Ejecuta:

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m flask --app app run
```

5. Visita `http://127.0.0.1:5000`.

No se usa `.env`. `config.py` se excluye del repositorio por `.gitignore`: no lo publiques con credenciales reales. No uses usuario `root` ni contrasena vacia en produccion.

## Notas tecnicas

- Se migraron las consultas a un adaptador de `MySQLdb` con `DictCursor`, porque los controladores `mysql.connector` y `flask_mysqldb` usan interfaces diferentes.
- `?` del codigo anterior se traduce a `%s` para parametrizar las consultas.
- La analitica usa SQLAlchemy con el controlador MySQLdb (`mysql+mysqldb`).
- No se realizo una prueba de extremo a extremo contra una instancia real de XAMPP; si aparece un error, comparte el traceback de VS Code.
- Los archivos SQL adjuntos incluyen datos migrados: mantenlos privados.
