"""Adaptador PostgreSQL (psycopg 3) para SportZone.

Mantiene la interfaz execute/executemany/commit/rollback del proyecto original.
"""
from psycopg import connect
from psycopg.rows import dict_row
from sqlalchemy import create_engine, URL


class Result:
    def __init__(self, cursor):
        self.rows = list(cursor.fetchall()) if cursor.description is not None else []
        self.rowcount = cursor.rowcount

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def fetchall(self):
        rows, self.rows = self.rows, []
        return rows


class DatabaseAdapter:
    def __init__(self, settings):
        self.connection = connect(
            host=settings["PGHOST"],
            port=int(settings["PGPORT"]),
            dbname=settings["PGDATABASE"],
            user=settings["PGUSER"],
            password=settings["PGPASSWORD"],
            sslmode=settings["PGSSLMODE"],
            row_factory=dict_row,
            connect_timeout=15,
        )
        self.sqlalchemy_engine = create_engine(
            URL.create(
                "postgresql+psycopg",
                username=settings["PGUSER"],
                password=settings["PGPASSWORD"],
                host=settings["PGHOST"],
                port=int(settings["PGPORT"]),
                database=settings["PGDATABASE"],
                query={"sslmode": settings["PGSSLMODE"]},
            ),
            pool_pre_ping=True,
        )

    @staticmethod
    def _placeholders(sql):
        # Las consultas originales utilizan marcadores ?; psycopg usa %s.
        return sql.replace("?", "%s")

    def execute(self, sql, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(self._placeholders(sql), tuple(params or ()))
            return Result(cursor)

    def executemany(self, sql, params):
        with self.connection.cursor() as cursor:
            cursor.executemany(self._placeholders(sql), params)
            return Result(cursor)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.sqlalchemy_engine.dispose()
        self.connection.close()
