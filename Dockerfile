# Imagen base de Python
FROM python:3.11-slim

# Evitar .pyc y usar salida sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /usr/src/app

# Copiamos requirements desde la raíz (ajusta si lo tienes en otro sitio)
# Crea un requirements.txt en la raíz o en api/ según prefieras.
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código de backend:
# - paquete db (modelos y conexión)
# - carpeta api (user.py, api.py, cliente.py, etc.)
COPY db ./db
COPY api ./api

# Trabajaremos dentro de /usr/src/app/api
WORKDIR /usr/src/app/api

# Puerto por defecto (el contenedor lo expone, luego docker-compose mapea 5050 o 5051)
EXPOSE 5050

# Comando por defecto: servicio de usuarios
# Para el servicio "catalog" lo sobreescribimos en docker-compose.yml
CMD ["python", "user.py"]
