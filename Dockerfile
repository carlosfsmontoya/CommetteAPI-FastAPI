# Usa una imagen base oficial de Python
FROM python:3.12-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Instala las herramientas necesarias para compilar paquetes de Python y pymssql
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    freetds-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Instala pymssql
RUN pip install --no-binary pymssql pymssql

# Copia el archivo requirements.txt al directorio de trabajo
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación al directorio de trabajo
COPY . .

# Expone el puerto en el que correrá la aplicación
EXPOSE 8000

# Comando para correr la aplicación usando uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]