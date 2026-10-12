# SportZone - PostgreSQL en Azure

Archivos listos para reemplazar en la raiz del repositorio: `app.py`, `database.py`, `config.py`, `requirements.txt`, `analytics_pdf.py`.

**No vuelvas a importar el SQL:** tu base ya tiene 8 tablas y 21 productos.

## Configuracion de Azure App Service

App Service `tiendavirtualtgs` > Configuracion > Variables de entorno > Configuracion de aplicacion:

- `PGHOST` = `tiendavirtualtgs-server.postgres.database.azure.com`
- `PGPORT` = `5432`
- `PGDATABASE` = `tiendavirtualtgs-database`
- `PGUSER` = `tcuoaibwzb`
- `PGPASSWORD` = tu contrasena nueva (NO la publiques en GitHub)
- `PGSSLMODE` = `require`
- `SECRET_KEY` = clave aleatoria larga, privada y estable
- `SESSION_COOKIE_SECURE` = `true`
- `SEED_PRODUCTS` = `false`

En el App Service Linux, configura el **comando de inicio** como:

```bash
gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 app:app
```

Despliega el repositorio desde Centro de implementacion (GitHub) y revisa Registros de implementación y Log Stream. Conserva las carpetas `templates/` y `static/` y utiliza el modulo `analytics_pdf.py` incluido en este paquete.

### Pendiente importante: imagenes

La base contiene rutas `/static/uploads/products/*.webp` pero los archivos reales no viajan con el SQL. Copia tus imagenes locales por separado y considera Azure Blob Storage o un almacenamiento persistente para futuras cargas: actualmente `app.py` guarda imagenes en `static/uploads/products`.

### Verificacion funcional

Comprueba inicio de sesion, listado de productos, carrito, compra de prueba, inventario, administracion y exportacion de analitica. No pruebes compras reales: el codigo original implementa pagos demostrativos.

**Nota:** el arranque inicial llama `init_db()` para completar registros faltantes. Debe ejecutarse solo contra una base con el esquema ya importado.
