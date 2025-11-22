# Dockerfile para Ecosystem Platform v3.1.0 - Ecossistema Co-Piloto Unificado
FROM python:3.11-slim

# Metadados
LABEL maintainer="Manus AI"
LABEL version="3.1.0"
LABEL description="Ecosystem Platform - Plataforma Central do Ecossistema"

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

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação (placeholder - será substituído pelo código real)
COPY ecosystem_platform_v3.1.0.py .

# Criar diretórios necessários
RUN mkdir -p /app/data /app/logs

# Configurar permissões
RUN chown -R app:app /app
USER app

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8002
ENV HOST=0.0.0.0

# Configurações do Ecosystem Platform
ENV PLATFORM_ENVIRONMENT=production
ENV ANALYTICS_ENABLED=true
ENV INSIGHTS_ENABLED=true
ENV MONITORING_INTERVAL=30

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Volumes para dados
VOLUME ["/app/data"]

# Expor porta
EXPOSE ${PORT}

# Comando de inicialização
CMD ["python", "ecosystem_platform_v3.1.0.py"]

