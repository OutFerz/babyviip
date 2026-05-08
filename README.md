# 🚀 Proyecto Babyviip

Este proyecto utiliza Docker para levantar un entorno completo con Python y una base de datos relacional. **No se reemplazó PostgreSQL por MySQL en el repo**: conviven ambos y eliges con variables y `docker compose`.

**Resumen rápido**

| Qué quieres | Qué usar |
|-------------|----------|
| **Desarrollo habitual (por defecto)** | Solo `docker-compose.yml`. Sin `DATABASE_ENGINE=mysql` en `.env` (o `DATABASE_ENGINE=postgresql`). Comando típico: `docker compose up -d`. Usa el servicio **`db`** (PostgreSQL). |
| **Evaluación que pide MySQL** | `.env` con **`DATABASE_ENGINE=mysql`** más el segundo archivo: `docker-compose.mysql.yml`. Comando típico: ver sección siguiente. Usa **`mysql_db`**. PostgreSQL **no hace falta** levantarlo en ese modo. |

---

## Base de datos: MySQL (solo para la evaluación)

1. En tu `.env` (o combinando con lo que ya tienes):

   ```env
   DATABASE_ENGINE=mysql
   MYSQL_HOST=mysql_db
   MYSQL_PORT=3306
   MYSQL_ROOT_PASSWORD=un_root_seguro_distinto
   # DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD se reutilizan
   ```

   Puedes partir de **`.env.mysql.example`** en la raíz del proyecto.

2. Levantar **solo MySQL + web** (PostgreSQL puede no arrancarse):

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.mysql.yml up -d --build mysql_db web
   ```

3. Migraciones y usuario admin como siempre:

   ```bash
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

4. Volver a Postgres: pon `DATABASE_ENGINE=postgresql` (o bórrala), usa **`docker compose up -d`** sin el segundo archivo y opcionalmente baja los contenedores MySQL (`docker compose -f docker-compose.yml -f docker-compose.mysql.yml down`).

_Notas rápidas: Django + ORM suele comportarse igual, pero cada motor tiene matices; para la evaluación lo habitual es **`migrate`** sobre una MySQL vacía. El arranque usa **`PyMySQL`** y `wait_for_db.py` espera según `DATABASE_ENGINE`._

---

## Nota importante (Windows + Docker)

Si trabajas en Windows, es común que `entrypoint.sh` quede con saltos de línea **CRLF**. Como el `docker-compose.yml` monta el proyecto con `.:/app`, el contenedor termina ejecutando el script del host y `sh` puede fallar con:

- `/app/entrypoint.sh: 5: set: Illegal option -`

Esto ocurre porque se interpreta como `set -e\r`. Para evitarlo:

- Se agregó `.gitattributes` para forzar **LF** en `*.sh`.
- El contenedor normaliza **CRLF → LF** antes de ejecutar `entrypoint.sh` cuando hay bind-mount.

1. Acceso externo (Azure Networking)

   Ve al Portal de Azure.

   Entra en tu Virtual Machine -> Networking (o Redes).

   Haz clic en Add inbound port rule (Agregar regla de puerto de entrada).

   Configura:

   - `Destination port ranges`: 8000
   - `Protocol`: TCP
   - `Name`: Django_Port

   Dale a Add.

   Nos conectamos a la VM

   `ssh -i ~/Documents/pass.pem USER@IP_ADDRESS`

   Lo primero que querrás hacer es preparar el entorno para Docker:

   - Instala Docker y Compose:

     ```bash
     sudo apt update
     sudo apt install docker-compose-v2 -y
     ```

   - Dale permisos a tu usuario:

     ```bash
     sudo usermod -aG docker $USER
     ```

     (Después de esto, cierra la sesión con `exit` y vuelve a entrar para que el cambio surta efecto).

2. Clonar el proyecto y configurar

   Ahora que estás dentro con los permisos frescos, vamos por el código.

   ```bash
   # Clona tu repositorio
   git clone https://github.com/OutFerz/babyviip.git
   cd babyviip

   # Crea el archivo de variables de entorno
   nano .env

   DATABASE_NAME=XXXXX
   DATABASE_USER=XXXXX
   DATABASE_PASSWORD=XXXXX
   DATABASE_HOST=XXXXX
   DATABASE_PORT=XXXXX
   ```

3. Levantar los contenedores

   ```bash
   docker compose up -d
   ```

4. Preparar la Base de Datos

   Una vez que los contenedores estén arriba (puedes verificar con `docker ps`), ejecuta las migraciones iniciales de Django:

   ```bash
   # Aplicar migraciones
   docker compose exec web python manage.py migrate

   # Crear tu usuario administrador
   docker compose exec web python manage.py createsuperuser

   # Aseguramos de que está ON
   docker compose ps
   ```

   y finalmente conectarnos a http://IP_ADDRESS:8000

---

## Autenticación y datos demo

- El modelo de usuario es **`erp.Usuario`** (`AUTH_USER_MODEL`). **Cliente** guarda datos de compra y puede enlazarse a un usuario (`usuario` OneToOne, opcional).
- **Registro / login:** `/accounts/registro/`, `/accounts/login/`, cerrar sesión con el botón **Salir**.
- **Ventas y clientes** (`/ventas/`): solo usuarios con `is_staff` o `es_administrador_tienda`. El enlace **Administración** (Django Admin) solo aparece si `is_staff`.
- **Productos de ejemplo** (polera U.CH. y pantalón con URLs de imagen):

  ```bash
  docker compose exec web python manage.py seed_productos
  ```

- Si venías de una base creada con el modelo antiguo (sin `Usuario`), puede hacer falta recrear el volumen y migrar de nuevo: `docker compose down -v` y luego `up -d`, `migrate` y `seed_productos`.