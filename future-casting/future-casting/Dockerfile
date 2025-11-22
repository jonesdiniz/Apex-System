# Dockerfile para Future-Casting v4.0.0 - Ecossistema Co-Piloto Unificado
FROM python:3.11-slim

# Metadados
LABEL maintainer="Manus AI"
LABEL version="4.0.0"
LABEL description="Future-Casting v4.0 - Previsões Executáveis e Ações Preventivas"

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
COPY future_casting_v4_preventive_actions.py .

# Criar diretórios necessários
RUN mkdir -p /app/data /app/logs /app/predictions

# Configurar permissões
RUN chown -R app:app /app
USER app

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8008
ENV HOST=0.0.0.0

# Configurações do Future-Casting v4.0 (Autônomo)
ENV FUTURE_CASTING_ENVIRONMENT=production
ENV AUTO_EXECUTE_THRESHOLD=0.9
ENV MONITORING_INTERVAL=30
ENV PREDICTIVE_ANALYSIS_ENABLED=true
ENV PREVENTIVE_ACTIONS_ENABLED=true

# Configurações de previsões
ENV MAX_ACTIVE_PREDICTIONS=1000
ENV PREDICTION_HORIZON_HOURS=24
ENV ACTION_SCHEDULING_ENABLED=true
ENV COST_BENEFIT_ANALYSIS_ENABLED=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Volumes para previsões e dados
VOLUME ["/app/data", "/app/predictions"]

# Expor porta
EXPOSE ${PORT}

# Comando de inicialização
CMD ["python", "future_casting_v4_preventive_actions.py"]

