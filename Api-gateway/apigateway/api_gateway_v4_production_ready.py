"""
API Gateway Inteligente - Ecossistema Co-Piloto Unificado v4.1.2 - PRODUCTION READY
REFATORAÇÃO CLOUD-NATIVE: Secret Manager + Logging Estruturado + Graceful Shutdown
Funcionalidades: IA, Load Balancing, Cache Adaptativo, Circuit Breaker + AUTO-OTIMIZAÇÃO + OAuth Completo
TODAS AS FUNCIONALIDADES PRESERVADAS INTEGRALMENTE
"""

import os
import sys
import time
import json
import hashlib
import asyncio
import statistics
import secrets
import urllib.parse
import signal
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple
from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
# Adicione JSONResponse às importações para permitir respostas de JSON quando necessário
from fastapi.responses import RedirectResponse, JSONResponse
# Importa instrumentador do Prometheus para métricas FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings # <<<--- ESTA É A LINHA CORRIGIDA
import uvicorn
import httpx
from collections import defaultdict, deque
import base64  # Garanta que esta linha esteja no topo do arquivo
from google.cloud import firestore  # <-- ADICIONE ESTA LINHA

# ============================================================================
# LOGGING ESTRUTURADO EM JSON PARA CLOUD LOGGING
# ============================================================================

import logging
import logging.config

class JSONFormatter(logging.Formatter):
    """Formatter para logs estruturados em JSON"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "service": "api-gateway-inteligente",
            "version": "4.1.2"
        }
        
        # Adicionar informações extras se disponíveis
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'platform'):
            log_entry["platform"] = record.platform
        if hasattr(record, 'service_name'):
            log_entry["service_name"] = record.service_name
        if hasattr(record, 'response_time'):
            log_entry["response_time_ms"] = record.response_time
        if hasattr(record, 'status_code'):
            log_entry["status_code"] = record.status_code
            
        # Adicionar stack trace para erros
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, ensure_ascii=False)

# Configurar logging estruturado
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JSONFormatter,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "httpx": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Inicializa o cliente do Firestore
try:
    db = firestore.Client()
    logger.info("Cliente Firestore inicializado com sucesso.")
except Exception as e:
    logger.error(f"Falha ao inicializar cliente Firestore: {e}")
    db = None

# ============================================================================
# CONFIGURAÇÕES CENTRALIZADAS COM PYDANTIC BASESETTINGS
# ============================================================================

class Settings(BaseSettings):
    """Configurações centralizadas da aplicação"""
    
    # Configurações básicas
    app_name: str = Field(default="API Gateway Inteligente", env="APP_NAME")
    app_version: str = Field(default="4.1.2", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Configurações de servidor
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8080, env="PORT")
    app_base_url: str = Field(default="http://localhost:8080", env="APP_BASE_URL")

    # URL de redirecionamento para o frontend após o sucesso da autenticação
    # Esta URL é usada para encaminhar o usuário de volta ao aplicativo de frontend com o token de autorização
    frontend_redirect_url: str = Field(default="http://localhost:3001/settings/credentials", env="FRONTEND_REDIRECT_URL")
    
    # Configurações do Google Cloud
    google_cloud_project: str = Field(default="", env="GOOGLE_CLOUD_PROJECT")
    google_cloud_region: str = Field(default="southamerica-east1", env="GOOGLE_CLOUD_REGION")
    
    # Configurações de cache
    cache_ttl_default: int = Field(default=300, env="CACHE_TTL_DEFAULT")
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    # Configurações de circuit breaker
    circuit_breaker_timeout: int = Field(default=60, env="CIRCUIT_BREAKER_TIMEOUT")
    circuit_breaker_threshold: int = Field(default=5, env="CIRCUIT_BREAKER_THRESHOLD")
    
    # Configurações de auto-tuning
    auto_tuning_interval: int = Field(default=300, env="AUTO_TUNING_INTERVAL")
    auto_tuning_enabled: bool = Field(default=True, env="AUTO_TUNING_ENABLED")
    
    # URLs dos serviços do ecossistema
    service_api_gateway_url: str = Field(default="http://localhost:8000", env="SERVICE_API_GATEWAY_URL")
    service_rl_engine_url: str = Field(default="http://localhost:8001", env="SERVICE_RL_ENGINE_URL")
    service_ecosystem_platform_url: str = Field(default="http://localhost:8002", env="SERVICE_ECOSYSTEM_PLATFORM_URL")
    service_creative_studio_url: str = Field(default="http://localhost:8003", env="SERVICE_CREATIVE_STUDIO_URL")
    service_immune_system_url: str = Field(default="http://localhost:8007", env="SERVICE_IMMUNE_SYSTEM_URL")
    service_future_casting_url: str = Field(default="http://localhost:8008", env="SERVICE_FUTURE_CASTING_URL")
    service_proactive_conversation_url: str = Field(default="http://localhost:8009", env="SERVICE_PROACTIVE_CONVERSATION_URL")
    
    # Configurações OAuth 2.0 (fallback para variáveis de ambiente)
    google_client_id: str = Field(default="", env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", env="GOOGLE_CLIENT_SECRET")
    linkedin_client_id: str = Field(default="", env="LINKEDIN_CLIENT_ID")
    linkedin_client_secret: str = Field(default="", env="LINKEDIN_CLIENT_SECRET")
    meta_client_id: str = Field(default="", env="META_CLIENT_ID")
    meta_client_secret: str = Field(default="", env="META_CLIENT_SECRET")
    twitter_client_id: str = Field(default="", env="TWITTER_CLIENT_ID")
    twitter_client_secret: str = Field(default="", env="TWITTER_CLIENT_SECRET")
    tiktok_client_id: str = Field(default="", env="TIKTOK_CLIENT_ID")
    tiktok_client_secret: str = Field(default="", env="TIKTOK_CLIENT_SECRET")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Instância global das configurações
settings = Settings()

# ============================================================================
# INTEGRAÇÃO COM GOOGLE SECRET MANAGER
# ============================================================================

class SecretManager:
    """Gerenciador de secrets do Google Cloud"""
    
    def __init__(self):
        self.client = None
        self.project_id = settings.google_cloud_project
        self.is_production = settings.environment == "production"
        
        if self.is_production and self.project_id:
            try:
                from google.cloud import secretmanager
                self.client = secretmanager.SecretManagerServiceClient()
                logger.info("Google Secret Manager inicializado", extra={"project_id": self.project_id})
            except ImportError:
                logger.warning("Google Cloud Secret Manager não disponível - usando variáveis de ambiente")
                self.client = None
            except Exception as e:
                logger.error(f"Erro ao inicializar Secret Manager: {e}")
                self.client = None
    
    async def get_secret(self, secret_name: str, version: str = "latest") -> Optional[str]:
        """Obter secret do Google Secret Manager"""
        if not self.client or not self.project_id:
            logger.debug(f"Secret Manager não disponível - usando variável de ambiente para {secret_name}")
            return None
        
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
            response = self.client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8").strip()
                        
            logger.info(f"Secret obtido com sucesso", extra={
                "secret_name": secret_name,
                "version": version
            })
            return secret_value
            
        except Exception as e:
            logger.error(f"Erro ao obter secret {secret_name}: {e}")
            return None
    
    async def get_oauth_credentials(self) -> Dict[str, Dict[str, str]]:
        """Obter todas as credenciais OAuth do Secret Manager ou variáveis de ambiente"""
        credentials = {}
        
        platforms = {
            "google": ("google-client-id", "google-client-secret"),
            "linkedin": ("linkedin-client-id", "linkedin-client-secret"),
            "meta": ("meta-client-id", "meta-client-secret"),
            "twitter": ("twitter-client-id", "twitter-client-secret"),
            "tiktok": ("tiktok-client-id", "tiktok-client-secret")
        }
        
        for platform, (id_secret, secret_secret) in platforms.items():
            if self.is_production and self.client:
                # Tentar obter do Secret Manager
                client_id = await self.get_secret(id_secret)
                client_secret = await self.get_secret(secret_secret)
            else:
                # Usar variáveis de ambiente
                client_id = getattr(settings, f"{platform}_client_id", "")
                client_secret = getattr(settings, f"{platform}_client_secret", "")
            
            if client_id and client_secret:
                credentials[platform] = {
                    "client_id": client_id,
                    "client_secret": client_secret
                }
                logger.info(f"Credenciais OAuth configuradas", extra={"platform": platform})
            else:
                logger.warning(f"Credenciais OAuth não encontradas", extra={"platform": platform})
        
        return credentials

# Instância global do Secret Manager
secret_manager = SecretManager()

# ============================================================================
# GRACEFUL SHUTDOWN - SIGNAL HANDLERS
# ============================================================================

class GracefulShutdown:
    """Gerenciador de desligamento suave"""
    
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.tasks_running = set()
        self.is_shutting_down = False
        
    def setup_signal_handlers(self):
        """Configurar handlers para sinais de sistema"""
        if sys.platform != "win32":
            # Unix/Linux signal handlers
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            logger.info("Signal handlers configurados para SIGTERM e SIGINT")
        else:
            # Windows signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            logger.info("Signal handler configurado para SIGINT (Windows)")
    
    def _signal_handler(self, signum, frame):
        """Handler para sinais de desligamento"""
        signal_name = signal.Signals(signum).name
        logger.info(f"Sinal {signal_name} recebido - iniciando desligamento suave")
        
        # Marcar que estamos desligando
        self.is_shutting_down = True
        
        # Sinalizar para todas as tarefas pararem
        asyncio.create_task(self._shutdown())
    
    async def _shutdown(self):
        """Executar desligamento suave"""
        logger.info("Iniciando processo de desligamento suave")
        
        # Aguardar conclusão de tarefas em andamento
        if self.tasks_running:
            logger.info(f"Aguardando conclusão de {len(self.tasks_running)} tarefas")
            await asyncio.gather(*self.tasks_running, return_exceptions=True)
        
        # Sinalizar que o desligamento está completo
        self.shutdown_event.set()
        logger.info("Desligamento suave concluído")
    
    def add_task(self, task):
        """Adicionar tarefa ao conjunto de tarefas monitoradas"""
        self.tasks_running.add(task)
        task.add_done_callback(self.tasks_running.discard)
    
    async def wait_for_shutdown(self):
        """Aguardar sinal de desligamento"""
        await self.shutdown_event.wait()

# Instância global do graceful shutdown
graceful_shutdown = GracefulShutdown()

# ============================================================================
# MODELOS DE DADOS (PRESERVADOS INTEGRALMENTE)
# ============================================================================

class RouteRequest(BaseModel):
    service: str
    path: str
    data: Optional[Dict[str, Any]] = {}
    method: Optional[str] = "POST"
    use_cache: Optional[bool] = True
    force_rl_decision: Optional[bool] = False

class ServiceHealth(BaseModel):
    name: str
    url: str
    status: str
    response_time: float
    error_count: int
    last_check: datetime

class AutoTuningDecision(BaseModel):
    component: str
    parameter: str
    old_value: Any
    new_value: Any
    reason: str
    confidence: float
    timestamp: datetime

class OAuthTokenResponse(BaseModel):
    platform: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = "Bearer"
    scope: Optional[str] = None
    timestamp: datetime

# ============================================================================
# CONFIGURAÇÃO OAUTH 2.0 DINÂMICA - TODAS AS 6 PLATAFORMAS
# ============================================================================

async def get_oauth_config() -> Dict[str, Dict[str, str]]:
    """Obter configuração OAuth dinâmica do Secret Manager ou variáveis de ambiente"""
    credentials = await secret_manager.get_oauth_credentials()
    
    # Detectar URL base do serviço a partir de uma variável de ambiente
    base_url = settings.app_base_url
    
    oauth_config = {}
    
    # Configuração para cada plataforma
    platform_configs = {
        "google": {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "scope": "https://www.googleapis.com/auth/adwords https://www.googleapis.com/auth/analytics.readonly",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        },
        "linkedin": {
            "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
            "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
            "scope": "r_ads,r_ads_reporting,rw_ads",
            "response_type": "code"
        },
        "meta": {
            "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
            "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
            "scope": "ads_management,ads_read,business_management",
            "response_type": "code"
        },
        "twitter": {
            # Configuração para autenticação OAuth 2.0 com PKCE (Twitter API v2)
            "auth_url": "https://twitter.com/i/oauth2/authorize",
            "token_url": "https://api.twitter.com/2/oauth2/token",
            "scope": "tweet.read users.read offline.access",
            "response_type": "code",
            "code_challenge_method": "S256"
        },
        "tiktok": {
            "auth_url": "https://www.tiktok.com/auth/authorize/",
            "token_url": "https://open-api.tiktok.com/oauth/access_token/",
            "scope": "user.info.basic,video.list",
            "response_type": "code"
        }
    }
    
    # Construir configuração completa para cada plataforma
    for platform, config in platform_configs.items():
        if platform in credentials:
            oauth_config[platform] = {
                **config,
                "client_id": credentials[platform]["client_id"],
                "client_secret": credentials[platform]["client_secret"],
                "redirect_uri": f"{base_url}/auth/{platform}/callback"
            }
    
    return oauth_config

# ============================================================================
# VARIÁVEIS GLOBAIS DE ESTADO (PRESERVADAS INTEGRALMENTE)
# ============================================================================

# Métricas globais
start_time = time.time()
total_requests = 0
gateway_requests = 0
health_checks = 0
oauth_authorizations = 0
cache_hits = 0
cache_misses = 0
circuit_breaker_trips = 0
rl_decisions_used = 0
auto_tuning_decisions = 0

# Cache adaptativo
cache_storage: Dict[str, Any] = {}
cache_metadata: Dict[str, Dict[str, Any]] = {}

# Circuit breaker state
circuit_breaker_state: Dict[str, Dict[str, Any]] = {}

# Service health tracking
service_health: Dict[str, Dict[str, Any]] = {}
service_instances: Dict[str, List[str]] = defaultdict(list)

# Auto-tuning history
auto_tuning_history: deque = deque(maxlen=1000)

# REMOVIDO: oauth_tokens, oauth_states, oauth_code_verifiers (migrados para Firestore)

def get_services_config():
    """Configuração dinâmica dos serviços do ecossistema"""
    return {
        "api-gateway": {
            "instances": [
                {"url": settings.service_api_gateway_url, "weight": 1.0, "status": "active"}
            ],
            "endpoints": [
                "/health", "/status", "/metrics", "/api/v1/route", "/api/v1/services",
                "/api/v1/ecosystem/health", "/api/v1/auto-tuning/status",
                "/api/v1/cache/stats", "/api/v1/circuit-breaker/status"
            ],
            "cache_ttl": 120,
            "circuit_breaker_enabled": True,
            "description": "Gateway principal do ecossistema"
        },
        "rl-engine": {
            "instances": [
                {"url": settings.service_rl_engine_url, "weight": 1.0, "status": "active"}
            ],
            "endpoints": [
                "/health", "/metrics", "/api/v1/learn", "/api/v1/actions/generate",
                "/api/v1/strategies", "/api/v1/performance", "/api/v1/backup",
                "/api/v1/restore", "/api/v1/config", "/api/v1/debug/strategies",
                "/api/v1/debug/experiences", "/api/v1/strategies/reset",
                "/api/v1/experiences/reset"
            ],
            "cache_ttl": 60,
            "circuit_breaker_enabled": True,
            "description": "Sistema de aprendizado por reforço"
        },
        "ecosystem-platform": {
            "instances": [
                {"url": settings.service_ecosystem_platform_url, "weight": 1.0, "status": "active"}
            ],
            "endpoints": [
                "/health", "/metrics", "/api/v1/status", "/api/v1/services",
                "/api/v1/analytics", "/api/v1/insights"
            ],
            "cache_ttl": 300,
            "circuit_breaker_enabled": True,
            "description": "Plataforma central do ecossistema"
        },
        "creative-studio": {
            "instances": [
                {"url": settings.service_creative_studio_url, "weight": 1.0, "status": "active"}
            ],
            "endpoints": [
                "/health", "/metrics", "/api/v1/generate", "/api/v1/content",
                "/api/v1/intelligence", "/api/v1/analysis"
            ],
            "cache_ttl": 180,
            "circuit_breaker_enabled": True,
            "description": "Sistema de geração de conteúdo inteligente"
        },
        "immune-system": {
            "instances": [
                {"url": settings.service_immune_system_url, "weight": 1.0, "status": "active"}
            ],
            "endpoints": [
                "/health", "/health/deep", "/api/v4/autonomous/status",
                "/api/v4/autonomous/metrics", "/api/v4/autonomous/actions",
                "/api/v4/mitigation/status"
            ],
            "cache_ttl": 30,
            "circuit_breaker_enabled": True,
            "description": "Sistema autônomo de auto-scaling e mitigação v4.0"
        },
        "future-casting": {
            "instances": [
                {"url": settings.service_future_casting_url, "weight": 1.0, "status": "active"}
            ],
            "endpoints": [
                "/health", "/health/deep", "/api/v4/predictions", "/api/v4/actions",
                "/api/v4/status", "/api/v4/orchestration/coordinate"
            ],
            "cache_ttl": 45,
            "circuit_breaker_enabled": True,
            "description": "Sistema de previsões executáveis v4.0"
        },
        "proactive-conversation": {
            "instances": [
                {"url": settings.service_proactive_conversation_url, "weight": 1.0, "status": "active"}
            ],
            "endpoints": [
                "/health", "/health/deep", "/api/v4/orchestration/status",
                "/api/v4/ecosystem/state", "/api/v4/orchestration/start",
                "/api/v4/orchestration/stop"
            ],
            "cache_ttl": 20,
            "circuit_breaker_enabled": True,
            "description": "Orquestrador autônomo do ecossistema v4.0"
        }
    }

# Configuração dinâmica dos serviços
SERVICES = get_services_config()

# Mapeamento de contextos de roteamento para contextos conhecidos pelo RL Engine
CONTEXT_MAPPING = {
    "api_gateway_routing": "api_routing",
    "load_balancing": "load_balancing", 
    "cache_optimization": "cache_management",
    "circuit_breaker": "circuit_breaker",
    "auto_tuning": "auto_optimization",
    "ecosystem_coordination": "ecosystem_management",
    "autonomous_scaling": "scaling_decisions",
    "predictive_actions": "prediction_execution",
    "orchestration": "service_orchestration"
}

# ============================================================================
# FUNÇÕES OAUTH 2.0 EXPANDIDAS (REFATORADAS PARA FIRESTORE)
# ============================================================================

def generate_oauth_state() -> str:
    """Gerar estado único para OAuth 2.0"""
    return secrets.token_urlsafe(32)

def generate_code_verifier() -> str:
    """Gerar code verifier para PKCE (Twitter)"""
    return secrets.token_urlsafe(32)

def generate_code_challenge(verifier: str) -> str:
    """Gerar code challenge para PKCE (Twitter)"""
    import base64
    import hashlib
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

async def build_oauth_url(platform: str, state: str) -> str:
    """Construir URL de autorização OAuth para qualquer plataforma"""
    oauth_config = await get_oauth_config()
    
    if platform not in oauth_config:
        raise HTTPException(status_code=500, detail=f"OAuth não configurado para {platform}")
    
    config = oauth_config[platform]
    
    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "scope": config["scope"],
        "response_type": config["response_type"],
        "state": state
    }
    
    # Parâmetros específicos do Google
    if platform == "google":
        params["access_type"] = config["access_type"]
        params["prompt"] = config["prompt"]
    
    # Parâmetros específicos do Twitter (PKCE)
    elif platform == "twitter":
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        
        # Salvar code_verifier no Firestore junto com o state
        if db:
            try:
                state_doc_ref = db.collection('oauth_pending_states').document(state)
                state_doc_ref.set({
                    'platform': platform,
                    'code_verifier': code_verifier,
                    'expires_at': datetime.now(timezone.utc) + timedelta(minutes=10),
                    'timestamp': datetime.now()
                })
            except Exception as e:
                logger.error(f"Erro ao salvar code_verifier no Firestore: {e}")
                raise HTTPException(status_code=500, detail="Erro interno ao processar autenticação")
        
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = config["code_challenge_method"]
    
    query_string = urllib.parse.urlencode(params)
    return f"{config['auth_url']}?{query_string}"

async def exchange_code_for_token(platform: str, code: str, state: str = None) -> Dict[str, Any]:
    """Trocar código de autorização por token de acesso para qualquer plataforma"""

    # Obter configuração de OAuth e validar se a plataforma está configurada
    oauth_config = await get_oauth_config()
    if platform not in oauth_config:
        raise HTTPException(status_code=500, detail=f"OAuth não configurado para {platform}")

    config = oauth_config[platform]
    token_url = config["token_url"]

    # Dados básicos exigidos pela maioria das plataformas
    token_data: Dict[str, Any] = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": config["redirect_uri"],
        "client_id": config["client_id"],
    }
    headers: Dict[str, str] = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Tratamento específico para o Twitter API v2 com PKCE
    if platform == "twitter":
        if not state or not db:
            raise HTTPException(status_code=400, detail="Estado OAuth ou Firestore inválido para o fluxo PKCE do Twitter.")

        # Recuperar code_verifier do Firestore
        try:
            state_doc_ref = db.collection('oauth_pending_states').document(state)
            state_doc = state_doc_ref.get()
            
            if not state_doc.exists:
                raise HTTPException(status_code=400, detail="Estado OAuth inválido ou expirado")
            
            state_data = state_doc.to_dict()
            if state_data['platform'] != platform:
                raise HTTPException(status_code=400, detail="Estado OAuth não corresponde à plataforma")
            
            if datetime.now(timezone.utc) > state_data['expires_at']:
                # Limpar estado expirado
                state_doc_ref.delete()
                raise HTTPException(status_code=400, detail="Estado OAuth expirado")
            
            token_data["code_verifier"] = state_data['code_verifier']
            
            # Excluir o documento após uso
            state_doc_ref.delete()
            
        except Exception as e:
            logger.error(f"Erro ao recuperar code_verifier do Firestore: {e}")
            raise HTTPException(status_code=500, detail="Erro interno durante a autenticação")

        # A API do Twitter v2 exige autenticação Basic para a troca de token
        auth_string = f"{config['client_id']}:{config['client_secret']}"
        auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        headers["Authorization"] = f"Basic {auth_b64}"
    else:
        # Outras plataformas (Google, Meta, LinkedIn) geralmente enviam o secret no corpo
        token_data["client_secret"] = config["client_secret"]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Iniciando requisição de token para {platform.upper()}", extra={"platform": platform, "url": token_url})
            response = await client.post(token_url, data=token_data, headers=headers)

            response.raise_for_status()  # Lança uma exceção para respostas 4xx ou 5xx

            logger.info(f"Token recebido com sucesso de {platform.upper()}", extra={"platform": platform})
            return response.json()

    except httpx.HTTPStatusError as e:
        # Log detalhado do erro da API
        logger.error(f"Erro na troca de token para {platform.upper()}: Status {e.response.status_code}", extra={
            "platform": platform,
            "status_code": e.response.status_code,
            "response_body": e.response.text,
            "request_url": str(e.request.url)
        })
        raise HTTPException(status_code=502, detail=f"Falha na comunicação com a API do {platform.capitalize()}: {e.response.text}")
    except Exception as e:
        logger.error(f"Erro inesperado na troca de token para {platform.upper()}", extra={"platform": platform, "error": str(e)})
        raise HTTPException(status_code=500, detail="Erro interno durante a autenticação.")

def store_oauth_token(platform: str, token_data: Dict[str, Any]) -> str:
    """Armazenar token OAuth no Firestore e retornar ID único"""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore não disponível")
    
    # Para fins de demonstração, usamos um ID de usuário fixo
    # Em produção, isso viria do contexto de autenticação
    DUMMY_USER_ID = "user_12345"
    
    try:
        # Criar documento no caminho user_tokens/{DUMMY_USER_ID}/tokens/{platform}
        token_doc_ref = db.collection('user_tokens').document(DUMMY_USER_ID).collection('tokens').document(platform)
        
        token_response = OAuthTokenResponse(
            platform=platform,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in"),
            token_type=token_data.get("token_type", "Bearer"),
            scope=token_data.get("scope"),
            timestamp=datetime.now()
        )
        
        # Salvar no Firestore
        token_doc_ref.set(token_response.dict())
        
        # Gerar ID único para compatibilidade com o frontend
        token_id = secrets.token_urlsafe(16)
        
        logger.info(f"Token OAuth salvo no Firestore", extra={
            "platform": platform,
            "user_id": DUMMY_USER_ID,
            "token_id": token_id
        })
        
        return token_id
        
    except Exception as e:
        logger.error(f"Erro ao salvar token no Firestore: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao salvar token")



# ============================================================================
# AUTO-TUNING ENGINE - COMPONENTES PRINCIPAIS (PRESERVADOS INTEGRALMENTE)
# ============================================================================

class CacheTuner:
    """Otimizador automático de cache"""
    
    def __init__(self):
        self.cache_hit_rates = defaultdict(lambda: deque(maxlen=100))
        self.cache_response_times = defaultdict(lambda: deque(maxlen=100))
        self.last_optimization = {}
        
    def record_cache_metrics(self, service: str, hit: bool, response_time: float):
        """Registrar métricas de cache"""
        self.cache_hit_rates[service].append(1 if hit else 0)
        self.cache_response_times[service].append(response_time)
        
    def should_optimize_cache(self, service: str) -> bool:
        """Verificar se cache precisa de otimização"""
        if service not in self.cache_hit_rates:
            return False
            
        hit_rate = sum(self.cache_hit_rates[service]) / len(self.cache_hit_rates[service])
        avg_response_time = sum(self.cache_response_times[service]) / len(self.cache_response_times[service])
        
        # Otimizar se hit rate baixo ou response time alto
        return hit_rate < 0.6 or avg_response_time > 0.5
        
    def optimize_cache_ttl(self, service: str) -> Optional[int]:
        """Otimizar TTL do cache"""
        if not self.should_optimize_cache(service):
            return None
            
        current_ttl = SERVICES[service]["cache_ttl"]
        hit_rate = sum(self.cache_hit_rates[service]) / len(self.cache_hit_rates[service])
        
        if hit_rate < 0.4:
            # Hit rate muito baixo - aumentar TTL
            new_ttl = min(current_ttl * 1.5, 600)
        elif hit_rate > 0.8:
            # Hit rate alto - pode diminuir TTL para dados mais frescos
            new_ttl = max(current_ttl * 0.8, 30)
        else:
            new_ttl = current_ttl
            
        if abs(new_ttl - current_ttl) > 10:  # Mudança significativa
            SERVICES[service]["cache_ttl"] = int(new_ttl)
            self.last_optimization[service] = datetime.now()
            return int(new_ttl)
            
        return None

class CircuitBreakerTuner:
    """Otimizador automático de circuit breaker"""
    
    def __init__(self):
        self.failure_patterns = defaultdict(lambda: deque(maxlen=200))
        self.success_patterns = defaultdict(lambda: deque(maxlen=200))
        
    def record_circuit_breaker_metrics(self, service: str, success: bool, response_time: float):
        """Registrar métricas de circuit breaker"""
        if success:
            self.success_patterns[service].append(response_time)
        else:
            self.failure_patterns[service].append(response_time)
            
    def optimize_circuit_breaker_threshold(self, service: str) -> Optional[int]:
        """Otimizar threshold do circuit breaker"""
        if service not in circuit_breaker_state:
            return None
            
        failure_count = len(self.failure_patterns[service])
        success_count = len(self.success_patterns[service])
        
        if failure_count + success_count < 50:  # Dados insuficientes
            return None
            
        failure_rate = failure_count / (failure_count + success_count)
        current_threshold = circuit_breaker_state[service]["threshold"]
        
        if failure_rate > 0.2:  # Taxa de falha alta
            new_threshold = max(current_threshold - 1, 2)
        elif failure_rate < 0.05:  # Taxa de falha baixa
            new_threshold = min(current_threshold + 1, 10)
        else:
            new_threshold = current_threshold
            
        if new_threshold != current_threshold:
            circuit_breaker_state[service]["threshold"] = new_threshold
            return new_threshold
            
        return None

class LoadBalancerTuner:
    """Otimizador automático de load balancer"""
    
    def __init__(self):
        self.response_time_patterns = defaultdict(lambda: deque(maxlen=100))
        self.success_rate_patterns = defaultdict(lambda: deque(maxlen=100))
        
    def record_load_balancer_metrics(self, service_url: str, response_time: float, success: bool):
        """Registrar métricas de load balancer"""
        self.response_time_patterns[service_url].append(response_time)
        self.success_rate_patterns[service_url].append(1 if success else 0)
        
    def optimize_service_weights(self) -> Dict[str, float]:
        """Otimizar pesos dos serviços"""
        optimizations = {}
        
        for service_url in self.response_time_patterns:
            if len(self.response_time_patterns[service_url]) < 20:
                continue
                
            avg_response_time = sum(self.response_time_patterns[service_url]) / len(self.response_time_patterns[service_url])
            success_rate = sum(self.success_rate_patterns[service_url]) / len(self.success_rate_patterns[service_url])
            
            # Calcular peso baseado em performance
            performance_score = success_rate / max(avg_response_time, 0.1)
            new_weight = min(max(performance_score, 0.1), 2.0)
            
            current_weight = service_health[service_url]["weight"]
            if abs(new_weight - current_weight) > 0.1:
                service_health[service_url]["weight"] = new_weight
                optimizations[service_url] = new_weight
                
        return optimizations

class AutoTuningEngine:
    """Engine principal de auto-otimização"""
    
    def __init__(self):
        self.cache_tuner = CacheTuner()
        self.cb_tuner = CircuitBreakerTuner()
        self.lb_tuner = LoadBalancerTuner()
        self.running = settings.auto_tuning_enabled
        self.optimization_interval = settings.auto_tuning_interval
        self.last_optimization = datetime.now()
        
    async def start_auto_tuning(self):
        """Iniciar auto-otimização em background"""
        while self.running and not graceful_shutdown.is_shutting_down:
            try:
                await self.run_optimization_cycle()
                await asyncio.sleep(self.optimization_interval)
            except Exception as e:
                logger.error("Erro no auto-tuning", extra={"error": str(e)})
                await asyncio.sleep(60)
                
    async def run_optimization_cycle(self):
        """Executar ciclo de otimização"""
        global auto_tuning_decisions
        
        logger.info("Iniciando ciclo de auto-otimização")
        decisions_made = 0
        
        # Otimizar cache para cada serviço
        for service in SERVICES:
            new_ttl = self.cache_tuner.optimize_cache_ttl(service)
            if new_ttl:
                decision = AutoTuningDecision(
                    component="cache",
                    parameter="ttl",
                    old_value=SERVICES[service]["cache_ttl"],
                    new_value=new_ttl,
                    reason=f"Otimização baseada em hit rate e response time",
                    confidence=0.8,
                    timestamp=datetime.now()
                )
                auto_tuning_history.append(decision)
                decisions_made += 1
                
        # Otimizar circuit breakers
        for service in circuit_breaker_state:
            new_threshold = self.cb_tuner.optimize_circuit_breaker_threshold(service)
            if new_threshold:
                decision = AutoTuningDecision(
                    component="circuit_breaker",
                    parameter="threshold",
                    old_value=circuit_breaker_state[service]["threshold"],
                    new_value=new_threshold,
                    reason=f"Ajuste baseado em taxa de falhas",
                    confidence=0.7,
                    timestamp=datetime.now()
                )
                auto_tuning_history.append(decision)
                decisions_made += 1
                
        # Otimizar load balancer
        weight_optimizations = self.lb_tuner.optimize_service_weights()
        for service_url, new_weight in weight_optimizations.items():
            decision = AutoTuningDecision(
                component="load_balancer",
                parameter="weight",
                old_value=service_health[service_url]["weight"],
                new_value=new_weight,
                reason=f"Ajuste baseado em performance",
                confidence=0.75,
                timestamp=datetime.now()
            )
            auto_tuning_history.append(decision)
            decisions_made += 1
            
        auto_tuning_decisions += decisions_made
        self.last_optimization = datetime.now()
        
        if decisions_made > 0:
            logger.info("Ciclo de auto-otimização concluído", extra={
                "decisions_made": decisions_made,
                "total_decisions": auto_tuning_decisions
            })

# Instância global do auto-tuning engine
auto_tuning_engine = AutoTuningEngine()

# ============================================================================
# FUNÇÕES DE CACHE (PRESERVADAS INTEGRALMENTE)
# ============================================================================

def get_cache_key(service: str, path: str, data: Dict[str, Any]) -> str:
    """Gerar chave única para cache"""
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.md5(f"{service}:{path}:{data_str}".encode()).hexdigest()

def is_cache_valid(cache_key: str, ttl: int) -> bool:
    """Verificar se entrada do cache ainda é válida"""
    if cache_key not in cache_metadata:
        return False
    
    cache_time = cache_metadata[cache_key]["timestamp"]
    return (datetime.now() - cache_time).total_seconds() < ttl

def get_from_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """Obter dados do cache"""
    global cache_hits, cache_misses
    
    if cache_key in cache_storage:
        cache_hits += 1
        return cache_storage[cache_key]
    else:
        cache_misses += 1
        return None

def store_in_cache(cache_key: str, data: Dict[str, Any], ttl: int):
    """Armazenar dados no cache"""
    global cache_storage, cache_metadata
    
    # Limpar cache se exceder tamanho máximo
    if len(cache_storage) >= settings.cache_max_size:
        # Remover entrada mais antiga
        oldest_key = min(cache_metadata.keys(), key=lambda k: cache_metadata[k]["timestamp"])
        del cache_storage[oldest_key]
        del cache_metadata[oldest_key]
    
    cache_storage[cache_key] = data
    cache_metadata[cache_key] = {
        "timestamp": datetime.now(),
        "ttl": ttl,
        "access_count": 0
    }

# ============================================================================
# FUNÇÕES DE CIRCUIT BREAKER (PRESERVADAS INTEGRALMENTE)
# ============================================================================

def initialize_circuit_breaker(service: str):
    """Inicializar circuit breaker para um serviço"""
    if service not in circuit_breaker_state:
        circuit_breaker_state[service] = {
            "state": "CLOSED",  # CLOSED, OPEN, HALF_OPEN
            "failure_count": 0,
            "success_count": 0,
            "last_failure": None,
            "next_attempt": None,
            "threshold": settings.circuit_breaker_threshold,
            "success_threshold": 3
        }

def get_circuit_breaker_state(service: str) -> str:
    """Obter estado atual do circuit breaker"""
    initialize_circuit_breaker(service)
    return circuit_breaker_state[service]["state"]

def should_circuit_breaker_allow(service: str) -> bool:
    """Verificar se circuit breaker permite requisição"""
    cb_state = circuit_breaker_state[service]
    
    if cb_state["state"] == "CLOSED":
        return True
    elif cb_state["state"] == "OPEN":
        if cb_state["next_attempt"] and datetime.now() > cb_state["next_attempt"]:
            cb_state["state"] = "HALF_OPEN"
            cb_state["success_count"] = 0
            return True
        return False
    elif cb_state["state"] == "HALF_OPEN":
        return True
    
    return False

def record_success(service: str, response_time: float):
    """Registrar sucesso para circuit breaker"""
    cb_state = circuit_breaker_state[service]
    
    if cb_state["state"] == "HALF_OPEN":
        cb_state["success_count"] += 1
        if cb_state["success_count"] >= cb_state["success_threshold"]:
            cb_state["state"] = "CLOSED"
            cb_state["failure_count"] = 0
    elif cb_state["state"] == "CLOSED":
        cb_state["failure_count"] = max(0, cb_state["failure_count"] - 1)
    
    # Registrar métricas para auto-tuning
    auto_tuning_engine.cb_tuner.record_circuit_breaker_metrics(service, True, response_time)

def record_failure(service: str):
    """Registrar falha para circuit breaker"""
    global circuit_breaker_trips
    
    cb_state = circuit_breaker_state[service]
    cb_state["failure_count"] += 1
    cb_state["last_failure"] = datetime.now()
    
    if cb_state["state"] == "HALF_OPEN":
        cb_state["state"] = "OPEN"
        cb_state["next_attempt"] = datetime.now() + timedelta(seconds=settings.circuit_breaker_timeout)
        circuit_breaker_trips += 1
    elif cb_state["state"] == "CLOSED" and cb_state["failure_count"] >= cb_state["threshold"]:
        cb_state["state"] = "OPEN"
        cb_state["next_attempt"] = datetime.now() + timedelta(seconds=settings.circuit_breaker_timeout)
        circuit_breaker_trips += 1
    
    # Registrar métricas para auto-tuning
    auto_tuning_engine.cb_tuner.record_circuit_breaker_metrics(service, False, 30.0)

def select_service_instance(service: str) -> str:
    """Selecionar instância do serviço usando load balancing inteligente"""
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")
    
    instances = SERVICES[service]["instances"]
    if not instances:
        raise HTTPException(status_code=503, detail=f"No instances available for service '{service}'")
    
    # Load balancing baseado em peso e saúde
    best_instance = None
    best_score = -1
    
    for instance in instances:
        url = instance["url"]
        health = service_health[url]
        
        # Calcular score baseado em peso, response time e success rate
        weight = health["weight"]
        avg_response_time = sum(health["response_times"]) / len(health["response_times"]) if health["response_times"] else 0.1
        success_rate = health["success_rate"]
        
        score = (weight * success_rate) / max(avg_response_time, 0.01)
        
        if score > best_score:
            best_score = score
            best_instance = instance
    
    return best_instance["url"] if best_instance else instances[0]["url"]

async def call_rl_engine(context: str, current_state: Dict[str, Any]) -> Dict[str, Any]:
    """Chamar RL Engine para decisão inteligente"""
    try:
        # Mapear contexto para formato conhecido pelo RL Engine
        rl_context = CONTEXT_MAPPING.get(context, context)
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.service_rl_engine_url}/api/v1/actions/generate",
                json={
                    "context": rl_context,
                    "current_state": current_state,
                    "require_learning": True
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("RL Engine retornou status não-200", extra={
                    "status_code": response.status_code
                })
                return {"action": "default", "confidence": 0.5}
                
    except Exception as e:
        logger.error("Erro ao chamar RL Engine", extra={"error": str(e)})
        return {"action": "default", "confidence": 0.5}

# ============================================================================
# APLICAÇÃO FASTAPI
# ============================================================================

app = FastAPI(
    title="API Gateway Inteligente - Ecossistema Unificado",
    description="Gateway principal do Ecossistema Co-Piloto com 7 serviços integrados + OAuth 2.0 (6 plataformas) - PRODUCTION READY",
    version=settings.app_version
)

# Adiciona o instrumentador do Prometheus para expor o endpoint /metrics
Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Inicializar serviços em background"""
    logger.info("Iniciando API Gateway do Ecossistema Unificado", extra={
        "version": settings.app_version,
        "environment": settings.environment,
        "total_services": len(SERVICES)
    })
    
    # Configurar signal handlers para graceful shutdown
    graceful_shutdown.setup_signal_handlers()
    
    # Log dos serviços integrados
    for service_name, config in SERVICES.items():
        logger.info("Serviço registrado", extra={
            "service_name": service_name,
            "url": config['instances'][0]['url'],
            "description": config['description']
        })
    
    # Verificar configurações OAuth
    oauth_config = await get_oauth_config()
    oauth_configured = list(oauth_config.keys())
    
    if oauth_configured:
        logger.info("OAuth 2.0 configurado", extra={
            "platforms": oauth_configured,
            "total_platforms": len(oauth_configured)
        })
    else:
        logger.warning("Nenhuma plataforma OAuth configurada")
    
    # Inicializar instâncias de serviços
    for service_name, config in SERVICES.items():
        for instance in config["instances"]:
            service_instances[service_name].append(instance["url"])
    
    # Iniciar auto-tuning em background se habilitado
    if settings.auto_tuning_enabled:
        task = asyncio.create_task(auto_tuning_engine.start_auto_tuning())
        graceful_shutdown.add_task(task)
        logger.info("Auto-Tuning Engine iniciado")
    else:
        logger.info("Auto-Tuning Engine desabilitado")

@app.on_event("shutdown")
async def shutdown_event():
    """Desligamento suave da aplicação"""
    logger.info("Iniciando desligamento da aplicação")
    
    # Parar auto-tuning
    auto_tuning_engine.running = False
    
    # Aguardar conclusão de tarefas
    await graceful_shutdown.wait_for_shutdown()
    
    logger.info("Aplicação desligada com sucesso")

@app.get("/")
async def root():
    """Endpoint raiz com informações do gateway"""
    oauth_config = await get_oauth_config()
    
    return {
        "service": "api-gateway-inteligente-unificado",
        "version": settings.app_version,
        "environment": settings.environment,
        "description": "Gateway principal do Ecossistema Co-Piloto com 7 serviços integrados + OAuth 2.0 (6 plataformas) - PRODUCTION READY",
        "ecosystem_services": len(SERVICES),
        "services": list(SERVICES.keys()),
        "features": [
            "intelligent_routing",
            "auto_tuning",
            "load_balancing", 
            "adaptive_caching",
            "circuit_breaker",
            "ecosystem_coordination",
            "oauth_2_0_authorization",
            "structured_logging",
            "secret_management",
            "graceful_shutdown"
        ],
        "oauth_platforms": list(oauth_config.keys()),
        "oauth_platforms_count": len(oauth_config),
        "cloud_native": True,
        "production_ready": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check simples e rápido para liveness/startup probes."""
    return {"status": "healthy", "service": "api-gateway-inteligente"}

@app.get("/status")
async def detailed_status():
    """Health check detalhado com informações completas do gateway."""
    global health_checks
    health_checks += 1

    oauth_config = await get_oauth_config()

    return {
        "status": "healthy",
        "service": "api-gateway-inteligente",
        "port": settings.port,
        "version": settings.app_version,
        "environment": settings.environment,
        "framework": "FastAPI",
        "uptime_seconds": time.time() - start_time,
        "total_requests": total_requests,
        "health_checks": health_checks,
        "gateway_requests": gateway_requests,
        "oauth_authorizations": oauth_authorizations,
        "cache_stats": {
            "hits": cache_hits,
            "misses": cache_misses,
            "hit_rate": cache_hits / max(cache_hits + cache_misses, 1),
            "size": len(cache_storage),
            "max_size": settings.cache_max_size
        },
        "circuit_breaker_trips": circuit_breaker_trips,
        "rl_decisions_used": rl_decisions_used,
        "auto_tuning": {
            "enabled": settings.auto_tuning_enabled,
            "running": auto_tuning_engine.running,
            "total_decisions": auto_tuning_decisions,
            "recent_optimizations": len([d for d in auto_tuning_history if (datetime.now() - d.timestamp).total_seconds() < 3600])
        },
        "ecosystem_integration": {
            "services_registered": len(SERVICES),
            "services_active": len([s for s in SERVICES if SERVICES[s]["instances"]]),
            "integration_status": "unified"
        },
        "oauth_status": {
            "platforms_configured": len(oauth_config),
            "total_platforms": 6,
            "active_tokens": 0,  # Será implementado na próxima fase
            "supported_platforms": list(oauth_config.keys())
        },
        "cloud_native": {
            "secret_manager_enabled": secret_manager.is_production and secret_manager.client is not None,
            "structured_logging": True,
            "graceful_shutdown": True,
            "environment_detection": settings.environment
        },
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# ROTAS OAUTH 2.0 - TODAS AS 6 PLATAFORMAS (REFATORADAS PARA FIRESTORE)
# ============================================================================

@app.get("/auth/google")
async def auth_google():
    """Iniciar autorização OAuth 2.0 com Google Ads + Analytics"""
    global oauth_authorizations
    
    oauth_config = await get_oauth_config()
    
    # Verificar se as credenciais estão configuradas
    if "google" not in oauth_config:
        raise HTTPException(
            status_code=500, 
            detail="Google OAuth não configurado. Configure as credenciais no Secret Manager ou variáveis de ambiente."
        )
    
    # Gerar estado único para segurança
    state = generate_oauth_state()
    
    # Salvar estado no Firestore
    if db:
        try:
            state_doc_ref = db.collection('oauth_pending_states').document(state)
            state_doc_ref.set({
                'platform': 'google',
                'expires_at': datetime.now() + timedelta(minutes=10),
                'timestamp': datetime.now()
            })
        except Exception as e:
            logger.error(f"Erro ao salvar estado OAuth no Firestore: {e}")
            raise HTTPException(status_code=500, detail="Erro interno ao processar autenticação")
    
    # Construir URL de autorização
    auth_url = await build_oauth_url("google", state)
    
    oauth_authorizations += 1
    logger.info("Iniciando autorização Google OAuth", extra={
        "platform": "google",
        "state": state,
        "services": ["Google Ads", "Google Analytics"]
    })
    
    return RedirectResponse(url=auth_url)

@app.get("/auth/google/callback")
async def auth_google_callback(code: str = None, state: str = None, error: str = None):
    """Callback da autorização OAuth 2.0 do Google"""
    
    # Verificar se houve erro
    if error:
        logger.error("Erro na autorização Google", extra={"error": error})
        raise HTTPException(status_code=400, detail=f"Autorização negada: {error}")
    
    # Verificar se código foi fornecido
    if not code:
        raise HTTPException(status_code=400, detail="Código de autorização não fornecido")
    
    # Verificar estado no Firestore
    if not state or not db:
        raise HTTPException(status_code=400, detail="Estado OAuth inválido ou Firestore indisponível")
    
    try:
        state_doc_ref = db.collection('oauth_pending_states').document(state)
        state_doc = state_doc_ref.get()
        
        if not state_doc.exists:
            raise HTTPException(status_code=400, detail="Estado OAuth inválido ou expirado")
        
        state_data = state_doc.to_dict()
        if state_data['platform'] != 'google':
            raise HTTPException(status_code=400, detail="Estado OAuth não corresponde à plataforma")
        
        if datetime.now(timezone.utc) > state_data['expires_at']:
            # Limpar estado expirado
            state_doc_ref.delete()
            raise HTTPException(status_code=400, detail="Estado OAuth expirado")
        
        # Trocar código por token
        token_data = await exchange_code_for_token("google", code, state)
        
        # Armazenar token
        token_id = store_oauth_token("google", token_data)
        
        # Limpar estado usado
        state_doc_ref.delete()
        
        logger.info("Autorização Google concluída com sucesso", extra={
            "platform": "google",
            "token_id": token_id,
            "scope": token_data.get("scope"),
            "expires_in": token_data.get("expires_in")
        })
        
        # Após armazenar o token com sucesso, redirecionar para a URL do frontend
        redirect_url = f"{settings.frontend_redirect_url}?token={token_id}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error("Erro no callback Google", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Erro ao processar autorização: {str(e)}")

@app.get("/auth/linkedin")
async def auth_linkedin():
    """Iniciar autorização OAuth 2.0 com LinkedIn Ads"""
    global oauth_authorizations
    
    oauth_config = await get_oauth_config()
    
    # Verificar se as credenciais estão configuradas
    if "linkedin" not in oauth_config:
        raise HTTPException(
            status_code=500, 
            detail="LinkedIn OAuth não configurado. Configure as credenciais no Secret Manager ou variáveis de ambiente."
        )
    
    # Gerar estado único para segurança
    state = generate_oauth_state()
    
    # Salvar estado no Firestore
    if db:
        try:
            state_doc_ref = db.collection('oauth_pending_states').document(state)
            state_doc_ref.set({
                'platform': 'linkedin',
                'expires_at': datetime.now() + timedelta(minutes=10),
                'timestamp': datetime.now()
            })
        except Exception as e:
            logger.error(f"Erro ao salvar estado OAuth no Firestore: {e}")
            raise HTTPException(status_code=500, detail="Erro interno ao processar autenticação")
    
    # Construir URL de autorização
    auth_url = await build_oauth_url("linkedin", state)
    
    oauth_authorizations += 1
    logger.info("Iniciando autorização LinkedIn OAuth", extra={
        "platform": "linkedin",
        "state": state
    })
    
    return RedirectResponse(url=auth_url)

@app.get("/auth/linkedin/callback")
async def auth_linkedin_callback(code: str = None, state: str = None, error: str = None, error_description: str = None):
    """Callback da autorização OAuth 2.0 do LinkedIn"""
    
    # Verificar se houve erro
    if error:
        error_msg = f"{error}: {error_description}" if error_description else error
        logger.error("Erro na autorização LinkedIn", extra={"error": error_msg})
        raise HTTPException(status_code=400, detail=f"Autorização negada: {error_msg}")
    
    # Verificar se código foi fornecido
    if not code:
        raise HTTPException(status_code=400, detail="Código de autorização não fornecido")
    
    # Verificar estado no Firestore
    if not state or not db:
        raise HTTPException(status_code=400, detail="Estado OAuth inválido ou Firestore indisponível")
    
    try:
        state_doc_ref = db.collection('oauth_pending_states').document(state)
        state_doc = state_doc_ref.get()
        
        if not state_doc.exists:
            raise HTTPException(status_code=400, detail="Estado OAuth inválido ou expirado")
        
        state_data = state_doc.to_dict()
        if state_data['platform'] != 'linkedin':
            raise HTTPException(status_code=400, detail="Estado OAuth não corresponde à plataforma")
        
        if datetime.now(timezone.utc) > state_data['expires_at']:
            # Limpar estado expirado
            state_doc_ref.delete()
            raise HTTPException(status_code=400, detail="Estado OAuth expirado")
        
        # Trocar código por token
        token_data = await exchange_code_for_token("linkedin", code, state)
        
        # Armazenar token
        token_id = store_oauth_token("linkedin", token_data)
        
        # Limpar estado usado
        state_doc_ref.delete()
        
        logger.info("Autorização LinkedIn concluída com sucesso", extra={
            "platform": "linkedin",
            "token_id": token_id
        })
        
        # Após armazenar o token com sucesso, redirecionar para a URL do frontend
        redirect_url = f"{settings.frontend_redirect_url}?token={token_id}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error("Erro no callback LinkedIn", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Erro ao processar autorização: {str(e)}")

@app.get("/auth/meta")
async def auth_meta():
    """Iniciar autorização OAuth 2.0 com Meta Ads (Facebook/Instagram)"""
    global oauth_authorizations
    
    oauth_config = await get_oauth_config()
    
    # Verificar se as credenciais estão configuradas
    if "meta" not in oauth_config:
        raise HTTPException(
            status_code=500, 
            detail="Meta OAuth não configurado. Configure as credenciais no Secret Manager ou variáveis de ambiente."
        )
    
    # Gerar estado único para segurança
    state = generate_oauth_state()
    
    # Salvar estado no Firestore
    if db:
        try:
            state_doc_ref = db.collection('oauth_pending_states').document(state)
            state_doc_ref.set({
                'platform': 'meta',
                'expires_at': datetime.now() + timedelta(minutes=10),
                'timestamp': datetime.now()
            })
        except Exception as e:
            logger.error(f"Erro ao salvar estado OAuth no Firestore: {e}")
            raise HTTPException(status_code=500, detail="Erro interno ao processar autenticação")
    
    # Construir URL de autorização
    auth_url = await build_oauth_url("meta", state)
    
    oauth_authorizations += 1
    logger.info("Iniciando autorização Meta OAuth", extra={
        "platform": "meta",
        "state": state
    })
    
    return RedirectResponse(url=auth_url)

@app.get("/auth/meta/callback")
async def auth_meta_callback(code: str = None, state: str = None, error: str = None, error_description: str = None):
    """Callback da autorização OAuth 2.0 do Meta"""
    
    # Verificar se houve erro
    if error:
        error_msg = f"{error}: {error_description}" if error_description else error
        logger.error("Erro na autorização Meta", extra={"error": error_msg})
        raise HTTPException(status_code=400, detail=f"Autorização negada: {error_msg}")
    
    # Verificar se código foi fornecido
    if not code:
        raise HTTPException(status_code=400, detail="Código de autorização não fornecido")
    
    # Verificar estado no Firestore
    if not state or not db:
        raise HTTPException(status_code=400, detail="Estado OAuth inválido ou Firestore indisponível")
    
    try:
        state_doc_ref = db.collection('oauth_pending_states').document(state)
        state_doc = state_doc_ref.get()
        
        if not state_doc.exists:
            raise HTTPException(status_code=400, detail="Estado OAuth inválido ou expirado")
        
        state_data = state_doc.to_dict()
        if state_data['platform'] != 'meta':
            raise HTTPException(status_code=400, detail="Estado OAuth não corresponde à plataforma")
        
        if datetime.now(timezone.utc) > state_data['expires_at']:
            # Limpar estado expirado
            state_doc_ref.delete()
            raise HTTPException(status_code=400, detail="Estado OAuth expirado")
        
        # Trocar código por token
        token_data = await exchange_code_for_token("meta", code, state)
        
        # Armazenar token
        token_id = store_oauth_token("meta", token_data)
        
        # Limpar estado usado
        state_doc_ref.delete()
        
        logger.info("Autorização Meta concluída com sucesso", extra={
            "platform": "meta",
            "token_id": token_id
        })
        
        # Após armazenar o token com sucesso, redirecionar para a URL do frontend
        redirect_url = f"{settings.frontend_redirect_url}?token={token_id}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error("Erro no callback Meta", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Erro ao processar autorização: {str(e)}")

@app.get("/auth/twitter")
async def auth_twitter():
    """Iniciar autorização OAuth 2.0 com Twitter Ads (X)"""
    global oauth_authorizations
    
    oauth_config = await get_oauth_config()
    
    # Verificar se as credenciais estão configuradas
    if "twitter" not in oauth_config:
        raise HTTPException(
            status_code=500, 
            detail="Twitter OAuth não configurado. Configure as credenciais no Secret Manager ou variáveis de ambiente."
        )
    
    # Gerar estado único para segurança
    state = generate_oauth_state()
    
    # Construir URL de autorização (inclui PKCE e salva code_verifier no Firestore)
    auth_url = await build_oauth_url("twitter", state)
    
    oauth_authorizations += 1
    logger.info("Iniciando autorização Twitter OAuth", extra={
        "platform": "twitter",
        "state": state
    })
    
    return RedirectResponse(url=auth_url)

@app.get("/auth/twitter/callback")
async def auth_twitter_callback(code: str = None, state: str = None, error: str = None, error_description: str = None):
    """Callback da autorização OAuth 2.0 do Twitter"""
    
    # Verificar se houve erro
    if error:
        error_msg = f"{error}: {error_description}" if error_description else error
        logger.error("Erro na autorização Twitter", extra={"error": error_msg})
        raise HTTPException(status_code=400, detail=f"Autorização negada: {error_msg}")
    
    # Verificar se código foi fornecido
    if not code:
        raise HTTPException(status_code=400, detail="Código de autorização não fornecido")
    
    # Verificar estado no Firestore
    if not state or not db:
        raise HTTPException(status_code=400, detail="Estado OAuth inválido ou Firestore indisponível")
    
    # Logging adicional para depuração do fluxo OAuth do Twitter
    logger.info("Twitter OAuth Debug", extra={
        "code": code[:10] + "..." if code else None,
        "state": state
    })

    try:
        # Tentar trocar o código pelo token (a validação do state é feita dentro da função)
        token_data = await exchange_code_for_token("twitter", code, state)

        # Se a troca de código pelo token funcionar, armazene o token e redirecione para o frontend
        token_id = store_oauth_token("twitter", token_data)
        
        redirect_url = f"{settings.frontend_redirect_url}?token={token_id}"
        return RedirectResponse(url=redirect_url)

    except HTTPException as e:
        # Se a nossa função exchange_code_for_token falhar, ela levanta uma HTTPException.
        return Response(
            content=f"Erro HTTP da nossa API: Status={e.status_code}, Detalhe=[{e.detail}]",
            status_code=500
        )
    except Exception as e:
        # Capturar qualquer outro erro inesperado
        return Response(
            content=f"Erro inesperado no Python: Tipo={type(e).__name__}, Mensagem=[{str(e)}]",
            status_code=500
        )

@app.get("/auth/tiktok")
async def auth_tiktok():
    """Iniciar autorização OAuth 2.0 com TikTok Ads"""
    global oauth_authorizations
    
    oauth_config = await get_oauth_config()
    
    # Verificar se as credenciais estão configuradas
    if "tiktok" not in oauth_config:
        raise HTTPException(
            status_code=500, 
            detail="TikTok OAuth não configurado. Configure as credenciais no Secret Manager ou variáveis de ambiente."
        )
    
    # Gerar estado único para segurança
    state = generate_oauth_state()
    
    # Salvar estado no Firestore
    if db:
        try:
            state_doc_ref = db.collection('oauth_pending_states').document(state)
            state_doc_ref.set({
                'platform': 'tiktok',
                'expires_at': datetime.now() + timedelta(minutes=10),
                'timestamp': datetime.now()
            })
        except Exception as e:
            logger.error(f"Erro ao salvar estado OAuth no Firestore: {e}")
            raise HTTPException(status_code=500, detail="Erro interno ao processar autenticação")
    
    # Construir URL de autorização
    auth_url = await build_oauth_url("tiktok", state)
    
    oauth_authorizations += 1
    logger.info("Iniciando autorização TikTok OAuth", extra={
        "platform": "tiktok",
        "state": state
    })
    
    return RedirectResponse(url=auth_url)

@app.get("/auth/tiktok/callback")
async def auth_tiktok_callback(code: str = None, state: str = None, error: str = None, error_description: str = None):
    """Callback da autorização OAuth 2.0 do TikTok"""
    
    # Verificar se houve erro
    if error:
        error_msg = f"{error}: {error_description}" if error_description else error
        logger.error("Erro na autorização TikTok", extra={"error": error_msg})
        raise HTTPException(status_code=400, detail=f"Autorização negada: {error_msg}")
    
    # Verificar se código foi fornecido
    if not code:
        raise HTTPException(status_code=400, detail="Código de autorização não fornecido")
    
    # Verificar estado no Firestore
    if not state or not db:
        raise HTTPException(status_code=400, detail="Estado OAuth inválido ou Firestore indisponível")
    
    try:
        state_doc_ref = db.collection('oauth_pending_states').document(state)
        state_doc = state_doc_ref.get()
        
        if not state_doc.exists:
            raise HTTPException(status_code=400, detail="Estado OAuth inválido ou expirado")
        
        state_data = state_doc.to_dict()
        if state_data['platform'] != 'tiktok':
            raise HTTPException(status_code=400, detail="Estado OAuth não corresponde à plataforma")
        
        if datetime.now(timezone.utc) > state_data['expires_at']:
            # Limpar estado expirado
            state_doc_ref.delete()
            raise HTTPException(status_code=400, detail="Estado OAuth expirado")
        
        # Trocar código por token
        token_data = await exchange_code_for_token("tiktok", code, state)
        
        # Armazenar token
        token_id = store_oauth_token("tiktok", token_data)
        
        # Limpar estado usado
        state_doc_ref.delete()
        
        logger.info("Autorização TikTok concluída com sucesso", extra={
            "platform": "tiktok",
            "token_id": token_id
        })
        
        # Após armazenar o token com sucesso, redirecionar para a URL do frontend
        redirect_url = f"{settings.frontend_redirect_url}?token={token_id}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error("Erro no callback TikTok", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Erro ao processar autorização: {str(e)}")

@app.get("/api/v1/oauth/tokens")
async def get_oauth_tokens():
    """Listar tokens OAuth armazenados (sem expor tokens completos)"""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore não disponível")
    
    # Para fins de demonstração, usamos um ID de usuário fixo
    DUMMY_USER_ID = "user_12345"
    
    try:
        tokens_info = []
        
        # Buscar tokens do usuário no Firestore
        tokens_ref = db.collection('user_tokens').document(DUMMY_USER_ID).collection('tokens')
        tokens_docs = tokens_ref.stream()
        
        for token_doc in tokens_docs:
            token_data = token_doc.to_dict()
            tokens_info.append({
                "platform": token_data.get("platform"),
                "token_type": token_data.get("token_type", "Bearer"),
                "scope": token_data.get("scope"),
                "expires_in": token_data.get("expires_in"),
                "has_refresh_token": token_data.get("refresh_token") is not None,
                "created_at": token_data.get("timestamp").isoformat() if token_data.get("timestamp") else None,
                "access_token_preview": token_data.get("access_token", "")[:10] + "..." if token_data.get("access_token") else None
            })
        
        return {
            "total_tokens": len(tokens_info),
            "platforms_with_tokens": list(set([t["platform"] for t in tokens_info if t["platform"]])),
            "tokens": tokens_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar tokens OAuth: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao listar tokens")

@app.delete("/api/v1/oauth/tokens/{platform}")
async def delete_oauth_token(platform: str):
    """Remover token OAuth específico por plataforma"""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore não disponível")
    
    # Para fins de demonstração, usamos um ID de usuário fixo
    DUMMY_USER_ID = "user_12345"
    
    try:
        # Verificar se o token existe
        token_doc_ref = db.collection('user_tokens').document(DUMMY_USER_ID).collection('tokens').document(platform)
        token_doc = token_doc_ref.get()
        
        if not token_doc.exists:
            raise HTTPException(status_code=404, detail="Token não encontrado")
        
        # Excluir o token
        token_doc_ref.delete()
        
        logger.info("Token OAuth removido", extra={
            "platform": platform,
            "user_id": DUMMY_USER_ID
        })
        
        return {
            "status": "success",
            "message": f"Token da plataforma {platform} removido com sucesso",
            "platform": platform,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao remover token OAuth: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao remover token")


# ============================================================================
# ROTAS ORIGINAIS DO GATEWAY (PRESERVADAS INTEGRALMENTE)
# ============================================================================

@app.post("/api/v1/route")
async def route_request(request: RouteRequest, background_tasks: BackgroundTasks):
    """Rotear requisição para serviço apropriado com IA"""
    global total_requests, gateway_requests, rl_decisions_used
    
    total_requests += 1
    gateway_requests += 1
    
    service = request.service
    path = request.path
    data = request.data
    method = request.method
    use_cache = request.use_cache
    force_rl_decision = request.force_rl_decision
    
    # Verificar se serviço existe
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found in ecosystem")
    
    # Verificar circuit breaker
    if not should_circuit_breaker_allow(service):
        raise HTTPException(status_code=503, detail=f"Service '{service}' circuit breaker is OPEN")
    
    # Verificar cache
    cache_key = get_cache_key(service, path, data)
    cache_ttl = SERVICES[service]["cache_ttl"]
    
    if use_cache and is_cache_valid(cache_key, cache_ttl):
        cached_response = get_from_cache(cache_key)
        if cached_response:
            # Registrar métricas de cache para auto-tuning
            auto_tuning_engine.cache_tuner.record_cache_metrics(service, True, 0.001)
            
            # Adicionar metadata de cache hit
            cached_response["_gateway_metadata"]["cache_hit"] = True
            cached_response["_gateway_metadata"]["cache_age_seconds"] = (datetime.now() - cache_metadata[cache_key]["timestamp"]).total_seconds()
            
            return cached_response
    
    # Registrar cache miss para auto-tuning
    auto_tuning_engine.cache_tuner.record_cache_metrics(service, False, 0)
    
    # Decisão do RL Engine (se forçada ou para contextos específicos)
    rl_decision = None
    if force_rl_decision or service in ["immune-system", "future-casting", "proactive-conversation"]:
        current_state = {
            "service": service,
            "path": path,
            "cache_hit_rate": cache_hits / max(cache_hits + cache_misses, 1),
            "circuit_breaker_state": get_circuit_breaker_state(service),
            "ecosystem_load": len([s for s in SERVICES if circuit_breaker_state[s]["state"] != "OPEN"]) / len(SERVICES)
        }
        
        rl_decision = await call_rl_engine("ecosystem_coordination", current_state)
        rl_decisions_used += 1
    
    # Selecionar instância do serviço
    service_url = select_service_instance(service)
    
    # Fazer requisição para o serviço
    try:
        start_time_req = time.time()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(f"{service_url}{path}", params=data)
            else:
                response = await client.request(method.upper(), f"{service_url}{path}", json=data)
        
        request_time = time.time() - start_time_req
        
        # Registrar sucesso
        record_success(service, request_time)
        service_health[service_url]["response_times"].append(request_time)
        service_health[service_url]["last_success"] = datetime.now()
        service_health[service_url]["request_count"] += 1
        
        # Calcular success rate
        total_requests_service = service_health[service_url]["request_count"]
        error_count = service_health[service_url]["error_count"]
        service_health[service_url]["success_rate"] = (total_requests_service - error_count) / max(total_requests_service, 1)
        
        # Registrar métricas para auto-tuning
        auto_tuning_engine.lb_tuner.record_load_balancer_metrics(service_url, request_time, True)
        
        # Log da requisição
        logger.info("Requisição roteada com sucesso", extra={
            "service_name": service,
            "service_url": service_url,
            "path": path,
            "method": method,
            "response_time": request_time * 1000,
            "status_code": response.status_code
        })
        
        # Processar resposta
        if response.status_code == 200:
            try:
                service_response = response.json()
            except:
                service_response = {"response": response.text, "status_code": response.status_code}
        else:
            service_response = {"error": f"Service returned status {response.status_code}", "status_code": response.status_code}
        
        # Preparar resposta com metadata expandida
        final_response = {
            **service_response,
            "_gateway_metadata": {
                "routed_by": "api-gateway-inteligente-unificado",
                "version": settings.app_version,
                "environment": settings.environment,
                "service": service,
                "instance_url": service_url,
                "path": path,
                "method": method,
                "status_code": response.status_code,
                "response_time_ms": round(request_time * 1000, 2),
                "rl_decision": rl_decision,
                "cache_hit": False,
                "circuit_breaker_state": get_circuit_breaker_state(service),
                "auto_tuning_active": auto_tuning_engine.running,
                "dynamic_weight": service_health[service_url]["weight"],
                "ecosystem_integration": "unified",
                "oauth_enabled": True,
                "oauth_platforms_supported": len(await get_oauth_config()),
                "cloud_native": True,
                "production_ready": True,
                "timestamp": datetime.now().isoformat(),
                "total_routed": gateway_requests
            }
        }
        
        # Armazenar no cache (se aplicável e sucesso)
        if use_cache and response.status_code == 200 and cache_ttl > 0:
            background_tasks.add_task(store_in_cache, cache_key, final_response, cache_ttl)
        
        return final_response
        
    except httpx.TimeoutException:
        record_failure(service)
        service_health[service_url]["error_count"] += 1
        auto_tuning_engine.lb_tuner.record_load_balancer_metrics(service_url, 30.0, False)
        logger.error("Timeout na requisição", extra={
            "service_name": service,
            "service_url": service_url,
            "path": path
        })
        raise HTTPException(status_code=504, detail=f"Timeout connecting to service '{service}'")
        
    except httpx.RequestError as e:
        record_failure(service)
        service_health[service_url]["error_count"] += 1
        auto_tuning_engine.lb_tuner.record_load_balancer_metrics(service_url, 30.0, False)
        logger.error("Erro de conexão", extra={
            "service_name": service,
            "service_url": service_url,
            "error": str(e)
        })
        raise HTTPException(status_code=502, detail=f"Error connecting to service '{service}': {str(e)}")
        
    except Exception as e:
        record_failure(service)
        service_health[service_url]["error_count"] += 1
        logger.error("Erro inesperado no roteamento", extra={
            "service_name": service,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Internal error routing to service '{service}'")

@app.get("/api/v1/services")
async def get_services():
    """Listar todos os serviços disponíveis no ecossistema"""
    services_info = []
    
    for service_name, config in SERVICES.items():
        # Inicializar circuit breaker se necessário
        initialize_circuit_breaker(service_name)
        
        # Calcular health score
        cb_state = get_circuit_breaker_state(service_name)
        health_score = 1.0 if cb_state == "CLOSED" else 0.5 if cb_state == "HALF_OPEN" else 0.0
        
        services_info.append({
            "name": service_name,
            "description": config["description"],
            "instances": len(config["instances"]),
            "endpoints": config["endpoints"],
            "cache_ttl": config["cache_ttl"],
            "circuit_breaker_enabled": config["circuit_breaker_enabled"],
            "circuit_breaker_state": cb_state,
            "health_score": health_score,
            "status": "healthy" if health_score > 0.5 else "degraded" if health_score > 0 else "failed"
        })
    
    return {
        "ecosystem": "co-piloto-unificado",
        "total_services": len(services_info),
        "services": services_info,
        "gateway_version": settings.app_version,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/ecosystem/health")
async def get_ecosystem_health():
    """Health check completo do ecossistema"""
    ecosystem_health = {
        "ecosystem_status": "healthy",
        "total_services": len(SERVICES),
        "healthy_services": 0,
        "degraded_services": 0,
        "failed_services": 0,
        "services_detail": {}
    }
    
    for service_name in SERVICES:
        initialize_circuit_breaker(service_name)
        cb_state = get_circuit_breaker_state(service_name)
        
        if cb_state == "CLOSED":
            status = "healthy"
            ecosystem_health["healthy_services"] += 1
        elif cb_state == "HALF_OPEN":
            status = "degraded"
            ecosystem_health["degraded_services"] += 1
        else:  # OPEN
            status = "failed"
            ecosystem_health["failed_services"] += 1
        
        ecosystem_health["services_detail"][service_name] = {
            "status": status,
            "circuit_breaker_state": cb_state
        }
    
    # Determinar status geral do ecossistema
    if ecosystem_health["failed_services"] > 0:
        ecosystem_health["ecosystem_status"] = "degraded"
    elif ecosystem_health["degraded_services"] > len(SERVICES) * 0.3:
        ecosystem_health["ecosystem_status"] = "degraded"
    
    return ecosystem_health

@app.get("/api/v1/auto-tuning/status")
async def get_auto_tuning_status():
    """Status detalhado do Auto-Tuning Engine"""
    return {
        "auto_tuning": {
            "enabled": settings.auto_tuning_enabled,
            "running": auto_tuning_engine.running,
            "optimization_interval": auto_tuning_engine.optimization_interval,
            "last_optimization": auto_tuning_engine.last_optimization.isoformat(),
            "total_decisions": auto_tuning_decisions,
            "recent_decisions": len([d for d in auto_tuning_history if (datetime.now() - d.timestamp).total_seconds() < 3600])
        },
        "components": {
            "cache_tuner": {
                "services_monitored": len(auto_tuning_engine.cache_tuner.cache_hit_rates),
                "last_optimizations": {k: v.isoformat() for k, v in auto_tuning_engine.cache_tuner.last_optimization.items()}
            },
            "circuit_breaker_tuner": {
                "services_monitored": len(auto_tuning_engine.cb_tuner.failure_patterns)
            },
            "load_balancer_tuner": {
                "instances_monitored": len(auto_tuning_engine.lb_tuner.response_time_patterns)
            }
        },
        "recent_optimizations": [
            {
                "component": d.component,
                "parameter": d.parameter,
                "old_value": d.old_value,
                "new_value": d.new_value,
                "reason": d.reason,
                "confidence": d.confidence,
                "timestamp": d.timestamp.isoformat()
            }
            for d in list(auto_tuning_history)[-10:]  # Últimas 10 decisões
        ]
    }

@app.get("/api/v1/cache/stats")
async def get_cache_stats():
    """Estatísticas detalhadas do cache"""
    return {
        "cache_stats": {
            "total_entries": len(cache_storage),
            "max_size": settings.cache_max_size,
            "hits": cache_hits,
            "misses": cache_misses,
            "hit_rate": cache_hits / max(cache_hits + cache_misses, 1),
            "memory_usage_mb": sum(len(str(v)) for v in cache_storage.values()) / 1024 / 1024
        },
        "service_cache_config": {
            service: {"ttl": config["cache_ttl"]}
            for service, config in SERVICES.items()
        }
    }

@app.get("/api/v1/circuit-breaker/status")
async def get_circuit_breaker_status():
    """Status dos circuit breakers"""
    return {
        "circuit_breakers": {
            service: {
                "state": cb_state["state"],
                "failure_count": cb_state["failure_count"],
                "threshold": cb_state["threshold"],
                "success_count": cb_state["success_count"],
                "last_failure": cb_state["last_failure"].isoformat() if cb_state["last_failure"] else None,
                "next_attempt": cb_state["next_attempt"].isoformat() if cb_state["next_attempt"] else None
            }
            for service, cb_state in circuit_breaker_state.items()
        },
        "total_trips": circuit_breaker_trips
    }

# ============================================================================
# ENDPOINTS DE METAS DE NEGÓCIO (CPA & ROAS)
# ============================================================================

class BusinessGoals(BaseModel):
    """
    Model representing the business goals for a user. The attribute names
    follow the conventions expected by the frontend. Aliases are provided
    to ensure compatibility when serializing and deserializing the model.

    Attributes:
        maxCPA (Optional[float]): Custo Máximo por Novo Cliente (CPA) desejado.
        minROAS (Optional[float]): Retorno Mínimo Sobre Investimento (ROAS) desejado.
    """

    # Usando alias para garantir que os nomes no JSON correspondam aos esperados pelo frontend.
    maxCPA: Optional[float] = Field(
        None,
        alias="maxCPA",
        description="Custo Máximo por Novo Cliente (CPA) desejado."
    )
    minROAS: Optional[float] = Field(
        None,
        alias="minROAS",
        description="Retorno Mínimo Sobre Investimento (ROAS) desejado."
    )

# Para fins de teste, usaremos um ID de usuário fixo.
# Em produção, isso viria de um contexto de autenticação.
DUMMY_USER_ID = "user_12345"

@app.post("/api/v1/settings/goals")
async def set_business_goals(goals: BusinessGoals):
    """Salva ou atualiza as metas de negócio para um usuário."""
    if not db:
        raise HTTPException(status_code=500, detail="Conexão com o banco de dados não disponível.")
    
    try:
        user_settings_ref = db.collection('user_settings').document(DUMMY_USER_ID)
        # Usamos 'set' com 'merge=True' para criar ou atualizar o documento parcialmente.
        # Usamos by_alias=True para garantir que os nomes de campo enviados para o banco de dados
        # correspondam aos esperados pelo frontend (maxCPA, minROAS).
        user_settings_ref.set(goals.dict(by_alias=True, exclude_unset=True), merge=True)
        
        logger.info(f"Metas de negócio atualizadas para o usuário {DUMMY_USER_ID}", extra=goals.dict())
        return {"status": "success", "message": "Metas de negócio salvas com sucesso."}
    except Exception as e:
        logger.error(f"Erro ao salvar metas de negócio: {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar as metas de negócio.")

@app.get("/api/v1/settings/goals", response_model=BusinessGoals)
async def get_business_goals():
    """Recupera as metas de negócio de um usuário."""
    if not db:
        raise HTTPException(status_code=500, detail="Conexão com o banco de dados não disponível.")
        
    try:
        user_settings_ref = db.collection('user_settings').document(DUMMY_USER_ID)
        doc = user_settings_ref.get()
        if doc.exists:
            # Constrói um objeto BusinessGoals a partir do dicionário retornado pelo banco.
            # Isso garante que as chaves sejam convertidas corretamente para os campos do modelo.
            return BusinessGoals(**doc.to_dict())
        # Se não houver metas salvas, retorna um objeto BusinessGoals com campos nulos
        return BusinessGoals(maxCPA=None, minROAS=None)
    except Exception as e:
        logger.error(f"Erro ao recuperar metas de negócio: {e}")
        raise HTTPException(status_code=500, detail="Erro ao recuperar as metas de negócio.")

@app.get("/api/v1/credentials/status")
async def get_credentials_status():
    """Verifica e retorna o status de conexão de todas as plataformas OAuth."""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore não disponível")
    
    # Para fins de demonstração, usamos um ID de usuário fixo
    DUMMY_USER_ID = "user_12345"
    
    platforms = ["google", "meta", "linkedin", "twitter"]
    status_report: Dict[str, Dict[str, str]] = {}

    try:
        # Verificar tokens no Firestore
        tokens_ref = db.collection('user_tokens').document(DUMMY_USER_ID).collection('tokens')
        tokens_docs = tokens_ref.stream()
        
        # Criar conjunto de plataformas com tokens
        platforms_with_tokens = set()
        for token_doc in tokens_docs:
            token_data = token_doc.to_dict()
            platform = token_data.get("platform")
            if platform:
                platforms_with_tokens.add(platform)

        # Gerar relatório de status
        for platform in platforms:
            if platform in platforms_with_tokens:
                status_report[platform] = {"status": "connected"}
            else:
                status_report[platform] = {"status": "disconnected"}

        logger.info("Relatório de status de credenciais gerado", extra={"report": status_report})
        return status_report
        
    except Exception as e:
        logger.error(f"Erro ao verificar status de credenciais: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao verificar credenciais")

# ============================================================================
# MAIN - PRODUCTION READY
# ============================================================================

def main():
    """Função principal para inicialização da aplicação"""
    try:
        # Cloud Run fornece a porta através da variável de ambiente PORT
        port = int(os.environ.get("PORT", 8080))
        host = "0.0.0.0"
        
        logger.info("Iniciando API Gateway v4.1.2 - Production Ready", extra={
            "host": host,
            "port": port,
            "environment": settings.environment,
            "google_cloud_project": settings.google_cloud_project,
            "cloud_run_detected": bool(os.getenv('K_SERVICE'))
        })
        
        # Configuração específica para Cloud Run
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_config=None,  # Usar nosso logging estruturado
            access_log=False,  # Evitar logs duplicados
            server_header=False,
            date_header=False
        )
        
        server = uvicorn.Server(config)
        
        logger.info("Servidor configurado - iniciando...", extra={
            "config": {
                "host": config.host,
                "port": config.port,
                "app": str(config.app)
            }
        })
        
        # Iniciar servidor
        server.run()
        
    except Exception as e:
        logger.error("Falha crítica na inicialização", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        sys.exit(1)

if __name__ == "__main__":
    main()
else:
    # Para Cloud Run, a aplicação é importada como módulo
    logger.info("API Gateway carregado como módulo", extra={
        "environment": settings.environment,
        "port": settings.port,
        "cloud_run": bool(os.getenv('K_SERVICE'))
    })

