# Despliegue en AWS EC2 con Docker + MySQL (Babyviip)

Guía de los pasos seguidos para llevar el proyecto a una instancia **EC2** (p. ej. **Amazon Linux 2023**), usar **MySQL en contenedor**, resolver permisos de Docker, autenticación de MySQL, migraciones y acceso desde el navegador.

---

## 1. Servidor: Docker y permisos

1. Instalar **Docker Engine** y arrancar el servicio (según la guía oficial para tu AMI: Amazon Linux 2023 suele usar `dnf`).
2. Añadir el usuario al grupo `docker` para no depender de `sudo` en cada comando:
   - `sudo usermod -aG docker ec2-user`
3. Cerrar sesión SSH y volver a entrar, o ejecutar **`newgrp docker`** en la terminal actual.
4. Si aparece **`permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`**, el shell no tiene aún el grupo `docker`: usa **`newgrp docker`** o antepon **`sudo`** a `docker` / `docker-compose`.

---

## 2. Docker Compose (binario)

En algunas AMIs no viene el plugin **Compose V2** (`docker compose`). Se puede instalar el binario **standalone** como `docker-compose` en `/usr/local/bin` y comprobar con `docker-compose version`.

Los comandos de este proyecto pueden escribirse con:

- `docker-compose` (binario), o  
- `docker compose` (plugin), según lo que tengas instalado.

---

## 3. Clonar el repositorio

```bash
cd ~
git clone https://github.com/OutFerz/babyviip.git babyviip
cd babyviip
```

(Ajusta la URL si tu remoto es otro.)

---

## 4. Archivo `.env` para MySQL

1. Copia el ejemplo de MySQL y edítalo:
   - `cp .env.mysql.example .env`
2. Valores mínimos coherentes con **`docker-compose.mysql.yml`** y con **`core/settings.py`**:
   - `DATABASE_ENGINE=mysql`
   - `MYSQL_HOST=mysql_db` (nombre del servicio en Compose; **no** uses `db` ni `localhost` para el contenedor `web`).
   - `MYSQL_PORT=3306` (puerto **dentro** de la red Docker; el contenedor `web` habla con MySQL por el puerto interno 3306).
   - `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`: alineados con las variables que usa el servicio `mysql_db` en el compose.
   - `MYSQL_ROOT_PASSWORD=...` (**obligatorio** para la imagen oficial `mysql:8`).
3. Evita dejar en el mismo `.env` valores que fuercen Postgres cuando quieres MySQL (p. ej. `DATABASE_HOST=db` pensado para el servicio `db` de Postgres). Para MySQL manda **`MYSQL_HOST=mysql_db`**.

Para exponer la app en internet con una IP concreta, conviene definir también:

- `DJANGO_ALLOWED_HOSTS=tu.ip.publica,localhost,127.0.0.1` (separado por comas; en muchos entornos de prueba se usa `*` vía `DJANGO_ALLOWED_HOSTS` según `settings.py`).

---

## 5. Levantar solo MySQL + aplicación web

No hace falta levantar Postgres en este modo. Usa **dos archivos** de Compose:

```bash
newgrp docker   # si hace falta por permisos
docker-compose -f docker-compose.yml -f docker-compose.mysql.yml up -d --build mysql_db web
```

- **`mysql_db`**: base MySQL 8.
- **`web`**: imagen Django definida en el `dockerfile`; el **`entrypoint.sh`** espera a la base (`wait_for_db.py`) y ejecuta **`migrate`** al arrancar.

---

## 6. Puerto del servicio MySQL en el **host** (conflicto con 3306)

Si en la EC2 ya hay **MariaDB/MySQL** en el puerto **3306** del host, el `ports` del servicio `mysql_db` chocará. Solución: en **`docker-compose.mysql.yml`** mapear por ejemplo **`3307:3306`** (host **3307** → contenedor **3306**). Dentro de Docker, **`web`** sigue usando **`MYSQL_PORT=3306`** hacia el hostname `mysql_db`.

---

## 7. PyMySQL, `caching_sha2_password` y el paquete `cryptography`

Si al ejecutar migraciones aparece:

`RuntimeError: 'cryptography' package is required for sha256_password or caching_sha2_password auth methods`

Opciones (cualquiera basta; pueden combinarse para mayor robustez):

1. **Dependencia en el proyecto:** en `requirements.txt` está **`cryptography`**; tras añadirla, **`docker-compose ... up -d --build web`** para instalarla en la imagen.
2. **MySQL con plugin de autenticación clásico:** en el `command` del servicio `mysql_db`, añadir  
   `--default-authentication-plugin=mysql_native_password`  
   y, si creas usuarios sobre datos viejos, conviene **`down -v`** para recrear el volumen de datos y que los usuarios se creen con ese plugin.

---

## 8. Migraciones y error `Duplicate column name 'publicado'`

- El contenedor **`web`** ejecuta **`python manage.py migrate --noinput`** al iniciar (**`entrypoint.sh`**).
- Si **al mismo tiempo** lanzas **`docker-compose exec web python manage.py migrate`** desde fuera, dos procesos pueden aplicar la misma migración y en MySQL fallar con **columna `publicado` duplicada**.
- **Qué hacer:** no lanzar `migrate` manual **en paralelo** justo después de `up`; esperar unos segundos o revisar logs. En el repo, la migración **`erp/0002_producto_publicado`** está hecha para **no repetir** el `ADD COLUMN` si la columna ya existe.

Si la base quedó en estado raro después de pruebas:

```bash
docker-compose -f docker-compose.yml -f docker-compose.mysql.yml down -v
docker-compose -f docker-compose.yml -f docker-compose.mysql.yml up -d --build mysql_db web
```

(`-v` borra el volumen de MySQL; **pierdes datos** demo en esa base.)

Comprobación:

```bash
docker-compose -f docker-compose.yml -f docker-compose.mysql.yml exec web python manage.py migrate
```

Si todo está aplicado, verás: **`No migrations to apply.`**

---

## 9. Usuario administrador y datos de prueba

```bash
docker-compose -f docker-compose.yml -f docker-compose.mysql.yml exec web python manage.py createsuperuser
docker-compose -f docker-compose.yml -f docker-compose.mysql.yml exec web python manage.py seed_productos
```

(`seed_productos` solo si el comando existe en tu rama y lo necesitas.)

---

## 10. Puerto HTTP de la aplicación y Security Group

- En **`docker-compose.yml`**, el servicio **`web`** mapea el puerto del contenedor **8000** al host, por defecto **`8000:8000`**. Si cambias a **`8001:8000`**, la app pública será el puerto **8001** del servidor.
- En la consola **EC2 → Security Group → Reglas de entrada**, abre el **mismo puerto TCP** que hayas mapeado (**8000** u **8001**) hacia tu IP o hacia `0.0.0.0/0` (solo para pruebas).
- Sin esa regla, el navegador muestra **timeout** (`ERR_CONNECTION_TIMED_OUT`) aunque Django esté bien dentro del contenedor.

Comprobar **en la EC2** (sustituye el puerto si usas 8001):

```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/
```

Si responde **200** u otro código HTTP válido, el servicio escucha; el problema suele ser el **Security Group** o un firewall del host.

URL típica: **`http://IP_PUBLICA_DE_LA_EC2:8000/`** o **`:8001/`** según tu `ports`.

---

## 11. Resumen de comandos útiles

| Acción | Comando |
|--------|---------|
| Arrancar / reconstruir | `docker-compose -f docker-compose.yml -f docker-compose.mysql.yml up -d --build mysql_db web` |
| Ver logs del web | `docker-compose -f docker-compose.yml -f docker-compose.mysql.yml logs -f --tail=80 web` |
| Migraciones | `docker-compose ... exec web python manage.py migrate` |
| Superusuario | `docker-compose ... exec web python manage.py createsuperuser` |
| Parar y borrar volúmenes | `docker-compose ... down -v` |

---

## 12. Actualizar código en el servidor

```bash
cd ~/babyviip
git pull
docker-compose -f docker-compose.yml -f docker-compose.mysql.yml up -d --build mysql_db web
```

---

*Documento alineado con el despliegue documentado en el repositorio y las incidencias habituales (Docker, MySQL 8, migraciones y red en EC2).*
