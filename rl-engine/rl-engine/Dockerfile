# Dockerfile para RL-Engine v3.4.2 - Ecossistema Co-Piloto Unificado
FROM python:3.11-slim

# Metadados
LABEL maintainer="Manus AI"
LABEL version="3.4.2"
LABEL description="RL-Engine Dual Buffer - Sistema de Aprendizado por Reforço"

# Configurar timezone
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements (assumindo que requirements.txt está no mesmo diretório)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação principal (AGORA É main.py)
COPY main.py .

# Comando para rodar a aplicação
CMD gunicorn --bind "0.0.0.0:${PORT}" --workers 2 --worker-class uvicorn.workers.UvicornWorker main:app
