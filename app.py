from __future__ import annotations

from MySQLdb import Error as DatabaseError, IntegrityError
from flask_mysqldb import MySQL
from database import DatabaseAdapter
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar
import secrets
from config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB,
    SECRET_KEY, SESSION_COOKIE_SECURE, SEED_PRODUCTS, ADMIN_EMAIL, ADMIN_PASSWORD,
)

import click
import pandas as pd
from analytics_pdf import build_analytics_pdf, build_dataset_pdf
from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from PIL import Image, ImageOps, UnidentifiedImageError

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "products"
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
F = TypeVar("F", bound=Callable[..., Any])

SEED_PRODUCTS = [
    (
        "Wilson Pro Staff 97 V14 Profesional",
        "Wilson",
        "tenis",
        "Raqueta profesional",
        "adulto",
        "Raqueta de control y precisión para jugadores avanzados.",
        1299900,
        8,
        "https://images.unsplash.com/photo-1617083934555-ac7d4d58ce51?w=900&q=80",
    ),
    (
        "Wilson Clash 100 V3",
        "Wilson",
        "tenis",
        "Raqueta normal",
        "adulto",
        "Raqueta versátil, cómoda y estable para nivel intermedio.",
        899900,
        14,
        "https://images.unsplash.com/photo-1622279457486-62dcc4a431d6?w=900&q=80",
    ),
    (
        "Babolat Pure Drive Team",
        "Babolat",
        "tenis",
        "Raqueta normal",
        "adulto",
        "Potencia accesible con peso ligero para juego recreativo y competitivo.",
        829900,
        10,
        "https://images.unsplash.com/photo-1595435934249-5df7ed86e1c0?w=900&q=80",
    ),
    (
        "Wilson Junior 26 3/4",
        "Wilson",
        "tenis",
        "Raqueta infantil 3/4",
        "niños",
        "Tamaño 3/4 recomendado para niños en proceso de iniciación.",
        249900,
        18,
        "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=900&q=80",
    ),
    (
        "Pelotas US Open x3",
        "Wilson",
        "tenis",
        "Pelotas",
        "todos",
        "Tubo de tres pelotas para entrenamiento y competencia.",
        39900,
        40,
        "https://images.unsplash.com/photo-1554068865-24cecd4e34b8?w=900&q=80",
    ),
    (
        "Driver Qi10 Max",
        "TaylorMade",
        "golf",
        "Driver",
        "adulto",
        "Driver de alta estabilidad y tolerancia para mejorar la salida.",
        2399900,
        6,
        "https://images.unsplash.com/photo-1535131749006-b7f58c99034b?w=900&q=80",
    ),
    (
        "Hierro 5 Paradym AI Smoke",
        "Callaway",
        "golf",
        "Hierro 5",
        "adulto",
        "Hierro individual con diseño orientado a distancia y control.",
        719900,
        7,
        "https://images.unsplash.com/photo-1587174486073-ae5e5cff23aa?w=900&q=80",
    ),
    (
        "Hierro 6 G430",
        "PING",
        "golf",
        "Hierro 6",
        "adulto",
        "Hierro individual con buena tolerancia y trayectoria consistente.",
        759900,
        8,
        "https://images.unsplash.com/photo-1587174486073-ae5e5cff23aa?w=900&q=80",
    ),
    (
        "Hierro 7 Darkspeed",
        "Cobra",
        "golf",
        "Hierro 7",
        "adulto",
        "Hierro equilibrado para precisión en golpes de aproximación.",
        689900,
        9,
        "https://images.unsplash.com/photo-1592919505780-303950717480?w=900&q=80",
    ),
    (
        "Hierro 8 Dynapower",
        "Wilson Staff",
        "golf",
        "Hierro 8",
        "adulto",
        "Hierro de control para golpes cortos y aproximaciones al green.",
        599900,
        11,
        "https://images.unsplash.com/photo-1593111774240-d529f12cf4bb?w=900&q=80",
    ),
    (
        "Putter White Hot Versa",
        "Odyssey",
        "golf",
        "Putter",
        "adulto",
        "Putter con alineación visual y sensación suave en el impacto.",
        1099900,
        5,
        "https://images.unsplash.com/photo-1591491653056-4d2f82d9bd66?w=900&q=80",
    ),
    (
        "Pelotas Pro V1 x12",
        "Titleist",
        "golf",
        "Pelotas",
        "todos",
        "Docena de pelotas premium con control y rendimiento integral.",
        249900,
        24,
        "https://images.unsplash.com/photo-1587174486073-ae5e5cff23aa?w=900&q=80",
    ),
    (
        "Sonic Core Revelation Pro",
        "Dunlop",
        "squash",
        "Raqueta profesional",
        "adulto",
        "Raqueta profesional de precisión y respuesta rápida.",
        649900,
        9,
        "https://images.unsplash.com/photo-1657704358775-ed705c7388d2?w=900&q=80",
    ),
    (
        "Graphene 360 Speed 135",
        "HEAD",
        "squash",
        "Raqueta normal",
        "adulto",
        "Raqueta balanceada para jugadores intermedios.",
        469900,
        13,
        "https://images.unsplash.com/photo-1657704358775-ed705c7388d2?w=900&q=80",
    ),
    (
        "Carboflex 125 X-Top",
        "Tecnifibre",
        "squash",
        "Raqueta profesional",
        "adulto",
        "Raqueta ligera para velocidad de preparación y potencia.",
        799900,
        7,
        "https://images.unsplash.com/photo-1657704358775-ed705c7388d2?w=900&q=80",
    ),
    (
        "Pelotas Pro Doble Punto x3",
        "Dunlop",
        "squash",
        "Pelotas",
        "todos",
        "Pack de pelotas para jugadores avanzados y competencia.",
        54900,
        32,
        "https://images.unsplash.com/photo-1599474924187-334a4ae5bd3c?w=900&q=80",
    ),
    (
        "Gafas Protectoras Impulse",
        "HEAD",
        "squash",
        "Protección ocular",
        "todos",
        "Protección liviana para entrenamiento y competencia de squash.",
        119900,
        16,
        "https://images.unsplash.com/photo-1577803645773-f96470509666?w=900&q=80",
    ),
]

PAYMENT_METHODS = [
    ("card", "Tarjeta credito o debito", 1),
    ("pse", "PSE / transferencia bancaria", 1),
    ("cash", "Pago contra entrega", 1),
    ("wallet", "Billetera digital", 1),
    ("demo", "Pago de prueba", 1),
]

DEFAULT_GALLERY_IMAGES = {
    "tenis": [
        "https://images.unsplash.com/photo-1622279457486-62dcc4a431d6?w=1200&q=85",
        "https://images.unsplash.com/photo-1595435934249-5df7ed86e1c0?w=1200&q=85",
        "https://images.unsplash.com/photo-1554068865-24cecd4e34b8?w=1200&q=85",
        "https://images.unsplash.com/photo-1617083934555-ac7d4d58ce51?w=1200&q=85",
    ],
    "golf": [
        "https://images.unsplash.com/photo-1535131749006-b7f58c99034b?w=1200&q=85",
        "https://images.unsplash.com/photo-1587174486073-ae5e5cff23aa?w=1200&q=85",
        "https://images.unsplash.com/photo-1592919505780-303950717480?w=1200&q=85",
        "https://images.unsplash.com/photo-1593111774240-d529f12cf4bb?w=1200&q=85",
    ],
    "squash": [
        "https://images.unsplash.com/photo-1657704358775-ed705c7388d2?w=1200&q=85",
        "https://images.unsplash.com/photo-1599474924187-334a4ae5bd3c?w=1200&q=85",
        "https://images.unsplash.com/photo-1577803645773-f96470509666?w=1200&q=85",
        "https://images.unsplash.com/photo-1544287757-a8ab80d90b60?w=1200&q=85",
    ],
}


def build_default_gallery(sport: str, primary_image: str) -> list[str]:
    images: list[str] = []
    for candidate in [primary_image, *DEFAULT_GALLERY_IMAGES.get(sport, [])]:
        candidate = (candidate or "").strip()
        if candidate and candidate not in images:
            images.append(candidate)
        if len(images) == 4:
            break
    while len(images) < 4:
        images.append("https://placehold.co/1200x900?text=SportZone")
    return images


def allowed_image_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


mysql = MySQL()

def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=SECRET_KEY,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=SESSION_COOKIE_SECURE,
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,
        MYSQL_HOST=MYSQL_HOST,
        MYSQL_PORT=MYSQL_PORT,
        MYSQL_USER=MYSQL_USER,
        MYSQL_PASSWORD=MYSQL_PASSWORD,
        MYSQL_DB=MYSQL_DB,
        MYSQL_CHARSET="utf8mb4",
    )

    if test_config:
        app.config.update(test_config)

    mysql.init_app(app)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def get_db() -> DatabaseAdapter:
        if "db" not in g:
            g.db = DatabaseAdapter(mysql.connection, app.config)
        return g.db

    def close_db(_: BaseException | None = None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    app.teardown_appcontext(close_db)

    def init_db(seed: bool = True) -> None:
        db = get_db()
        # Importa schema_mysql.sql en phpMyAdmin antes de iniciar.
        # La inicializacion solo carga registros faltantes.
        if seed and next(iter(db.execute("SELECT COUNT(*) FROM products").fetchone().values())) == 0:
            db.executemany(
                """
                INSERT INTO products
                    (name, brand, sport, product_type, audience, description, price, stock, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                SEED_PRODUCTS,
            )

        # Catalogo de metodos de pago. INSERT IGNORE conserva los cambios existentes.
        db.executemany(
            "INSERT IGNORE INTO payment_methods (code, name, active) VALUES (?, ?, ?)",
            PAYMENT_METHODS,
        )

        # Migra pedidos anteriores al nuevo modelo de pagos usando el metodo demostrativo.
        demo_method = db.execute(
            "SELECT id FROM payment_methods WHERE code = 'demo'"
        ).fetchone()
        if demo_method:
            db.execute(
                """
                INSERT IGNORE INTO payments
                    (order_id, payment_method_id, amount, status, transaction_reference, paid_at)
                SELECT id, ?, total, 'approved', CONCAT('LEGACY-', id), created_at
                FROM orders
                """,
                (demo_method["id"],),
            )

        # Crea un movimiento inicial para productos que aun no tienen kardex.
        db.execute(
            """
            INSERT INTO inventory_movements
                (product_id, movement_type, quantity_change, stock_before, stock_after, reason)
            SELECT p.id, 'initial', p.stock, 0, p.stock,
                   'Saldo inicial creado durante la migracion analitica'
            FROM products AS p
            WHERE NOT EXISTS (
                SELECT 1 FROM inventory_movements AS im WHERE im.product_id = p.id
            )
            """
        )

        # Migración no destructiva: crea una galería mínima de cuatro imágenes
        # para productos existentes y nuevos sin borrar usuarios, pedidos o inventario.
        products_without_gallery = db.execute(
            """
            SELECT products.*
            FROM products
            LEFT JOIN product_images ON product_images.product_id = products.id
            GROUP BY products.id
            HAVING COUNT(product_images.id) < 4
            """
        ).fetchall()
        for product in products_without_gallery:
            existing = db.execute(
                "SELECT image_url FROM product_images WHERE product_id = ? ORDER BY position, id",
                (product["id"],),
            ).fetchall()
            images = [row["image_url"] for row in existing]
            defaults = build_default_gallery(product["sport"], product["image_url"])
            for candidate in defaults:
                if candidate not in images:
                    images.append(candidate)
                if len(images) == 4:
                    break
            db.execute("DELETE FROM product_images WHERE product_id = ?", (product["id"],))
            db.executemany(
                "INSERT INTO product_images (product_id, image_url, position) VALUES (?, ?, ?)",
                [(product["id"], image_url, position) for position, image_url in enumerate(images[:4], 1)],
            )
            db.execute(
                "UPDATE products SET image_url = ? WHERE id = ?",
                (images[0], product["id"]),
            )
        db.commit()

    app.get_db = get_db  # type: ignore[attr-defined]
    app.init_db = init_db  # type: ignore[attr-defined]

    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Crea la base de datos y carga el catálogo inicial."""
        init_db(seed=True)
        click.echo("Base de datos inicializada.")

    @app.cli.command("create-admin")
    @click.option("--name", prompt="Nombre del administrador")
    @click.option("--email", prompt="Correo del administrador")
    @click.password_option(confirmation_prompt=True)
    def create_admin_command(name: str, email: str, password: str) -> None:
        """Crea o actualiza una cuenta con rol administrador."""
        email = email.strip().lower()
        if len(password) < 8:
            raise click.ClickException("La contraseña debe tener al menos 8 caracteres.")
        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        password_hash = generate_password_hash(password)
        if existing:
            db.execute(
                "UPDATE users SET name = ?, password_hash = ?, role = 'admin' WHERE id = ?",
                (name.strip(), password_hash, existing["id"]),
            )
        else:
            db.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
                (name.strip(), email, password_hash),
            )
        db.commit()
        click.echo(f"Administrador listo: {email}")

    def login_required(view: F) -> F:
        @wraps(view)
        def wrapped_view(*args: Any, **kwargs: Any) -> Any:
            if g.user is None:
                flash("Debes iniciar sesión para continuar.", "warning")
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)

        return wrapped_view  # type: ignore[return-value]

    def admin_required(view: F) -> F:
        @wraps(view)
        @login_required
        def wrapped_view(*args: Any, **kwargs: Any) -> Any:
            if g.user["role"] != "admin":
                abort(403)
            return view(*args, **kwargs)

        return wrapped_view  # type: ignore[return-value]

    def csrf_token() -> str:
        token = session.get("_csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["_csrf_token"] = token
        return token

    @app.before_request
    def load_logged_in_user_and_validate_csrf() -> None:
        user_id = session.get("user_id")
        g.user = (
            get_db().execute(
                "SELECT id, name, email, role, created_at FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if user_id
            else None
        )

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
            if not supplied or not secrets.compare_digest(supplied, csrf_token()):
                abort(400, "Token CSRF inválido o ausente.")

    @app.after_request
    def set_security_headers(response: Any) -> Any:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self'; object-src 'none'; base-uri 'self'"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store" if request.path.startswith(("/admin", "/mis-pedidos", "/pagar")) else response.headers.get("Cache-Control", "")
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.context_processor
    def inject_helpers() -> dict[str, Any]:
        return {"csrf_token": csrf_token, "format_cop": format_cop}

    @app.route("/")
    def index() -> str:
        sport = request.args.get("sport", "").strip().lower()
        query = request.args.get("q", "").strip()
        sql = "SELECT * FROM products WHERE active = 1"
        params: list[Any] = []
        if sport in {"tenis", "golf", "squash"}:
            sql += " AND sport = ?"
            params.append(sport)
        if query:
            sql += " AND (name LIKE ? OR brand LIKE ? OR product_type LIKE ?)"
            term = f"%{query}%"
            params.extend([term, term, term])
        sql += " ORDER BY sport, id"
        products = get_db().execute(sql, params).fetchall()
        return render_template("index.html", products=products, selected_sport=sport, query=query)

    @app.route("/productos/<int:product_id>")
    def product_detail(product_id: int) -> str:
        db = get_db()
        if g.user and g.user["role"] == "admin":
            product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        else:
            product = db.execute(
                "SELECT * FROM products WHERE id = ? AND active = 1", (product_id,)
            ).fetchone()
        if product is None:
            abort(404)
        images = db.execute(
            "SELECT image_url, position FROM product_images WHERE product_id = ? ORDER BY position, id",
            (product_id,),
        ).fetchall()
        related = db.execute(
            """
            SELECT * FROM products
            WHERE sport = ? AND id <> ? AND active = 1
            ORDER BY id DESC LIMIT 4
            """,
            (product["sport"], product_id),
        ).fetchall()
        return render_template(
            "product_detail.html", product=product, images=images, related=related
        )

    @app.route("/registro", methods=("GET", "POST"))
    def register() -> str | Any:
        if g.user:
            return redirect(url_for("index"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            password_confirm = request.form.get("password_confirm", "")
            error = None
            if len(name) < 2:
                error = "Escribe un nombre válido."
            elif "@" not in email or "." not in email.rsplit("@", 1)[-1]:
                error = "Escribe un correo electrónico válido."
            elif len(password) < 8:
                error = "La contraseña debe tener al menos 8 caracteres."
            elif password != password_confirm:
                error = "Las contraseñas no coinciden."

            if error is None:
                try:
                    db = get_db()
                    db.execute(
                        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'user')",
                        (name, email, generate_password_hash(password)),
                    )
                    db.commit()
                except IntegrityError:
                    error = "Ya existe una cuenta con ese correo."
                else:
                    flash("Cuenta creada. Ya puedes iniciar sesión.", "success")
                    return redirect(url_for("login"))
            flash(error, "danger")
        return render_template("register.html")

    login_attempts = {}

    @app.route("/ingresar", methods=("GET", "POST"))
    def login() -> str | Any:
        if g.user:
            return redirect(url_for("index"))
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()[:254]
            password = request.form.get("password", "")
            from time import monotonic
            key = (request.remote_addr or "unknown", email)
            recent = [t for t in login_attempts.get(key, []) if monotonic() - t < 900]
            if len(recent) >= 8:
                abort(429)
            login_attempts[key] = recent
            user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if user is None or not check_password_hash(user["password_hash"], password):
                login_attempts[key].append(monotonic())
                flash("Correo o contraseña incorrectos.", "danger")
            else:
                login_attempts.pop(key, None)
                session.clear()
                session["user_id"] = user["id"]
                csrf_token()
                flash(f"Bienvenido, {user['name']}.", "success")
                target = request.args.get("next")
                return redirect(target if target and target.startswith("/") and not target.startswith("//") and not target.startswith("/\\") else url_for("index"))
        return render_template("login.html")

    @app.post("/salir")
    def logout() -> Any:
        session.clear()
        flash("Sesión cerrada correctamente.", "info")
        return redirect(url_for("index"))

    def get_cart() -> dict[str, int]:
        raw = session.get("cart", {})
        return {str(k): max(0, int(v)) for k, v in raw.items() if int(v) > 0}

    def cart_details() -> tuple[list[dict[str, Any]], int, int, int]:
        cart = get_cart()
        if not cart:
            return [], 0, 0, 0
        ids = [int(product_id) for product_id in cart]
        placeholders = ",".join("?" for _ in ids)
        rows = get_db().execute(
            f"SELECT * FROM products WHERE id IN ({placeholders})", ids
        ).fetchall()
        items: list[dict[str, Any]] = []
        subtotal = 0
        for row in rows:
            quantity = cart.get(str(row["id"]), 0)
            line_total = row["price"] * quantity
            subtotal += line_total
            items.append({"product": row, "quantity": quantity, "line_total": line_total})
        shipping = 0 if subtotal == 0 or subtotal >= 250000 else 18000
        return items, subtotal, shipping, subtotal + shipping

    @app.route("/carrito")
    def cart_page() -> str:
        items, subtotal, shipping, total = cart_details()
        return render_template(
            "cart.html", items=items, subtotal=subtotal, shipping=shipping, total=total
        )

    @app.post("/api/carrito/agregar")
    def cart_add() -> Any:
        data = request.get_json(silent=True) or {}
        try:
            product_id = int(data.get("product_id", 0))
            quantity = max(1, min(20, int(data.get("quantity", 1))))
        except (TypeError, ValueError):
            return jsonify(ok=False, message="Datos inválidos."), 400
        product = get_db().execute(
            "SELECT id, name, stock, active FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if product is None or not product["active"]:
            return jsonify(ok=False, message="Producto no disponible."), 404
        cart = get_cart()
        new_quantity = cart.get(str(product_id), 0) + quantity
        if new_quantity > product["stock"]:
            return jsonify(ok=False, message="No hay suficiente inventario."), 409
        cart[str(product_id)] = new_quantity
        session["cart"] = cart
        session.modified = True
        return jsonify(
            ok=True,
            message=f"{product['name']} fue añadido al carrito.",
            cart_count=sum(cart.values()),
        )

    @app.post("/api/carrito/actualizar")
    def cart_update() -> Any:
        data = request.get_json(silent=True) or {}
        try:
            product_id = int(data.get("product_id", 0))
            quantity = max(0, min(20, int(data.get("quantity", 0))))
        except (TypeError, ValueError):
            return jsonify(ok=False, message="Datos inválidos."), 400
        product = get_db().execute(
            "SELECT id, stock FROM products WHERE id = ? AND active = 1", (product_id,)
        ).fetchone()
        if product is None:
            return jsonify(ok=False, message="Producto no disponible."), 404
        if quantity > product["stock"]:
            return jsonify(ok=False, message="La cantidad supera el inventario."), 409
        cart = get_cart()
        if quantity == 0:
            cart.pop(str(product_id), None)
        else:
            cart[str(product_id)] = quantity
        session["cart"] = cart
        session.modified = True
        return jsonify(ok=True, cart_count=sum(cart.values()))

    @app.route("/pagar", methods=("GET", "POST"))
    @login_required
    def checkout() -> str | Any:
        items, subtotal, shipping, total = cart_details()
        if not items:
            flash("El carrito está vacío.", "warning")
            return redirect(url_for("cart_page"))

        db = get_db()
        payment_methods = db.execute(
            "SELECT id, code, name FROM payment_methods WHERE active = 1 ORDER BY id"
        ).fetchall()

        if request.method == "POST":
            # La plantilla envia payment_method_id. Como respaldo, se usa el
            # metodo demostrativo si un navegador antiguo no envia el campo.
            raw_payment_method = request.form.get("payment_method_id", "").strip()
            if raw_payment_method:
                try:
                    payment_method_id = int(raw_payment_method)
                except ValueError:
                    payment_method_id = 0
                selected_method = db.execute(
                    "SELECT id, code, name FROM payment_methods WHERE id = ? AND active = 1",
                    (payment_method_id,),
                ).fetchone()
            else:
                selected_method = db.execute(
                    "SELECT id, code, name FROM payment_methods WHERE code = 'demo' AND active = 1"
                ).fetchone()

            if selected_method is None:
                flash("Selecciona un método de pago válido.", "danger")
                return redirect(url_for("checkout"))

            order_id: int | None = None
            payment_method_name = str(selected_method["name"])
            try:
                db.commit()
                db.execute("START TRANSACTION")
                cart = get_cart()
                validated_items: list[tuple[dict, int]] = []
                product_subtotal = 0

                for product_id, quantity in cart.items():
                    product = db.execute(
                        "SELECT * FROM products WHERE id = ? AND active = 1 FOR UPDATE",
                        (int(product_id),),
                    ).fetchone()
                    if product is None:
                        raise ValueError("Uno de los productos ya no está disponible.")
                    if quantity > product["stock"]:
                        raise ValueError(
                            f"Stock insuficiente para {product['name']}. "
                            f"Disponible: {product['stock']}."
                        )
                    validated_items.append((product, quantity))
                    product_subtotal += int(product["price"]) * int(quantity)

                final_shipping = 0 if product_subtotal >= 250000 else 18000
                final_total = product_subtotal + final_shipping

                cursor = db.execute(
                    "INSERT INTO orders (user_id, total, status) VALUES (?, ?, 'pagado_prueba')",
                    (g.user["id"], final_total),
                )
                order_id = int(cursor.lastrowid)
                transaction_reference = f"DEMO-{order_id}-{secrets.token_hex(4).upper()}"

                db.execute(
                    """
                    INSERT INTO payments
                        (order_id, payment_method_id, amount, status, transaction_reference)
                    VALUES (?, ?, ?, 'approved', ?)
                    """,
                    (
                        order_id,
                        int(selected_method["id"]),
                        final_total,
                        transaction_reference,
                    ),
                )

                for product, quantity in validated_items:
                    stock_before = int(product["stock"])
                    stock_after = stock_before - int(quantity)
                    updated = db.execute(
                        "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
                        (quantity, product["id"], quantity),
                    )
                    if updated.rowcount != 1:
                        raise ValueError(
                            f"El inventario de {product['name']} cambió. Intenta nuevamente."
                        )

                    db.execute(
                        """
                        INSERT INTO order_items
                            (order_id, product_id, product_name, unit_price, quantity)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            order_id,
                            product["id"],
                            product["name"],
                            product["price"],
                            quantity,
                        ),
                    )
                    db.execute(
                        """
                        INSERT INTO inventory_movements
                            (product_id, user_id, order_id, movement_type, quantity_change,
                             stock_before, stock_after, reason)
                        VALUES (?, ?, ?, 'sale', ?, ?, ?, ?)
                        """,
                        (
                            product["id"],
                            g.user["id"],
                            order_id,
                            -int(quantity),
                            stock_before,
                            stock_after,
                            f"Venta asociada al pedido #{order_id}",
                        ),
                    )

                # Todo el pedido, el pago, el detalle y el stock se confirman juntos.
                db.commit()
            except (DatabaseError, ValueError) as exc:
                db.rollback()
                app.logger.exception("No fue posible confirmar el checkout")
                flash(str(exc) if isinstance(exc, ValueError) else "No se pudo procesar la compra.", "danger")
                return redirect(url_for("cart_page"))
            except Exception:
                # Evita dejar una transaccion abierta ante un error inesperado.
                db.rollback()
                app.logger.exception("Error inesperado durante el checkout")
                flash(
                    "No fue posible completar la compra. El inventario no fue modificado.",
                    "danger",
                )
                return redirect(url_for("cart_page"))

            # Estas operaciones se ejecutan solo despues de un commit correcto.
            session.pop("cart", None)
            session.modified = True
            flash(
                f"Pago aprobado con {payment_method_name}. Pedido #{order_id} creado.",
                "success",
            )
            return redirect(url_for("payment_success", order_id=order_id))

        return render_template(
            "checkout.html",
            items=items,
            subtotal=subtotal,
            shipping=shipping,
            total=total,
            payment_methods=payment_methods,
        )

    @app.route("/pago/exitoso/<int:order_id>")
    @login_required
    def payment_success(order_id: int) -> str:
        db = get_db()
        order = db.execute(
            "SELECT * FROM orders WHERE id = ? AND user_id = ?",
            (order_id, g.user["id"]),
        ).fetchone()
        if order is None:
            abort(404)

        payment = db.execute(
            """
            SELECT payments.*, payment_methods.name AS method_name
            FROM payments
            LEFT JOIN payment_methods
                ON payment_methods.id = payments.payment_method_id
            WHERE payments.order_id = ?
            """,
            (order_id,),
        ).fetchone()
        lines = db.execute(
            "SELECT * FROM order_items WHERE order_id = ? ORDER BY id",
            (order_id,),
        ).fetchall()
        return render_template(
            "payment_success.html",
            order=order,
            payment=payment,
            items=lines,
        )

    @app.route("/mis-pedidos")
    @login_required
    def orders() -> str:
        db = get_db()
        order_rows = db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (g.user["id"],)
        ).fetchall()
        order_data = []
        for order in order_rows:
            lines = db.execute(
                "SELECT * FROM order_items WHERE order_id = ? ORDER BY id", (order["id"],)
            ).fetchall()
            payment = db.execute(
                """
                SELECT payments.*, payment_methods.name AS method_name
                FROM payments
                JOIN payment_methods ON payment_methods.id = payments.payment_method_id
                WHERE payments.order_id = ?
                """,
                (order["id"],),
            ).fetchone()
            order_data.append({"order": order, "items": lines, "payment": payment})
        return render_template("orders.html", orders=order_data)

    @app.route("/admin")
    @admin_required
    def admin_dashboard() -> str:
        db = get_db()
        products = db.execute("SELECT * FROM products ORDER BY sport, name").fetchall()
        users = db.execute(
            "SELECT id, name, email, role, created_at FROM users ORDER BY id DESC"
        ).fetchall()
        orders_rows = db.execute(
            """
            SELECT orders.*, users.name AS customer_name, users.email AS customer_email,
                   COALESCE(payment_methods.name, 'Sin registrar') AS payment_method
            FROM orders
            JOIN users ON users.id = orders.user_id
            LEFT JOIN payments ON payments.order_id = orders.id
            LEFT JOIN payment_methods ON payment_methods.id = payments.payment_method_id
            ORDER BY orders.id DESC LIMIT 30
            """
        ).fetchall()
        stats = {
            "products": next(iter(db.execute("SELECT COUNT(*) FROM products").fetchone().values())),
            "users": next(iter(db.execute("SELECT COUNT(*) FROM users").fetchone().values())),
            "orders": next(iter(db.execute("SELECT COUNT(*) FROM orders").fetchone().values())),
            "sales": next(iter(db.execute("SELECT COALESCE(SUM(total), 0) FROM orders").fetchone().values())),
        }
        return render_template(
            "admin/dashboard.html",
            products=products,
            users=users,
            orders=orders_rows,
            stats=stats,
        )

    def save_uploaded_product_image(file_storage: Any) -> tuple[str | None, str | None]:
        """Valida, orienta y optimiza una imagen sin recortarla.

        Todas las imágenes locales se guardan como WebP con un máximo de
        1800 x 1800 píxeles. La proporción original se conserva y el ajuste
        visual final se realiza con object-fit: contain en las plantillas.
        """
        if not file_storage or not file_storage.filename:
            return None, None
        if not allowed_image_file(file_storage.filename):
            return None, "Las imágenes deben ser JPG, JPEG, PNG o WebP."

        # Evita procesar imágenes desproporcionadamente grandes.
        Image.MAX_IMAGE_PIXELS = 30_000_000
        filename = f"{secrets.token_hex(12)}.webp"
        destination = UPLOAD_DIR / filename

        try:
            file_storage.stream.seek(0)
            with Image.open(file_storage.stream) as source:
                # Corrige imágenes tomadas con celular que traen rotación EXIF.
                image = ImageOps.exif_transpose(source)
                image.load()

                if image.width < 120 or image.height < 120:
                    return None, "La imagen es demasiado pequeña. Usa mínimo 120 x 120 píxeles."

                # Mantiene transparencia cuando existe; de lo contrario usa RGB.
                has_alpha = image.mode in {"RGBA", "LA"} or "transparency" in image.info
                image = image.convert("RGBA" if has_alpha else "RGB")
                image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
                image.save(
                    destination,
                    format="WEBP",
                    quality=88,
                    method=6,
                )
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            destination.unlink(missing_ok=True)
            return None, "No fue posible procesar la imagen. Verifica que el archivo no esté dañado."

        return url_for("static", filename=f"uploads/products/{filename}"), None

    def collect_product_images(existing_images: list[str] | None = None) -> tuple[list[str] | None, str | None]:
        existing_images = existing_images or []
        resolved: list[str] = []
        for position in range(1, 5):
            upload = request.files.get(f"image_file_{position}")
            typed_url = request.form.get(f"image_url_{position}", "").strip()
            current = existing_images[position - 1] if position <= len(existing_images) else ""
            if upload and upload.filename:
                saved_url, error = save_uploaded_product_image(upload)
                if error:
                    return None, error
                image_url = saved_url or ""
            elif typed_url:
                if not (typed_url.startswith("https://") or typed_url.startswith("/static/uploads/products/")) or any(ch in typed_url for ch in ('"', "'", "<", ">")):
                    return None, "La imagen debe utilizar una URL HTTPS válida o una ruta local autorizada."
                image_url = typed_url
            else:
                image_url = current
            if not image_url:
                return None, "Cada producto debe tener cuatro imágenes. Completa los cuatro espacios."
            resolved.append(image_url)
        return resolved, None

    def replace_product_images(db: DatabaseAdapter, product_id: int, images: list[str]) -> None:
        db.execute("DELETE FROM product_images WHERE product_id = ?", (product_id,))
        db.executemany(
            "INSERT INTO product_images (product_id, image_url, position) VALUES (?, ?, ?)",
            [(product_id, image_url, position) for position, image_url in enumerate(images, 1)],
        )
        db.execute("UPDATE products SET image_url = ? WHERE id = ?", (images[0], product_id))

    @app.route("/admin/productos/nuevo", methods=("GET", "POST"))
    @admin_required
    def admin_product_new() -> str | Any:
        if request.method == "POST":
            product_data, error = validate_product_form(request.form)
            images, image_error = collect_product_images()
            error = error or image_error
            if error:
                flash(error, "danger")
            else:
                db = get_db()
                cursor = db.execute(
                    """
                    INSERT INTO products
                        (name, brand, sport, product_type, audience, description, price, stock, image_url, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (*product_data[:-1], images[0], product_data[-1]),
                )
                product_id = int(cursor.lastrowid)
                replace_product_images(db, product_id, images)
                initial_stock = int(product_data[7])
                db.execute(
                    """
                    INSERT INTO inventory_movements
                        (product_id, user_id, movement_type, quantity_change,
                         stock_before, stock_after, reason)
                    VALUES (?, ?, 'initial', ?, 0, ?, 'Producto creado por administrador')
                    """,
                    (product_id, g.user["id"], initial_stock, initial_stock),
                )
                db.commit()
                flash("Producto creado correctamente con cuatro imágenes.", "success")
                return redirect(url_for("admin_dashboard"))
        return render_template("admin/product_form.html", product=None, product_images=[])

    @app.route("/admin/productos/<int:product_id>/editar", methods=("GET", "POST"))
    @admin_required
    def admin_product_edit(product_id: int) -> str | Any:
        db = get_db()
        product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if product is None:
            abort(404)
        image_rows = db.execute(
            "SELECT image_url FROM product_images WHERE product_id = ? ORDER BY position, id",
            (product_id,),
        ).fetchall()
        existing_images = [row["image_url"] for row in image_rows]
        if request.method == "POST":
            product_data, error = validate_product_form(request.form)
            images, image_error = collect_product_images(existing_images)
            error = error or image_error
            if error:
                flash(error, "danger")
            else:
                old_stock = int(product["stock"])
                new_stock = int(product_data[7])
                db.execute(
                    """
                    UPDATE products SET
                        name = ?, brand = ?, sport = ?, product_type = ?, audience = ?,
                        description = ?, price = ?, stock = ?, image_url = ?, active = ?
                    WHERE id = ?
                    """,
                    (*product_data[:-1], images[0], product_data[-1], product_id),
                )
                replace_product_images(db, product_id, images)
                if new_stock != old_stock:
                    db.execute(
                        """
                        INSERT INTO inventory_movements
                            (product_id, user_id, movement_type, quantity_change,
                             stock_before, stock_after, reason)
                        VALUES (?, ?, 'adjustment', ?, ?, ?, 'Edicion completa del producto')
                        """,
                        (
                            product_id,
                            g.user["id"],
                            new_stock - old_stock,
                            old_stock,
                            new_stock,
                        ),
                    )
                db.commit()
                flash("Producto, stock e imágenes actualizados.", "success")
                return redirect(url_for("admin_dashboard"))
        return render_template(
            "admin/product_form.html", product=product, product_images=existing_images
        )

    @app.post("/admin/productos/<int:product_id>/stock")
    @admin_required
    def admin_product_stock(product_id: int) -> Any:
        try:
            stock = int(request.form.get("stock", ""))
        except ValueError:
            flash("El stock debe ser un número entero.", "danger")
            return redirect(url_for("admin_dashboard"))
        if stock < 0:
            flash("El stock no puede ser negativo.", "danger")
            return redirect(url_for("admin_dashboard"))
        db = get_db()
        product = db.execute(
            "SELECT id, name, stock FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if product is None:
            abort(404)
        old_stock = int(product["stock"])
        updated = db.execute("UPDATE products SET stock = ? WHERE id = ?", (stock, product_id))
        if updated.rowcount != 1:
            abort(404)
        if stock != old_stock:
            db.execute(
                """
                INSERT INTO inventory_movements
                    (product_id, user_id, movement_type, quantity_change,
                     stock_before, stock_after, reason)
                VALUES (?, ?, 'adjustment', ?, ?, ?, 'Ajuste rapido desde administracion')
                """,
                (product_id, g.user["id"], stock - old_stock, old_stock, stock),
            )
        db.commit()
        flash(f"Stock del producto #{product_id} actualizado a {stock} unidades.", "success")
        return redirect(url_for("admin_dashboard"))

    def read_mysql_frame(sql: str, db: DatabaseAdapter) -> pd.DataFrame:
        from sqlalchemy import text
        return pd.read_sql_query(text(sql), db.sqlalchemy_engine)

    def load_analytics_frames() -> dict[str, pd.DataFrame]:
        """Lee las tablas de MySQL con pandas y devuelve DataFrames para analizar."""
        db = get_db()
        orders_df = read_mysql_frame(
            """
            SELECT o.id AS order_id, o.user_id, o.total, o.status AS order_status,
                   o.created_at, u.name AS customer_name, u.email AS customer_email,
                   COALESCE(pm.id, 0) AS payment_method_id,
                   COALESCE(pm.name, 'Sin registrar') AS payment_method,
                   COALESCE(pay.status, 'approved') AS payment_status,
                   COALESCE(pay.transaction_reference, CONCAT('LEGACY-', o.id)) AS transaction_reference
            FROM orders AS o
            JOIN users AS u ON u.id = o.user_id
            LEFT JOIN payments AS pay ON pay.order_id = o.id
            LEFT JOIN payment_methods AS pm ON pm.id = pay.payment_method_id
            """,
            db,
        )
        items_df = read_mysql_frame(
            """
            SELECT oi.id AS item_id, oi.order_id, oi.product_id, oi.product_name,
                   oi.unit_price, oi.quantity,
                   (oi.unit_price * oi.quantity) AS line_total,
                   o.created_at, o.user_id,
                   COALESCE(p.sport, 'sin_categoria') AS sport,
                   COALESCE(p.brand, 'Sin marca') AS brand,
                   COALESCE(pm.id, 0) AS payment_method_id,
                   COALESCE(pm.name, 'Sin registrar') AS payment_method,
                   COALESCE(pay.status, 'approved') AS payment_status
            FROM order_items AS oi
            JOIN orders AS o ON o.id = oi.order_id
            LEFT JOIN products AS p ON p.id = oi.product_id
            LEFT JOIN payments AS pay ON pay.order_id = o.id
            LEFT JOIN payment_methods AS pm ON pm.id = pay.payment_method_id
            """,
            db,
        )
        stock_df = read_mysql_frame(
            """
            SELECT id AS product_id, name, brand, sport, product_type, price, stock,
                   active, (price * stock) AS inventory_value
            FROM products
            ORDER BY stock ASC, name
            """,
            db,
        )
        payments_df = read_mysql_frame(
            """
            SELECT pay.id AS payment_id, pay.order_id, pay.amount, pay.status,
                   pay.transaction_reference, pay.paid_at,
                   pm.id AS payment_method_id, pm.name AS payment_method
            FROM payments AS pay
            JOIN payment_methods AS pm ON pm.id = pay.payment_method_id
            ORDER BY pay.paid_at DESC
            """,
            db,
        )
        movements_df = read_mysql_frame(
            """
            SELECT im.id, im.product_id, p.name AS product_name, p.sport,
                   im.movement_type, im.quantity_change, im.stock_before,
                   im.stock_after, im.reason, im.created_at,
                   COALESCE(u.name, 'Sistema') AS responsible,
                   im.order_id
            FROM inventory_movements AS im
            JOIN products AS p ON p.id = im.product_id
            LEFT JOIN users AS u ON u.id = im.user_id
            ORDER BY im.created_at DESC, im.id DESC
            """,
            db,
        )
        for frame, date_column in (
            (orders_df, "created_at"),
            (items_df, "created_at"),
            (payments_df, "paid_at"),
            (movements_df, "created_at"),
        ):
            if not frame.empty:
                frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce")
        return {
            "orders": orders_df,
            "items": items_df,
            "stock": stock_df,
            "payments": payments_df,
            "movements": movements_df,
        }

    def apply_analytics_filters(
        frames: dict[str, pd.DataFrame],
        start_date: str,
        end_date: str,
        sport: str,
        payment_method_id: int,
    ) -> dict[str, pd.DataFrame]:
        orders_df = frames["orders"].copy()
        items_df = frames["items"].copy()
        stock_df = frames["stock"].copy()
        payments_df = frames["payments"].copy()
        movements_df = frames["movements"].copy()

        start_ts = pd.to_datetime(start_date, errors="coerce") if start_date else None
        end_ts = pd.to_datetime(end_date, errors="coerce") if end_date else None
        if start_ts is not None and not pd.isna(start_ts):
            orders_df = orders_df[orders_df["created_at"] >= start_ts]
            items_df = items_df[items_df["created_at"] >= start_ts]
            payments_df = payments_df[payments_df["paid_at"] >= start_ts]
            movements_df = movements_df[movements_df["created_at"] >= start_ts]
        if end_ts is not None and not pd.isna(end_ts):
            inclusive_end = end_ts + pd.Timedelta(days=1)
            orders_df = orders_df[orders_df["created_at"] < inclusive_end]
            items_df = items_df[items_df["created_at"] < inclusive_end]
            payments_df = payments_df[payments_df["paid_at"] < inclusive_end]
            movements_df = movements_df[movements_df["created_at"] < inclusive_end]
        if sport in {"tenis", "golf", "squash"}:
            items_df = items_df[items_df["sport"] == sport]
            stock_df = stock_df[stock_df["sport"] == sport]
            movements_df = movements_df[movements_df["sport"] == sport]
            valid_order_ids = set(items_df["order_id"].tolist())
            orders_df = orders_df[orders_df["order_id"].isin(valid_order_ids)]
            payments_df = payments_df[payments_df["order_id"].isin(valid_order_ids)]
        if payment_method_id > 0:
            orders_df = orders_df[orders_df["payment_method_id"] == payment_method_id]
            items_df = items_df[items_df["payment_method_id"] == payment_method_id]
            payments_df = payments_df[payments_df["payment_method_id"] == payment_method_id]

        approved_orders = set(
            orders_df.loc[orders_df["payment_status"] == "approved", "order_id"].tolist()
        )
        items_df = items_df[items_df["order_id"].isin(approved_orders)]
        orders_df = orders_df[orders_df["order_id"].isin(approved_orders)]
        payments_df = payments_df[payments_df["status"] == "approved"]
        return {
            "orders": orders_df,
            "items": items_df,
            "stock": stock_df,
            "payments": payments_df,
            "movements": movements_df,
        }

    def build_dashboard_analysis(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
        orders_df = frames["orders"]
        items_df = frames["items"]
        stock_df = frames["stock"]
        payments_df = frames["payments"]
        movements_df = frames["movements"]

        sales_total = int(items_df["line_total"].sum()) if not items_df.empty else 0
        units_sold = int(items_df["quantity"].sum()) if not items_df.empty else 0
        order_count = int(items_df["order_id"].nunique()) if not items_df.empty else 0
        average_ticket = int(round(sales_total / order_count)) if order_count else 0
        inventory_value = int(stock_df["inventory_value"].sum()) if not stock_df.empty else 0
        low_stock_count = int((stock_df["stock"] <= 5).sum()) if not stock_df.empty else 0

        if not items_df.empty:
            daily = (
                items_df.assign(sale_date=items_df["created_at"].dt.strftime("%Y-%m-%d"))
                .groupby("sale_date", as_index=False)
                .agg(sales=("line_total", "sum"), orders=("order_id", "nunique"))
                .sort_values("sale_date")
            )
            by_sport = (
                items_df.groupby("sport", as_index=False)["line_total"]
                .sum()
                .sort_values("line_total", ascending=False)
            )
            top_products = (
                items_df.groupby(["product_id", "product_name"], dropna=False, as_index=False)
                .agg(units=("quantity", "sum"), revenue=("line_total", "sum"))
                .sort_values(["revenue", "units"], ascending=False)
                .head(10)
            )
            by_payment = (
                items_df.groupby("payment_method", as_index=False)["line_total"]
                .sum()
                .sort_values("line_total", ascending=False)
            )
        else:
            daily = pd.DataFrame(columns=["sale_date", "sales", "orders"])
            by_sport = pd.DataFrame(columns=["sport", "line_total"])
            top_products = pd.DataFrame(
                columns=["product_id", "product_name", "units", "revenue"]
            )
            by_payment = pd.DataFrame(columns=["payment_method", "line_total"])

        stock_table = stock_df.sort_values(["stock", "name"]).head(12).copy()
        recent_payments = payments_df.sort_values("paid_at", ascending=False).head(10).copy()
        recent_movements = movements_df.sort_values(
            ["created_at", "id"], ascending=False
        ).head(12).copy()

        for frame, column in (
            (recent_payments, "paid_at"),
            (recent_movements, "created_at"),
        ):
            if not frame.empty:
                frame[column] = frame[column].dt.strftime("%Y-%m-%d %H:%M")

        return {
            "kpis": {
                "sales_total": sales_total,
                "units_sold": units_sold,
                "order_count": order_count,
                "average_ticket": average_ticket,
                "inventory_value": inventory_value,
                "low_stock_count": low_stock_count,
            },
            "charts": {
                "daily": {
                    "labels": daily["sale_date"].tolist(),
                    "sales": [int(value) for value in daily["sales"].tolist()],
                    "orders": [int(value) for value in daily["orders"].tolist()],
                },
                "sport": {
                    "labels": by_sport["sport"].str.title().tolist(),
                    "values": [int(value) for value in by_sport["line_total"].tolist()],
                },
                "products": {
                    "labels": top_products["product_name"].tolist(),
                    "units": [int(value) for value in top_products["units"].tolist()],
                    "revenue": [int(value) for value in top_products["revenue"].tolist()],
                },
                "payments": {
                    "labels": by_payment["payment_method"].tolist(),
                    "values": [int(value) for value in by_payment["line_total"].tolist()],
                },
                "stock": {
                    "labels": stock_table["name"].tolist(),
                    "values": [int(value) for value in stock_table["stock"].tolist()],
                },
            },
            "top_products": top_products.to_dict(orient="records"),
            "stock_table": stock_table.to_dict(orient="records"),
            "recent_payments": recent_payments.to_dict(orient="records"),
            "recent_movements": recent_movements.to_dict(orient="records"),
        }

    @app.route("/admin/analitica")
    @admin_required
    def admin_analytics() -> str:
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()
        sport = request.args.get("sport", "").strip().lower()
        try:
            payment_method_id = int(request.args.get("payment_method_id", "0"))
        except ValueError:
            payment_method_id = 0

        frames = load_analytics_frames()
        filtered = apply_analytics_filters(
            frames, start_date, end_date, sport, payment_method_id
        )
        analysis = build_dashboard_analysis(filtered)
        payment_methods = get_db().execute(
            "SELECT id, name FROM payment_methods WHERE active = 1 ORDER BY name"
        ).fetchall()
        return render_template(
            "admin/analytics.html",
            analysis=analysis,
            chart_data=analysis["charts"],
            payment_methods=payment_methods,
            filters={
                "start_date": start_date,
                "end_date": end_date,
                "sport": sport,
                "payment_method_id": payment_method_id,
            },
        )

    @app.route("/admin/analitica/exportar/<dataset>")
    @admin_required
    def admin_analytics_export(dataset: str) -> Any:
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()
        sport = request.args.get("sport", "").strip().lower()
        try:
            payment_method_id = int(request.args.get("payment_method_id", "0"))
        except ValueError:
            payment_method_id = 0
        frames = apply_analytics_filters(
            load_analytics_frames(), start_date, end_date, sport, payment_method_id
        )
        available = {
            "ventas": frames["items"],
            "pedidos": frames["orders"],
            "stock": frames["stock"],
            "pagos": frames["payments"],
            "movimientos": frames["movements"],
        }
        frame = available.get(dataset)
        if frame is None:
            abort(404)
        csv_data = frame.to_csv(index=False).encode("utf-8-sig")
        return app.response_class(
            csv_data,
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=sportzone_{dataset}.csv"
            },
        )


    @app.route("/admin/analitica/exportar-pdf")
    @admin_required
    def admin_analytics_pdf() -> Any:
        """Compatibilidad: descarga el informe PDF completo."""
        return admin_analytics_pdf_dataset("completo")

    @app.route("/admin/analitica/exportar-pdf/<dataset>")
    @admin_required
    def admin_analytics_pdf_dataset(dataset: str) -> Any:
        """Exporta PDF por conjunto de datos, igual que el menu CSV."""
        allowed = {"completo", "ventas", "pedidos", "stock", "pagos", "movimientos"}
        if dataset not in allowed:
            abort(404)

        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()
        sport = request.args.get("sport", "").strip().lower()
        try:
            payment_method_id = int(request.args.get("payment_method_id", "0"))
        except ValueError:
            payment_method_id = 0

        filtered = apply_analytics_filters(
            load_analytics_frames(), start_date, end_date, sport, payment_method_id
        )
        analysis = build_dashboard_analysis(filtered)

        payment_method_name = "Todos"
        if payment_method_id > 0:
            method = get_db().execute(
                "SELECT name FROM payment_methods WHERE id = ?",
                (payment_method_id,),
            ).fetchone()
            if method is not None:
                payment_method_name = method["name"]

        filters = {
            "start_date": start_date,
            "end_date": end_date,
            "sport": sport,
            "payment_method_id": payment_method_id,
            "payment_method_name": payment_method_name,
        }
        pdf_bytes = build_dataset_pdf(dataset, filtered, analysis, filters)
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M")
        filename = f"sportzone_{dataset}_{timestamp}.pdf"
        return app.response_class(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
                "Cache-Control": "no-store",
            },
        )

    def validate_product_form(form: Any) -> tuple[tuple[Any, ...] | None, str | None]:
        name = form.get("name", "").strip()
        brand = form.get("brand", "").strip()
        sport = form.get("sport", "").strip().lower()
        product_type = form.get("product_type", "").strip()
        audience = form.get("audience", "adulto").strip()
        description = form.get("description", "").strip()
        active = 1 if form.get("active") == "1" else 0
        try:
            price = int(form.get("price", "0"))
            stock = int(form.get("stock", "0"))
        except ValueError:
            return None, "Precio y stock deben ser números enteros."
        if not all((name, brand, product_type)):
            return None, "Nombre, marca y tipo son obligatorios."
        if sport not in {"tenis", "golf", "squash"}:
            return None, "Selecciona un deporte válido."
        if price < 0 or stock < 0:
            return None, "Precio y stock no pueden ser negativos."
        return (
            name,
            brand,
            sport,
            product_type,
            audience,
            description,
            price,
            stock,
            active,
        ), None

    @app.errorhandler(429)
    def rate_limited(_: Any) -> tuple[str, int]:
        return render_template("error.html", code=429, message="Demasiados intentos. Intenta nuevamente en 15 minutos."), 429

    @app.errorhandler(400)
    def bad_request(error: Any) -> tuple[str, int]:
        return render_template("error.html", code=400, message=str(error.description)), 400

    @app.errorhandler(403)
    def forbidden(_: Any) -> tuple[str, int]:
        return render_template("error.html", code=403, message="No tienes permiso para acceder."), 403

    @app.errorhandler(404)
    def not_found(_: Any) -> tuple[str, int]:
        return render_template("error.html", code=404, message="La página solicitada no existe."), 404

    with app.app_context():
        init_db(seed=SEED_PRODUCTS)
        admin_email = ADMIN_EMAIL.strip().lower()
        admin_password = ADMIN_PASSWORD
        if admin_email and admin_password and len(admin_password) >= 8:
            db = get_db()
            existing = db.execute("SELECT id FROM users WHERE email = ?", (admin_email,)).fetchone()
            if not existing:
                db.execute(
                    "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
                    ("Administrador", admin_email, generate_password_hash(admin_password)),
                )
                db.commit()

    return app


def format_cop(value: int) -> str:
    return "$" + f"{int(value):,}".replace(",", ".")


app = create_app()


if __name__ == "__main__":
    app.run(debug=False)
