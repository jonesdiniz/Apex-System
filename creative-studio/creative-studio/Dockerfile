# Dockerfile para Creative Studio v3.5.0 - Ecossistema Co-Piloto Unificado
FROM python:3.11-slim

# Metadados
LABEL maintainer="Manus AI"
LABEL version="3.5.0"
LABEL description="Creative Studio - Sistema de Geração de Conteúdo Inteligente"

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
COPY creative_studio_v3.5.0.py .

# Criar diretórios necessários
RUN mkdir -p /app/data /app/logs /app/content

# Configurar permissões
RUN chown -R app:app /app
USER app

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8003
ENV HOST=0.0.0.0

# Configurações do Creative Studio
ENV STUDIO_ENVIRONMENT=production
ENV CONTENT_INTELLIGENCE_ENABLED=true
ENV GENERATION_ENABLED=true
ENV ANALYSIS_ENABLED=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Volumes para conteúdo
VOLUME ["/app/data", "/app/content"]

# Expor porta
EXPOSE ${PORT}

# Comando de inicialização
CMD ["python", "creative_studio_v3.5.0.py"]

