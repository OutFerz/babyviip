#!/usr/bin/env python3
"""
Espera a que la base responda según DATABASE_ENGINE (.env).
Usado desde entrypoint.sh (Docker).
"""
import os
import sys
import time


def env_lower(key: str, default: str) -> str:
    return os.environ.get(key, default).strip().lower()


def main() -> int:
    engine = env_lower("DATABASE_ENGINE", "postgresql")
    if engine in ("mysql", "mariadb", "maria"):
        import pymysql  # noqa: WPS433

        host = os.environ.get("MYSQL_HOST", "mysql_db")
        port = int(os.environ.get("MYSQL_PORT", "3306"))
        user = os.environ["DATABASE_USER"]
        password = os.environ["DATABASE_PASSWORD"]
        db = os.environ["DATABASE_NAME"]
        print(f"Esperando MySQL en {host}:{port} / {db} ...")
        while True:
            try:
                pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=db,
                    connect_timeout=3,
                )
                print("MySQL disponible.")
                return 0
            except Exception as exc:  # noqa: BLE001
                print(f"MySQL no listo ({exc!r}). Reintentando...")
                time.sleep(1)

    import psycopg2  # noqa: WPS433

    host = os.environ.get("DATABASE_HOST", "db")
    port = os.environ.get("DATABASE_PORT", "5432")
    user = os.environ["DATABASE_USER"]
    password = os.environ["DATABASE_PASSWORD"]
    db = os.environ["DATABASE_NAME"]
    print(f"Esperando Postgres en {host}:{port} / {db} ...")
    while True:
        try:
            psycopg2.connect(
                dbname=db,
                user=user,
                password=password,
                host=host,
                port=port,
                connect_timeout=3,
            )
            print("Postgres disponible.")
            return 0
        except Exception as exc:  # noqa: BLE001
            print(f"Postgres no listo ({exc!r}). Reintentando...")
            time.sleep(1)


if __name__ == "__main__":
    sys.exit(main())
