# Dockerfile para Proactive Conversation v4.0.0 - Ecossistema Co-Piloto Unificado
FROM python:3.11-slim

# Metadados
LABEL maintainer="Manus AI"
LABEL version="4.0.0"
LABEL description="Proactive Conversation v4.0 - Orquestração Autônoma do Ecossistema"

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

# Copiar código da aplicação
COPY proactive_conversation_v4_orchestrator.py .

# Criar diretórios necessários
RUN mkdir -p /app/data /app/logs /app/orchestration

# Configurar permissões
RUN chown -R app:app /app
USER app

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8009
ENV HOST=0.0.0.0

# Configurações do Proactive Conversation v4.0 (Orquestrador)
ENV ORCHESTRATION_ENVIRONMENT=production
ENV ORCHESTRATION_THRESHOLD=0.8
ENV MONITORING_INTERVAL=15
ENV ECOSYSTEM_COORDINATION_ENABLED=true
ENV EVENT_DRIVEN_WORKFLOWS_ENABLED=true

# Configurações de orquestração
ENV SERVICES_TO_MONITOR=6
ENV CROSS_SERVICE_OPTIMIZATION_ENABLED=true
ENV INTELLIGENT_DECISION_MAKING_ENABLED=true
ENV AUTONOMOUS_COMMUNICATION_ENABLED=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Volumes para dados de orquestração
VOLUME ["/app/data", "/app/orchestration"]

# Expor porta
EXPOSE ${PORT}

# Comando de inicialização
CMD ["python", "proactive_conversation_v4_orchestrator.py"]

