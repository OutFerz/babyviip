# 🚀 Proyecto Babyviip

Este proyecto utiliza Docker para levantar un entorno completo con Python y PostgreSQL.

---

## 📦 Requisitos

Antes de comenzar, asegúrate de tener instalado:

### 1. Subsistema de Linux (WSL)
```bash
wsl --install
2. Git
winget install --id Git.Git -e --source winget
3. Docker Desktop
winget install --id Docker.DockerDesktop -e --source winget
📥 Clonar el repositorio
cd C:\Users\tu_usuario\Desktop
git clone https://github.com/OutFerz/babyviip.git
cd babyviip
⚙️ Configuración

Crea un archivo .env en la raíz del proyecto con el siguiente contenido:

DATABASE_NAME=XXXX
DATABASE_USER=XXXX
DATABASE_PASSWORD=XXXX
DATABASE_HOST=XXXX
DATABASE_PORT=XXXX
🐳 Levantar el proyecto con Docker
docker-compose up -d --build

Esto descargará las imágenes necesarias (Python y PostgreSQL) y levantará los contenedores.

🌐 Acceso a la aplicación

Una vez iniciado, la aplicación debería estar disponible en:

http://localhost:8000
📝 Notas
Asegúrate de que Docker Desktop esté corriendo antes de ejecutar los comandos.
Si tienes problemas con WSL, reinicia tu equipo después de instalarlo.
Puedes detener los contenedores con:
docker-compose down