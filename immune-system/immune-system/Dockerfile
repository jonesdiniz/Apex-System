# Dockerfile para Immune System v4.0.0 - Ecossistema Co-Piloto Unificado
FROM python:3.11-slim

# Metadados
LABEL maintainer="Manus AI"
LABEL version="4.0.0"
LABEL description="Immune System v4.0 - Auto-Scaling Executável e Mitigação Proativa"

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
COPY immune_system_v4_curador_autonomo.py .
COPY proactive_mitigation_engine_v4.py .

# Criar diretórios necessários
RUN mkdir -p /app/data /app/logs /app/metrics

# Configurar permissões
RUN chown -R app:app /app
USER app

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8007
ENV HOST=0.0.0.0

# Configurações do Immune System v4.0 (Autônomo)
ENV IMMUNE_ENVIRONMENT=production
ENV AUTONOMOUS_MODE=true
ENV AUTO_EXECUTE_THRESHOLD=0.85
ENV MONITORING_INTERVAL=15
ENV CIRCUIT_BREAKER_ENABLED=true
ENV PROACTIVE_MITIGATION_ENABLED=true

# Configurações de segurança
ENV SAFETY_CHECKS_ENABLED=true
ENV ROLLBACK_ENABLED=true
ENV CONFLICT_DETECTION_ENABLED=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Volumes para métricas e dados
VOLUME ["/app/data", "/app/metrics"]

# Expor porta
EXPOSE ${PORT}

# Comando de inicialização
CMD ["python", "immune_system_v4_curador_autonomo.py"]

