"""
Paquete de configuración (proyecto `core`).
Carga .env antes de otros imports y registra PyMySQL si usamos MySQL.
"""
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

if os.environ.get("DATABASE_ENGINE", "postgresql").strip().lower() in (
    "mysql",
    "mariadb",
    "maria",
):
    import pymysql

    pymysql.install_as_MySQLdb()
