#!/bin/sh
# En Windows, si este archivo queda con CRLF, al montar .:/app Docker usa la copia
# del host y sh puede fallar en la siguiente línea con: set: Illegal option -
# (guárdalo en LF o configura el editor / .gitattributes para *.sh).
set -e

python /app/wait_for_db.py

echo "Base de datos lista. Aplicando migraciones..."
python manage.py migrate --noinput

echo "Iniciando servidor..."
exec python manage.py runserver 0.0.0.0:8000