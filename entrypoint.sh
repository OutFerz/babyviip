#!/bin/sh
# En Windows, si este archivo queda con CRLF, al montar .:/app Docker usa la copia
# del host y sh puede fallar en la siguiente línea con: set: Illegal option -
# (guárdalo en LF o configura el editor / .gitattributes para *.sh).
set -e

echo "Esperando a Postgres en ${DATABASE_HOST:-db}..."

# Usamos python para verificar la conexión en lugar de pg_isready
until python -c "import psycopg2, os; psycopg2.connect(dbname=os.getenv('DATABASE_NAME'), user=os.getenv('DATABASE_USER'), password=os.getenv('DATABASE_PASSWORD'), host=os.getenv('DATABASE_HOST', 'db'), port=os.getenv('DATABASE_PORT', '5432'))" > /dev/null 2>&1; do
  echo "Postgres no está listo - esperando..."
  sleep 1
done

echo "Base de datos lista. Aplicando migraciones..."
python manage.py migrate --noinput

echo "Iniciando servidor..."
exec python manage.py runserver 0.0.0.0:8000