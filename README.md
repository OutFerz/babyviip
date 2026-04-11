# 🚀 Proyecto Babyviip

Este proyecto utiliza Docker para levantar un entorno completo con Python y PostgreSQL.

---

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