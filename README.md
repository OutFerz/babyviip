# 🚀 Proyecto Babyviip

Este proyecto utiliza Docker para levantar un entorno completo con Python y PostgreSQL.

---

## 📦 Requisitos

Antes de comenzar, asegúrate de tener instalado:

### 1. Subsistema de Linux (WSL)
```bash
wsl --install
```

### 2. Git
```bash
winget install --id Git.Git -e --source winget
```

### 3. Docker Desktop
```bash
winget install --id Docker.DockerDesktop -e --source winget
```

---

## 📥 Clonar el repositorio

```bash
cd C:\Users\tu_usuario\Desktop
git clone https://github.com/OutFerz/babyviip.git
cd babyviip
```

---

## ⚙️ Configuración

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
DATABASE_NAME=XXXX
DATABASE_USER=XXXX
DATABASE_PASSWORD=XXXX
DATABASE_HOST=XXXX
DATABASE_PORT=XXXX
```

---

## 🐳 Levantar el proyecto con Docker

```bash
docker-compose up -d --build
```

Esto descargará las imágenes necesarias (Python y PostgreSQL) y levantará los contenedores.

---

## 🌐 Acceso a la aplicación

Una vez iniciado, la aplicación debería estar disponible en:

```
http://localhost:8000
```

---

## 📝 Notas

- Asegúrate de que Docker Desktop esté corriendo antes de ejecutar los comandos.
- Si tienes problemas con WSL, reinicia tu equipo después de instalarlo.
- Puedes detener los contenedores con:

```bash
docker-compose down
```

---

## 👨‍💻 Autor

Desarrollado por [OutFerz](https://github.com/OutFerz)
