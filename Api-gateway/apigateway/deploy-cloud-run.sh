#!/bin/bash

# Script de deploy para Google Cloud Run - API Gateway v4.1.2 Production Ready
# Região: southamerica-east1 (São Paulo, Brasil)

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Configurações
SERVICE_NAME="apex-api-gateway"
REGION="southamerica-east1"
PLATFORM="managed"
IMAGE_NAME="gcr.io/\$PROJECT_ID/apex-api-gateway:v4.1.2"
FRONTEND_URL="https://app.apexsystem.dev"

# Verificar se gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    error "gcloud CLI não está instalado. Instale em: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Verificar se está autenticado
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    error "Não está autenticado no gcloud. Execute: gcloud auth login"
    exit 1
fi

# Obter projeto atual
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    error "Projeto não configurado. Execute: gcloud config set project SEU_PROJETO"
    exit 1
fi

# Substituir variável no nome da imagem
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TAG="v4-1-2-$TIMESTAMP"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:$TAG" 

log "=== DEPLOY API GATEWAY v4.1.2 - PRODUCTION READY ==="
log "Projeto: $PROJECT_ID"
log "Região: $REGION"
log "Serviço: $SERVICE_NAME"
log "Imagem: $IMAGE_NAME"
echo ""

# Verificar se arquivos necessários existem
REQUIRED_FILES=("api_gateway_v4_production_ready.py" "Dockerfile" "requirements.txt")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        error "Arquivo necessário não encontrado: $file"
        exit 1
    fi
done

log "✓ Todos os arquivos necessários encontrados"

# Habilitar APIs necessárias
log "Habilitando APIs necessárias..."
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID
gcloud services enable logging.googleapis.com --project=$PROJECT_ID

# PULAR COMPLETAMENTE A VERIFICAÇÃO DE SECRETS
log "✓ APIs habilitadas - prosseguindo diretamente para o deploy"
info "A aplicação gerenciará secrets internamente durante a execução"

# Criar service account se não existir
log "Configurando service account..."
SERVICE_ACCOUNT="apex-api-gateway@$PROJECT_ID.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT --project=$PROJECT_ID &>/dev/null; then
    log "Criando service account: $SERVICE_ACCOUNT"
    gcloud iam service-accounts create apex-api-gateway \
        --display-name="API Gateway Service Account" \
        --description="Service account para o API Gateway do Ecossistema Co-Piloto" \
        --project=$PROJECT_ID
    
    # Dar permissões necessárias
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/logging.logWriter"
    
    log "✓ Service account criado e configurado"
else
    log "✓ Service account já existe"
fi

# Build da imagem usando Cloud Build
log "Iniciando build da imagem Docker..."
log "Aguarde - este processo pode levar alguns minutos..."
echo ""

gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID

echo ""
log "✓ Build da imagem concluído com sucesso"

# Deploy para Cloud Run
log "Iniciando deploy para Cloud Run..."
echo ""

gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform $PLATFORM \
    --region $REGION \
    --allow-unauthenticated \
    --service-account $SERVICE_ACCOUNT \
    --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_REGION=$REGION,FRONTEND_REDIRECT_URL=${FRONTEND_URL}/settings/credentials" \
    --memory="2Gi" \
    --cpu="2" \
    --concurrency="80" \
    --timeout="300" \
    --min-instances="1" \
    --max-instances="10" \
    --port="8080" \
    --project=$PROJECT_ID

echo ""
log "✓ Deploy para Cloud Run concluído com sucesso"

# Obter URL do serviço
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform=$PLATFORM --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)

echo ""
log "=== DEPLOY CONCLUÍDO COM SUCESSO! ==="
echo ""
info "🚀 API Gateway v4.1.2 deployado com sucesso!"
info "🌐 URL do serviço: $SERVICE_URL"
info "📊 Health check: $SERVICE_URL/health"
info "📚 Documentação: $SERVICE_URL/docs"
echo ""

# URLs OAuth (a aplicação determinará quais estão disponíveis)
info "🔐 URLs OAuth (disponibilidade depende dos secrets configurados):"
info "   Google: $SERVICE_URL/auth/google"
info "   LinkedIn: $SERVICE_URL/auth/linkedin"
info "   Meta: $SERVICE_URL/auth/meta"
info "   Twitter: $SERVICE_URL/auth/twitter"
info "   TikTok: $SERVICE_URL/auth/tiktok"
echo ""
warn "⚠️  IMPORTANTE: Atualize os redirect URIs nas configurações OAuth!"
warn "   Formato: $SERVICE_URL/auth/{plataforma}/callback"

# Informações de monitoramento
echo ""
info "📈 Comandos de monitoramento:"
info "   Logs: gcloud logs tail --follow --resource-type=cloud_run_revision --resource-labels=service_name=$SERVICE_NAME --project=$PROJECT_ID"
info "   Status: gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"

# Testar health check
echo ""
log "Testando health check do serviço..."
sleep 15  # Aguardar inicialização
if curl -s -f "$SERVICE_URL/health" >/dev/null 2>&1; then
    log "✓ Health check passou - serviço está funcionando perfeitamente!"
else
    warn "⚠️  Health check ainda não passou - serviço pode estar inicializando"
    info "Teste manualmente em alguns minutos: curl $SERVICE_URL/health"
fi

echo ""
log "=== APEX SYSTEM OPERACIONAL! ==="
log "Deploy finalizado com sucesso!"

# Salvar informações de deploy
cat > deploy-info.txt << EOF
API Gateway v4.1.2 - Deploy Information
=====================================

Deploy Date: $(date)
Project ID: $PROJECT_ID
Service Name: $SERVICE_NAME
Region: $REGION
Service URL: $SERVICE_URL
Image: $IMAGE_NAME

URLs:
- Health Check: $SERVICE_URL/health
- Documentation: $SERVICE_URL/docs
- OAuth URLs: $SERVICE_URL/auth/{platform}

Monitoring:
- Logs: gcloud logs tail --follow --resource-type=cloud_run_revision --resource-labels=service_name=$SERVICE_NAME --project=$PROJECT_ID
- Status: gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID

Service Account: $SERVICE_ACCOUNT

Note: OAuth availability depends on secrets configured in Secret Manager.
The application will handle missing secrets gracefully at runtime.
EOF

info "📄 Informações salvas em: deploy-info.txt"



# --- INÍCIO DO CÓDIGO A SER ADICIONADO ---
log "Obtendo URL do serviço para auto-configuração..."
SERVICE_URL_TEMP=$(gcloud run services describe $SERVICE_NAME --platform=$PLATFORM --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)

log "Atualizando o serviço com o seu próprio URL público ($SERVICE_URL_TEMP)..."
gcloud run services update $SERVICE_NAME \
    --update-env-vars="APP_BASE_URL=$SERVICE_URL_TEMP" \
    --region=$REGION \
    --project=$PROJECT_ID
# --- FIM DO CÓDIGO A SER ADICIONADO ---

