"""Adaptador SQL para las consultas existentes del proyecto con flask_mysqldb."""
from MySQLdb.cursors import DictCursor
from sqlalchemy import create_engine, URL


class Result:
    def __init__(self, cursor):
        self.rows = list(cursor.fetchall()) if cursor.description is not None else []
        self.lastrowid = cursor.lastrowid
        self.rowcount = cursor.rowcount

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def fetchall(self):
        rows, self.rows = self.rows, []
        return rows


class DatabaseAdapter:
    def __init__(self, connection, settings):
        self.connection = connection
        # Esta conexion independiente se utiliza exclusivamente en analytics con pandas.
        self.sqlalchemy_engine = create_engine(
            URL.create(
                "mysql+mysqldb",
                username=settings["MYSQL_USER"],
                password=settings["MYSQL_PASSWORD"],
                host=settings["MYSQL_HOST"],
                port=int(settings["MYSQL_PORT"]),
                database=settings["MYSQL_DB"],
            ),
            pool_pre_ping=True,
        )

    def execute(self, sql, params=None):
        cursor = self.connection.cursor(DictCursor)
        try:
            cursor.execute(sql.replace("?", "%s"), tuple(params or ()))
            return Result(cursor)
        finally:
            cursor.close()

    def executemany(self, sql, params):
        cursor = self.connection.cursor(DictCursor)
        try:
            cursor.executemany(sql.replace("?", "%s"), params)
            return Result(cursor)
        finally:
            cursor.close()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        # flask_mysqldb cierra la conexion de MySQL al finalizar app_context.
        self.sqlalchemy_engine.dispose()
