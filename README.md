# Proyecto Babyviip

# Instalar el Subsistema de Linux (requerido para Docker moderno)
wsl --install

# Instalar Git usando el gestor de paquetes de Windows
winget install --id Git.Git -e --source winget

winget install --id Docker.DockerDesktop -e --source winget

cd C:\Users\tu_usuario\Desktop
git clone https://github.com/OutFerz/babyviip.git
cd babyviip

crear el archivo env con los datos
DATABASE_NAME=XXXX
DATABASE_USER=XXXX
DATABASE_PASSWORD=XXXX
DATABASE_HOST=XXXX
DATABASE_PORT=XXXX

# Esto descarga las imágenes de Python y Postgres y arranca todo
docker-compose up -d --build

y en teoría debería estar corriendo en http://localhost:8000
