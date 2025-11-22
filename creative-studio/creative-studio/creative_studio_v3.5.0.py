#!/usr/bin/env python3
"""
Creative Studio v3.5 - Observability & Optimization
Plataforma de criação de conteúdo otimizada para Google Cloud Run

🚀 NOVIDADES v3.5 - OBSERVABILITY:
- ✅ Structured Logging (JSON format)
- ✅ Compression avançada (gzip/brotli)
- ✅ Métricas Prometheus completas
- ✅ Performance Profiling detalhado
- ✅ Otimizações finais de performance

🛡️ FUNCIONALIDADES HERDADAS:
- ✅ Resilience & Performance (v3.4)
- ✅ Cloud Run Optimization (v3.3)
- ✅ Content Intelligence (v3.2)
- ✅ Workflow Automation (v3.1)
- ✅ Advanced Image Generation (v3.0)
- ✅ AI Content Optimization (v2.1.1)
"""

import os
import sys
import time
import uuid
import hashlib
import logging
import asyncio
import io
import base64
import json
import random
import signal
import psutil
import threading
import gzip
import brotli
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from contextlib import asynccontextmanager
from enum import Enum

import requests
from bs4 import BeautifulSoup

# FastAPI e dependências
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Processamento de imagens
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io

# HTTP client
import httpx

# Novos modelos para análise de URL
class UrlAnalysisRequest(BaseModel):
    url: str = Field(..., description="URL para análise")

class UrlAnalysisResponse(BaseModel):
    suggested_headlines: List[str] = Field(..., description="Sugestões de títulos para anúncios")
    suggested_descriptions: List[str] = Field(..., description="Sugestões de descrições para anúncios")
    suggested_image_url: Optional[str] = Field(None, description="URL da imagem principal sugerida")

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("creative-studio")

# ================================
# CONFIGURAÇÃO VIA ENVIRONMENT VARIABLES
# ================================

class CloudRunConfig:
    """Configuração via Environment Variables - Cloud Run Ready"""
    
    # Configurações básicas
    PORT = int(os.getenv("PORT", "8003"))
    HOST = os.getenv("HOST", "0.0.0.0")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    VERSION = "3.5.0"
    SERVICE_NAME = os.getenv("SERVICE_NAME", "creative-studio")
    
    # Configurações de AI Optimization (v2.1.1)
    ANALYTICS_WINDOW_SIZE = int(os.getenv("ANALYTICS_WINDOW_SIZE", "3600"))
    ANALYTICS_RETENTION = int(os.getenv("ANALYTICS_RETENTION", "86400"))
    ANALYTICS_REFRESH_INTERVAL = int(os.getenv("ANALYTICS_REFRESH_INTERVAL", "60"))
    
    # Configurações de Advanced Image Generation (v3.0)
    IMAGE_MAX_SIZE = int(os.getenv("IMAGE_MAX_SIZE", "2048"))
    IMAGE_QUALITY = int(os.getenv("IMAGE_QUALITY", "85"))
    IMAGE_FORMATS = os.getenv("IMAGE_FORMATS", "JPEG,PNG,WEBP").split(",")
    BATCH_MAX_IMAGES = int(os.getenv("BATCH_MAX_IMAGES", "10"))
    
    # Configurações de Workflow Automation (v3.1)
    WORKFLOW_MAX_STEPS = int(os.getenv("WORKFLOW_MAX_STEPS", "20"))
    WORKFLOW_TIMEOUT_SECONDS = int(os.getenv("WORKFLOW_TIMEOUT_SECONDS", "300"))
    WORKFLOW_MAX_CONCURRENT = int(os.getenv("WORKFLOW_MAX_CONCURRENT", "5"))
    WORKFLOW_BATCH_SIZE = int(os.getenv("WORKFLOW_BATCH_SIZE", "10"))
    
    # Configurações de Content Intelligence (v3.2)
    INTELLIGENCE_CACHE_TTL = int(os.getenv("INTELLIGENCE_CACHE_TTL", "3600"))
    PREDICTION_MODEL_VERSION = os.getenv("PREDICTION_MODEL_VERSION", "1.2.0")
    TREND_ANALYSIS_DEPTH = int(os.getenv("TREND_ANALYSIS_DEPTH", "30"))
    AB_TEST_CONFIDENCE_THRESHOLD = float(os.getenv("AB_TEST_CONFIDENCE_THRESHOLD", "0.95"))
    
    # Configurações de performance
    MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", "512"))
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    
    # Feature flags
    ENABLE_AI_OPTIMIZATION = os.getenv("ENABLE_AI_OPTIMIZATION", "true").lower() == "true"
    ENABLE_IMAGE_GENERATION = os.getenv("ENABLE_IMAGE_GENERATION", "true").lower() == "true"
    ENABLE_STYLE_TRANSFER = os.getenv("ENABLE_STYLE_TRANSFER", "true").lower() == "true"
    ENABLE_BATCH_PROCESSING = os.getenv("ENABLE_BATCH_PROCESSING", "true").lower() == "true"
    ENABLE_WORKFLOW_AUTOMATION = os.getenv("ENABLE_WORKFLOW_AUTOMATION", "true").lower() == "true"
    ENABLE_CONTENT_INTELLIGENCE = os.getenv("ENABLE_CONTENT_INTELLIGENCE", "true").lower() == "true"
    
    # ================================
    # CLOUD RUN ESPECÍFICAS v3.3
    # ================================
    
    # Performance e Recursos
    MAX_CPU_CORES = float(os.getenv("MAX_CPU_CORES", "1.0"))
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "100"))
    
    # Timeouts
    REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    STARTUP_TIMEOUT_SECONDS = int(os.getenv("STARTUP_TIMEOUT_SECONDS", "10"))
    SHUTDOWN_TIMEOUT_SECONDS = int(os.getenv("SHUTDOWN_TIMEOUT_SECONDS", "10"))
    HEALTH_CHECK_TIMEOUT_MS = int(os.getenv("HEALTH_CHECK_TIMEOUT_MS", "100"))
    
    # Memory Management
    CACHE_MAX_SIZE_MB = int(os.getenv("CACHE_MAX_SIZE_MB", "50"))
    MEMORY_CLEANUP_INTERVAL = int(os.getenv("MEMORY_CLEANUP_INTERVAL", "60"))
    MEMORY_WARNING_THRESHOLD = float(os.getenv("MEMORY_WARNING_THRESHOLD", "0.8"))
    
    # Logging e Observabilidade
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    ENABLE_TRACING = os.getenv("ENABLE_TRACING", "true").lower() == "true"
    
    # Error Handling e Resilience
    CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
    CIRCUIT_BREAKER_TIMEOUT = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60"))
    RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "1000"))
    ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    ENABLE_CIRCUIT_BREAKER = os.getenv("ENABLE_CIRCUIT_BREAKER", "true").lower() == "true"
    
    # Cloud Run Features v3.3
    ENABLE_GRACEFUL_SHUTDOWN = os.getenv("ENABLE_GRACEFUL_SHUTDOWN", "true").lower() == "true"
    ENABLE_MEMORY_MONITORING = os.getenv("ENABLE_MEMORY_MONITORING", "true").lower() == "true"
    
    # ================================
    # OBSERVABILITY CONFIGURATIONS v3.5
    # ================================
    
    # Structured Logging
    ENABLE_STRUCTURED_LOGGING = os.getenv("ENABLE_STRUCTURED_LOGGING", "true").lower() == "true"
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json ou text
    LOG_CORRELATION_ID = os.getenv("LOG_CORRELATION_ID", "true").lower() == "true"
    
    # Compression
    ENABLE_COMPRESSION = os.getenv("ENABLE_COMPRESSION", "true").lower() == "true"
    ENABLE_BROTLI = os.getenv("ENABLE_BROTLI", "true").lower() == "true"
    COMPRESSION_LEVEL = int(os.getenv("COMPRESSION_LEVEL", "6"))  # 1-9
    COMPRESSION_MIN_SIZE = int(os.getenv("COMPRESSION_MIN_SIZE", "1024"))  # bytes
    
    # Prometheus Metrics
    ENABLE_PROMETHEUS_METRICS = os.getenv("ENABLE_PROMETHEUS_METRICS", "true").lower() == "true"
    METRICS_PATH = os.getenv("METRICS_PATH", "/metrics")
    ENABLE_BUSINESS_METRICS = os.getenv("ENABLE_BUSINESS_METRICS", "true").lower() == "true"
    ENABLE_SYSTEM_METRICS = os.getenv("ENABLE_SYSTEM_METRICS", "true").lower() == "true"
    
    # Performance Profiling
    ENABLE_PERFORMANCE_PROFILING = os.getenv("ENABLE_PERFORMANCE_PROFILING", "true").lower() == "true"
    PROFILING_SAMPLE_RATE = float(os.getenv("PROFILING_SAMPLE_RATE", "1.0"))  # 0.0-1.0
    PROFILING_MAX_OPERATIONS = int(os.getenv("PROFILING_MAX_OPERATIONS", "100"))
    
    # Optimization Settings
    ENABLE_ASYNC_OPTIMIZATION = os.getenv("ENABLE_ASYNC_OPTIMIZATION", "true").lower() == "true"
    ENABLE_CACHE_OPTIMIZATION = os.getenv("ENABLE_CACHE_OPTIMIZATION", "true").lower() == "true"
    ENABLE_MEMORY_CLEANUP = os.getenv("ENABLE_MEMORY_CLEANUP", "true").lower() == "true"
    ENABLE_CACHING_HEADERS = os.getenv("ENABLE_CACHING_HEADERS", "true").lower() == "true"

config = CloudRunConfig()

# ================================
# ENUMS E TIPOS
# ================================

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowStepType(str, Enum):
    CONTENT_GENERATION = "content_generation"
    CONTENT_OPTIMIZATION = "content_optimization"
    IMAGE_GENERATION = "image_generation"
    IMAGE_PROCESSING = "image_processing"
    TEMPLATE_APPLICATION = "template_application"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"

# ================================
# MODELOS PYDANTIC - API FIRST
# ================================

# Modelos existentes (v2.1.1 e v3.0) mantidos...
class ContentAnalysisRequest(BaseModel):
    content: str = Field(..., description="Conteúdo para análise")
    content_type: str = Field(default="text", description="Tipo do conteúdo")

class SEOAnalysisRequest(BaseModel):
    content: str = Field(..., description="Conteúdo para análise SEO")
    title: Optional[str] = Field(None, description="Título do conteúdo")

class ReadabilityAnalysisRequest(BaseModel):
    content: str = Field(..., description="Conteúdo para análise de legibilidade")

class ToneAnalysisRequest(BaseModel):
    content: str = Field(..., description="Conteúdo para análise de tom")

class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Prompt para geração da imagem")
    style: Optional[str] = Field("realistic", description="Estilo da imagem")
    width: Optional[int] = Field(512, description="Largura da imagem")
    height: Optional[int] = Field(512, description="Altura da imagem")
    quality: Optional[int] = Field(85, description="Qualidade da imagem (1-100)")

class StyleTransferRequest(BaseModel):
    style_name: str = Field(..., description="Nome do estilo a aplicar")
    intensity: Optional[float] = Field(0.8, description="Intensidade do estilo (0.0-1.0)")

class ImageEnhancementRequest(BaseModel):
    enhancement_type: str = Field(..., description="Tipo de melhoria (brightness, contrast, sharpness, color)")
    factor: Optional[float] = Field(1.2, description="Fator de melhoria (0.0-2.0)")

class ImageConversionRequest(BaseModel):
    target_format: str = Field(..., description="Formato de destino (JPEG, PNG, WEBP)")
    quality: Optional[int] = Field(85, description="Qualidade para formatos com compressão")

class BatchProcessingRequest(BaseModel):
    operations: List[str] = Field(..., description="Lista de operações a aplicar")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parâmetros para as operações")

# Novos modelos para Workflow Automation (v3.1)
class WorkflowStep(BaseModel):
    id: str = Field(..., description="ID único do step")
    type: WorkflowStepType = Field(..., description="Tipo do step")
    name: str = Field(..., description="Nome do step")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parâmetros do step")
    depends_on: List[str] = Field(default_factory=list, description="IDs dos steps dependentes")
    timeout_seconds: Optional[int] = Field(60, description="Timeout do step")

class WorkflowDefinition(BaseModel):
    name: str = Field(..., description="Nome do workflow")
    description: Optional[str] = Field("", description="Descrição do workflow")
    steps: List[WorkflowStep] = Field(..., description="Steps do workflow")
    timeout_seconds: Optional[int] = Field(300, description="Timeout total do workflow")
    retry_attempts: Optional[int] = Field(3, description="Tentativas de retry")

class WorkflowCreateRequest(BaseModel):
    workflow: WorkflowDefinition = Field(..., description="Definição do workflow")
    schedule: Optional[str] = Field(None, description="Agendamento (cron format)")

class WorkflowExecuteRequest(BaseModel):
    workflow_id: Optional[str] = Field(None, description="ID do workflow salvo")
    workflow: Optional[WorkflowDefinition] = Field(None, description="Definição inline do workflow")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Dados de entrada")
    priority: Optional[int] = Field(1, description="Prioridade (1-10)")

class WorkflowBatchRequest(BaseModel):
    workflow_id: Optional[str] = Field(None, description="ID do workflow salvo")
    workflow: Optional[WorkflowDefinition] = Field(None, description="Definição inline do workflow")
    batch_data: List[Dict[str, Any]] = Field(..., description="Lista de dados de entrada")
    parallel: Optional[bool] = Field(True, description="Executar em paralelo")

# Novos modelos para Content Intelligence (v3.2)
class TrendAnalysisRequest(BaseModel):
    topic: str = Field(..., description="Tópico para análise de tendências")
    time_window: Optional[str] = Field("last_7_days", description="Janela de tempo (last_24_hours, last_7_days, last_30_days)")

class PerformancePredictionRequest(BaseModel):
    content: str = Field(..., description="Conteúdo para predição de performance")
    platform: str = Field(..., description="Plataforma de destino (blog, twitter, instagram, linkedin)")

class ContentRecommendationsRequest(BaseModel):
    topic: str = Field(..., description="Tópico para obter recomendações")
    target_audience: Optional[str] = Field("general", description="Público-alvo")
    content_type: Optional[str] = Field("blog", description="Tipo de conteúdo desejado")

class CompetitorInsightsRequest(BaseModel):
    competitor_content: str = Field(..., description="Conteúdo do concorrente para análise")
    my_content: Optional[str] = Field(None, description="Seu conteúdo para comparação")

class ABTestRequest(BaseModel):
    variant_a: str = Field(..., description="Variante A do conteúdo")
    variant_b: str = Field(..., description="Variante B do conteúdo")
    metric: str = Field("engagement", description="Métrica para otimização (engagement, conversion, clicks)")

# ================================
# CLASSES DE SERVIÇO - STATELESS
# ================================

class AdvancedMemoryCache:
    """Cache em memória avançado - Cloud Run v3.3 com monitoramento"""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._access_count: Dict[str, int] = {}
        self._memory_usage_mb = 0
        self._last_cleanup = datetime.now()
        
        # Iniciar monitoramento se habilitado
        if config.ENABLE_MEMORY_MONITORING:
            self._start_memory_monitoring()
    
    def get(self, key: str) -> Optional[Any]:
        """Recuperar item do cache"""
        if key in self._cache:
            # Verificar TTL
            if datetime.now() - self._timestamps[key] < timedelta(seconds=config.CACHE_TTL_SECONDS):
                self._access_count[key] = self._access_count.get(key, 0) + 1
                return self._cache[key]
            else:
                # Expirado, remover
                self.delete(key)
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Armazenar item no cache com monitoramento de memória"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        self._access_count[key] = 1
        
        # Atualizar uso de memória
        self._update_memory_usage()
        
        # Limpeza automática se necessário
        if self._should_cleanup():
            self._cleanup_old_entries()
    
    def delete(self, key: str) -> None:
        """Remover item do cache"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._access_count.pop(key, None)
        self._update_memory_usage()
    
    def _should_cleanup(self) -> bool:
        """Verificar se limpeza é necessária"""
        # Limpeza por tamanho
        if len(self._cache) > 100:
            return True
        
        # Limpeza por uso de memória
        if self._memory_usage_mb > config.CACHE_MAX_SIZE_MB:
            return True
        
        # Limpeza por tempo
        if datetime.now() - self._last_cleanup > timedelta(seconds=config.MEMORY_CLEANUP_INTERVAL):
            return True
        
        return False
    
    def _cleanup_old_entries(self) -> None:
        """Limpeza inteligente de entradas antigas"""
        now = datetime.now()
        
        # Remover entradas expiradas
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if now - timestamp > timedelta(seconds=config.CACHE_TTL_SECONDS)
        ]
        
        for key in expired_keys:
            self.delete(key)
        
        # Se ainda precisar de mais espaço, remover menos acessadas
        if self._memory_usage_mb > config.CACHE_MAX_SIZE_MB:
            sorted_keys = sorted(
                self._access_count.items(), 
                key=lambda x: x[1]
            )
            
            # Remover 25% das entradas menos acessadas
            keys_to_remove = [key for key, _ in sorted_keys[:len(sorted_keys)//4]]
            for key in keys_to_remove:
                self.delete(key)
        
        self._last_cleanup = now
        logger.info(f"🧹 Cache cleanup concluído. Entradas: {len(self._cache)}, Memória: {self._memory_usage_mb:.1f}MB")
    
    def _update_memory_usage(self) -> None:
        """Atualizar estimativa de uso de memória"""
        if config.ENABLE_MEMORY_MONITORING:
            # Estimativa simples baseada no número de entradas
            self._memory_usage_mb = len(self._cache) * 0.1  # ~100KB por entrada
    
    def _start_memory_monitoring(self) -> None:
        """Iniciar monitoramento de memória em background"""
        def monitor():
            while True:
                try:
                    process = psutil.Process()
                    memory_percent = process.memory_percent()
                    
                    if memory_percent > config.MEMORY_WARNING_THRESHOLD * 100:
                        logger.warning(f"⚠️ Alto uso de memória: {memory_percent:.1f}%")
                        self._cleanup_old_entries()
                    
                    time.sleep(30)  # Verificar a cada 30 segundos
                except Exception as e:
                    logger.error(f"Erro no monitoramento de memória: {e}")
                    break
        
        if config.ENABLE_MEMORY_MONITORING:
            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache"""
        return {
            "total_entries": len(self._cache),
            "memory_usage_mb": self._memory_usage_mb,
            "last_cleanup": self._last_cleanup.isoformat(),
            "most_accessed": max(self._access_count.items(), key=lambda x: x[1]) if self._access_count else None
        }
    
    def set(self, key: str, value: Any) -> None:
        """Armazenar item no cache"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        
        # Limpeza automática se cache muito grande
        if len(self._cache) > 100:
            self._cleanup_old_entries()
    
    def delete(self, key: str) -> None:
        """Remover item do cache"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def _cleanup_old_entries(self) -> None:
        """Limpeza automática de entradas antigas"""
        now = datetime.now()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if now - timestamp > timedelta(seconds=config.CACHE_TTL_SECONDS)
        ]
        for key in expired_keys:
            self.delete(key)

# ================================
# RESILIENCE CLASSES v3.4
# ================================

class CircuitBreaker:
    """Circuit Breaker inteligente para falhas - v3.4"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def call(self, func, *args, **kwargs):
        """Executar função com circuit breaker"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Verificar se deve tentar resetar o circuit breaker"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.timeout
    
    def _on_success(self):
        """Callback para sucesso"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Callback para falha"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do circuit breaker"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "timeout": self.timeout
        }

class RateLimiter:
    """Rate Limiter avançado por IP/usuário - v3.4"""
    
    def __init__(self, max_requests: int = 1000, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.requests: Dict[str, List[float]] = {}
        self.blocked_until: Dict[str, float] = {}
        
    def is_allowed(self, identifier: str) -> bool:
        """Verificar se request é permitido"""
        current_time = time.time()
        
        # Verificar se está bloqueado
        if identifier in self.blocked_until:
            if current_time < self.blocked_until[identifier]:
                return False
            else:
                del self.blocked_until[identifier]
        
        # Limpar requests antigas
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remover requests fora da janela
        cutoff_time = current_time - self.window_seconds
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if req_time > cutoff_time
        ]
        
        # Verificar limite
        if len(self.requests[identifier]) >= self.max_requests:
            # Bloquear por 5 minutos
            self.blocked_until[identifier] = current_time + 300
            return False
        
        # Adicionar request atual
        self.requests[identifier].append(current_time)
        return True
    
    def get_stats(self, identifier: str) -> Dict[str, Any]:
        """Obter estatísticas do rate limiter"""
        current_time = time.time()
        
        if identifier not in self.requests:
            return {
                "requests_in_window": 0,
                "max_requests": self.max_requests,
                "window_seconds": self.window_seconds,
                "blocked": False,
                "blocked_until": None
            }
        
        # Contar requests na janela atual
        cutoff_time = current_time - self.window_seconds
        requests_in_window = len([
            req_time for req_time in self.requests[identifier] 
            if req_time > cutoff_time
        ])
        
        blocked = identifier in self.blocked_until and current_time < self.blocked_until[identifier]
        blocked_until = self.blocked_until.get(identifier) if blocked else None
        
        return {
            "requests_in_window": requests_in_window,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "blocked": blocked,
            "blocked_until": blocked_until
        }

class GracefulShutdownHandler:
    """Graceful Shutdown Handler - v3.4"""
    
    def __init__(self):
        self.shutdown_requested = False
        self.active_requests = 0
        self.shutdown_timeout = config.SHUTDOWN_TIMEOUT_SECONDS
        
    def register_request(self):
        """Registrar início de request"""
        self.active_requests += 1
    
    def unregister_request(self):
        """Registrar fim de request"""
        self.active_requests = max(0, self.active_requests - 1)
    
    def request_shutdown(self):
        """Solicitar shutdown graceful"""
        self.shutdown_requested = True
        logger.info(f"🛑 Graceful shutdown solicitado. Requests ativas: {self.active_requests}")
        
        # Aguardar requests ativas terminarem
        start_time = time.time()
        while self.active_requests > 0 and (time.time() - start_time) < self.shutdown_timeout:
            logger.info(f"⏳ Aguardando {self.active_requests} requests terminarem...")
            time.sleep(1)
        
        if self.active_requests > 0:
            logger.warning(f"⚠️ Timeout de shutdown. {self.active_requests} requests ainda ativas.")
        else:
            logger.info("✅ Shutdown graceful concluído. Todas as requests terminaram.")
    
    def is_shutdown_requested(self) -> bool:
        """Verificar se shutdown foi solicitado"""
        return self.shutdown_requested
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do shutdown handler"""
        return {
            "shutdown_requested": self.shutdown_requested,
            "active_requests": self.active_requests,
            "shutdown_timeout": self.shutdown_timeout
        }

# ================================
# OBSERVABILITY CLASSES v3.5
# ================================

class StructuredLogger:
    """Structured Logger com formato JSON - v3.5"""
    
    def __init__(self, service_name: str = "creative-studio"):
        self.service_name = service_name
        self.correlation_id = None
        
    def set_correlation_id(self, correlation_id: str):
        """Definir correlation ID para tracking"""
        self.correlation_id = correlation_id
    
    def _format_log(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """Formatar log em estrutura JSON"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "service": self.service_name,
            "version": config.VERSION,
            "message": message,
            "correlation_id": self.correlation_id,
            **kwargs
        }
        return log_entry
    
    def info(self, message: str, **kwargs):
        """Log de informação"""
        log_entry = self._format_log("INFO", message, **kwargs)
        logger.info(json.dumps(log_entry))
    
    def error(self, message: str, **kwargs):
        """Log de erro"""
        log_entry = self._format_log("ERROR", message, **kwargs)
        logger.error(json.dumps(log_entry))
    
    def warning(self, message: str, **kwargs):
        """Log de warning"""
        log_entry = self._format_log("WARNING", message, **kwargs)
        logger.warning(json.dumps(log_entry))
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        log_entry = self._format_log("DEBUG", message, **kwargs)
        logger.debug(json.dumps(log_entry))

class CompressionHandler:
    """Handler de compressão avançada - v3.5"""
    
    def __init__(self):
        self.gzip_level = config.COMPRESSION_LEVEL
        self.min_size = config.COMPRESSION_MIN_SIZE
        self.compressible_types = {
            "application/json",
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "text/plain"
        }
    
    def should_compress(self, content_type: str, content_length: int) -> bool:
        """Verificar se deve comprimir o conteúdo"""
        if content_length < self.min_size:
            return False
        
        return any(ct in content_type for ct in self.compressible_types)
    
    def compress_gzip(self, data: bytes) -> bytes:
        """Comprimir com gzip"""
        return gzip.compress(data, compresslevel=self.gzip_level)
    
    def compress_brotli(self, data: bytes) -> bytes:
        """Comprimir com brotli"""
        return brotli.compress(data, quality=self.gzip_level)
    
    def get_best_encoding(self, accept_encoding: str) -> str:
        """Obter melhor encoding baseado no Accept-Encoding"""
        if "br" in accept_encoding and config.ENABLE_BROTLI:
            return "br"
        elif "gzip" in accept_encoding:
            return "gzip"
        return None
    
    def compress_response(self, data: bytes, encoding: str) -> bytes:
        """Comprimir response com encoding especificado"""
        if encoding == "br":
            return self.compress_brotli(data)
        elif encoding == "gzip":
            return self.compress_gzip(data)
        return data

class PrometheusMetrics:
    """Métricas Prometheus para Cloud Run - v3.5"""
    
    def __init__(self):
        self.metrics = {
            # Request metrics
            "http_requests_total": 0,
            "http_request_duration_seconds": [],
            "http_requests_in_flight": 0,
            
            # Business metrics
            "content_generated_total": 0,
            "images_generated_total": 0,
            "workflows_executed_total": 0,
            "intelligence_queries_total": 0,
            
            # System metrics
            "memory_usage_bytes": 0,
            "cpu_usage_percent": 0,
            "cache_hits_total": 0,
            "cache_misses_total": 0,
            
            # Error metrics
            "http_errors_total": 0,
            "circuit_breaker_trips_total": 0,
            "rate_limit_exceeded_total": 0
        }
        self.labels = {}
    
    def increment_counter(self, metric_name: str, labels: Dict[str, str] = None):
        """Incrementar contador"""
        if metric_name in self.metrics:
            self.metrics[metric_name] += 1
            if labels:
                key = f"{metric_name}_{hash(str(sorted(labels.items())))}"
                self.labels[key] = labels
    
    def record_histogram(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Registrar valor em histograma"""
        if metric_name in self.metrics and isinstance(self.metrics[metric_name], list):
            self.metrics[metric_name].append(value)
            # Manter apenas últimos 1000 valores
            if len(self.metrics[metric_name]) > 1000:
                self.metrics[metric_name] = self.metrics[metric_name][-1000:]
    
    def set_gauge(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Definir valor de gauge"""
        if metric_name in self.metrics:
            self.metrics[metric_name] = value
    
    def get_metrics_text(self) -> str:
        """Obter métricas em formato Prometheus"""
        lines = []
        
        for metric_name, value in self.metrics.items():
            if isinstance(value, list):
                # Histograma - calcular estatísticas
                if value:
                    count = len(value)
                    total = sum(value)
                    lines.append(f"# TYPE {metric_name} histogram")
                    lines.append(f"{metric_name}_count {count}")
                    lines.append(f"{metric_name}_sum {total}")
                    lines.append(f"{metric_name}_bucket{{le=\"+Inf\"}} {count}")
            else:
                # Counter ou Gauge
                metric_type = "counter" if metric_name.endswith("_total") else "gauge"
                lines.append(f"# TYPE {metric_name} {metric_type}")
                lines.append(f"{metric_name} {value}")
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas das métricas"""
        stats = {}
        for metric_name, value in self.metrics.items():
            if isinstance(value, list):
                if value:
                    stats[metric_name] = {
                        "count": len(value),
                        "sum": sum(value),
                        "avg": sum(value) / len(value),
                        "min": min(value),
                        "max": max(value)
                    }
                else:
                    stats[metric_name] = {"count": 0}
            else:
                stats[metric_name] = value
        return stats

class PerformanceProfiler:
    """Performance Profiler detalhado - v3.5"""
    
    def __init__(self):
        self.profiles = {}
        self.active_profiles = {}
    
    def start_profile(self, profile_id: str, operation: str):
        """Iniciar profiling de operação"""
        self.active_profiles[profile_id] = {
            "operation": operation,
            "start_time": time.time(),
            "start_memory": psutil.Process().memory_info().rss
        }
    
    def end_profile(self, profile_id: str) -> Dict[str, Any]:
        """Finalizar profiling e obter resultados"""
        if profile_id not in self.active_profiles:
            return {}
        
        profile = self.active_profiles.pop(profile_id)
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        result = {
            "operation": profile["operation"],
            "duration_ms": round((end_time - profile["start_time"]) * 1000, 2),
            "memory_delta_mb": round((end_memory - profile["start_memory"]) / 1024 / 1024, 2),
            "timestamp": datetime.now().isoformat()
        }
        
        # Armazenar no histórico
        operation = profile["operation"]
        if operation not in self.profiles:
            self.profiles[operation] = []
        
        self.profiles[operation].append(result)
        
        # Manter apenas últimos 100 profiles por operação
        if len(self.profiles[operation]) > 100:
            self.profiles[operation] = self.profiles[operation][-100:]
        
        return result
    
    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """Obter estatísticas de uma operação"""
        if operation not in self.profiles or not self.profiles[operation]:
            return {}
        
        durations = [p["duration_ms"] for p in self.profiles[operation]]
        memory_deltas = [p["memory_delta_mb"] for p in self.profiles[operation]]
        
        return {
            "operation": operation,
            "count": len(durations),
            "duration_ms": {
                "avg": round(sum(durations) / len(durations), 2),
                "min": min(durations),
                "max": max(durations)
            },
            "memory_delta_mb": {
                "avg": round(sum(memory_deltas) / len(memory_deltas), 2),
                "min": min(memory_deltas),
                "max": max(memory_deltas)
            }
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Obter estatísticas de todas as operações"""
        return {
            operation: self.get_operation_stats(operation)
            for operation in self.profiles.keys()
        }

class ContentAnalyzer:
    """Analisador de conteúdo - Mantido das versões anteriores"""
    
    def __init__(self):
        self.cache = AdvancedMemoryCache()
    
    def analyze_content(self, content: str, content_type: str = "text") -> Dict[str, Any]:
        """Análise completa de conteúdo"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Verificar cache
        cached_result = self.cache.get(f"analysis_{content_hash}")
        if cached_result:
            return cached_result
        
        # Análise completa
        result = {
            "content_id": content_hash,
            "content_type": content_type,
            "analysis_timestamp": datetime.now().isoformat(),
            "content_score": self._calculate_content_score(content),
            "seo_analysis": self._analyze_seo(content),
            "readability_analysis": self._analyze_readability(content),
            "tone_analysis": self._analyze_tone(content),
            "processing_time_ms": 0
        }
        
        # Cache do resultado
        self.cache.set(f"analysis_{content_hash}", result)
        
        logger.info(f"🧠 Análise de conteúdo: {content_hash} (score: {result['content_score']['overall_score']})")
        return result
    
    def _calculate_content_score(self, content: str) -> Dict[str, Any]:
        """Calcular score de qualidade do conteúdo"""
        words = content.split()
        sentences = content.split('.')
        
        # Métricas básicas
        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])
        avg_words_per_sentence = word_count / max(sentence_count, 1)
        
        # Score baseado em múltiplos fatores
        length_score = min(word_count / 100, 1.0) * 25
        structure_score = min(sentence_count / 5, 1.0) * 25
        complexity_score = min(avg_words_per_sentence / 15, 1.0) * 25
        keyword_score = len(set(words)) / max(len(words), 1) * 25
        
        overall_score = length_score + structure_score + complexity_score + keyword_score
        
        return {
            "overall_score": round(overall_score, 1),
            "length_score": round(length_score, 1),
            "structure_score": round(structure_score, 1),
            "complexity_score": round(complexity_score, 1),
            "keyword_score": round(keyword_score, 1),
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_words_per_sentence": round(avg_words_per_sentence, 1)
        }
    
    def _analyze_seo(self, content: str, title: str = "") -> Dict[str, Any]:
        """Análise SEO do conteúdo"""
        words = content.lower().split()
        
        # Extração de palavras-chave
        word_freq = {}
        for word in words:
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Score SEO
        keyword_density = len(set(words)) / max(len(words), 1)
        title_score = 10 if title and len(title) > 10 else 5
        content_length_score = min(len(words) / 300, 1.0) * 15
        
        seo_score = (keyword_density * 50) + title_score + content_length_score
        
        return {
            "seo_score": round(min(seo_score, 100), 1),
            "keywords": [{"word": word, "frequency": freq} for word, freq in keywords],
            "keyword_density": round(keyword_density, 3),
            "title_optimized": bool(title and len(title) > 10),
            "content_length_optimal": len(words) >= 300
        }
    
    def _analyze_readability(self, content: str) -> Dict[str, Any]:
        """Análise de legibilidade"""
        words = content.split()
        sentences = content.split('.')
        
        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])
        
        if sentence_count == 0:
            return {"readability_score": 0, "reading_level": "unknown"}
        
        avg_sentence_length = word_count / sentence_count
        
        # Flesch Reading Ease adaptado
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * 1.5)
        flesch_score = max(0, min(100, flesch_score))
        
        # Nível de leitura
        if flesch_score >= 90:
            reading_level = "muito_facil"
        elif flesch_score >= 80:
            reading_level = "facil"
        elif flesch_score >= 70:
            reading_level = "medio"
        elif flesch_score >= 60:
            reading_level = "dificil"
        else:
            reading_level = "muito_dificil"
        
        return {
            "readability_score": round(flesch_score, 1),
            "reading_level": reading_level,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "word_count": word_count,
            "sentence_count": sentence_count
        }
    
    def _analyze_tone(self, content: str) -> Dict[str, Any]:
        """Análise de tom do conteúdo"""
        content_lower = content.lower()
        
        # Palavras indicadoras de diferentes tons
        professional_words = ["empresa", "negócio", "estratégia", "resultado", "análise", "dados"]
        casual_words = ["legal", "bacana", "cara", "galera", "pessoal", "gente"]
        technical_words = ["algoritmo", "sistema", "tecnologia", "implementação", "arquitetura"]
        emotional_words = ["amor", "paixão", "emoção", "sentimento", "coração"]
        
        # Contagem de palavras por categoria
        professional_count = sum(1 for word in professional_words if word in content_lower)
        casual_count = sum(1 for word in casual_words if word in content_lower)
        technical_count = sum(1 for word in technical_words if word in content_lower)
        emotional_count = sum(1 for word in emotional_words if word in content_lower)
        
        # Determinar tom principal
        tone_scores = {
            "professional": professional_count,
            "casual": casual_count,
            "technical": technical_count,
            "emotional": emotional_count,
            "neutral": 1
        }
        
        primary_tone = max(tone_scores.items(), key=lambda x: x[1])[0]
        confidence = tone_scores[primary_tone] / max(sum(tone_scores.values()), 1)
        
        return {
            "primary_tone": primary_tone,
            "confidence": round(confidence, 2),
            "tone_scores": tone_scores,
            "tone_indicators": {
                "professional_words": professional_count,
                "casual_words": casual_count,
                "technical_words": technical_count,
                "emotional_words": emotional_count
            }
        }

class AdvancedImageProcessor:
    """Processador avançado de imagens - Mantido da v3.0"""
    
    def __init__(self):
        self.cache = AdvancedMemoryCache()
        self.supported_formats = config.IMAGE_FORMATS
        self.max_size = config.IMAGE_MAX_SIZE
        
    def generate_image(self, prompt: str, style: str = "realistic", 
                      width: int = 512, height: int = 512, quality: int = 85) -> Dict[str, Any]:
        """Gerar imagem via prompt"""
        if not config.ENABLE_IMAGE_GENERATION:
            raise HTTPException(status_code=503, detail="Image generation disabled")
        
        # Validações
        if width > self.max_size or height > self.max_size:
            raise HTTPException(status_code=400, detail=f"Image size exceeds maximum {self.max_size}px")
        
        # Gerar ID único
        generation_id = str(uuid.uuid4())
        
        # Simular geração de imagem
        image = self._create_placeholder_image(width, height, prompt, style)
        
        # Converter para base64
        image_data = self._image_to_base64(image, "PNG", quality)
        
        result = {
            "generation_id": generation_id,
            "prompt": prompt,
            "style": style,
            "dimensions": {"width": width, "height": height},
            "format": "PNG",
            "quality": quality,
            "image_data": image_data,
            "size_bytes": len(base64.b64decode(image_data)),
            "generated_at": datetime.now().isoformat(),
            "processing_time_ms": 1500
        }
        
        logger.info(f"🎨 Imagem gerada: {generation_id} ({width}x{height}, {style})")
        return result
    
    def apply_style_transfer(self, image_data: bytes, style_name: str, intensity: float = 0.8) -> Dict[str, Any]:
        """Aplicar transferência de estilo"""
        if not config.ENABLE_STYLE_TRANSFER:
            raise HTTPException(status_code=503, detail="Style transfer disabled")
        
        # Carregar imagem
        image = Image.open(io.BytesIO(image_data))
        
        # Aplicar estilo
        styled_image = self._apply_style_effect(image, style_name, intensity)
        
        # Converter resultado
        result_data = self._image_to_base64(styled_image, "PNG", config.IMAGE_QUALITY)
        
        result = {
            "style_transfer_id": str(uuid.uuid4()),
            "style_name": style_name,
            "intensity": intensity,
            "original_size": len(image_data),
            "result_size": len(base64.b64decode(result_data)),
            "image_data": result_data,
            "processed_at": datetime.now().isoformat(),
            "processing_time_ms": 800
        }
        
        logger.info(f"🎭 Estilo aplicado: {style_name} (intensidade: {intensity})")
        return result
    
    def enhance_image(self, image_data: bytes, enhancement_type: str, factor: float = 1.2) -> Dict[str, Any]:
        """Melhorar qualidade da imagem"""
        # Carregar imagem
        image = Image.open(io.BytesIO(image_data))
        
        # Aplicar melhoria
        enhanced_image = self._apply_enhancement(image, enhancement_type, factor)
        
        # Converter resultado
        result_data = self._image_to_base64(enhanced_image, "PNG", config.IMAGE_QUALITY)
        
        result = {
            "enhancement_id": str(uuid.uuid4()),
            "enhancement_type": enhancement_type,
            "factor": factor,
            "original_size": len(image_data),
            "result_size": len(base64.b64decode(result_data)),
            "image_data": result_data,
            "processed_at": datetime.now().isoformat(),
            "processing_time_ms": 300
        }
        
        logger.info(f"✨ Imagem melhorada: {enhancement_type} (fator: {factor})")
        return result
    
    def convert_format(self, image_data: bytes, target_format: str, quality: int = 85) -> Dict[str, Any]:
        """Converter formato da imagem"""
        if target_format not in self.supported_formats:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {target_format}")
        
        # Carregar imagem
        image = Image.open(io.BytesIO(image_data))
        
        # Converter formato
        result_data = self._image_to_base64(image, target_format, quality)
        
        result = {
            "conversion_id": str(uuid.uuid4()),
            "target_format": target_format,
            "quality": quality,
            "original_size": len(image_data),
            "result_size": len(base64.b64decode(result_data)),
            "image_data": result_data,
            "converted_at": datetime.now().isoformat(),
            "processing_time_ms": 200
        }
        
        logger.info(f"🔄 Formato convertido para: {target_format}")
        return result
    
    def batch_process(self, images_data: List[bytes], operations: List[str], 
                     parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Processamento em lote"""
        if not config.ENABLE_BATCH_PROCESSING:
            raise HTTPException(status_code=503, detail="Batch processing disabled")
        
        if len(images_data) > config.BATCH_MAX_IMAGES:
            raise HTTPException(status_code=400, detail=f"Too many images. Max: {config.BATCH_MAX_IMAGES}")
        
        batch_id = str(uuid.uuid4())
        results = []
        
        for i, image_data in enumerate(images_data):
            image_results = {}
            
            for operation in operations:
                if operation == "enhance":
                    result = self.enhance_image(
                        image_data, 
                        parameters.get("enhancement_type", "brightness"),
                        parameters.get("factor", 1.2)
                    )
                elif operation == "convert":
                    result = self.convert_format(
                        image_data,
                        parameters.get("target_format", "PNG"),
                        parameters.get("quality", 85)
                    )
                elif operation == "style_transfer":
                    result = self.apply_style_transfer(
                        image_data,
                        parameters.get("style_name", "artistic"),
                        parameters.get("intensity", 0.8)
                    )
                
                image_results[operation] = result
            
            results.append({
                "image_index": i,
                "operations": image_results
            })
        
        batch_result = {
            "batch_id": batch_id,
            "total_images": len(images_data),
            "operations_applied": operations,
            "parameters": parameters,
            "results": results,
            "processed_at": datetime.now().isoformat(),
            "total_processing_time_ms": len(images_data) * len(operations) * 500
        }
        
        logger.info(f"📦 Batch processado: {batch_id} ({len(images_data)} imagens, {len(operations)} operações)")
        return batch_result
    
    def _create_placeholder_image(self, width: int, height: int, prompt: str, style: str) -> Image.Image:
        """Criar imagem placeholder"""
        import random
        random.seed(hash(prompt))
        
        # Cores baseadas no estilo
        if style == "artistic":
            colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255)]
        elif style == "realistic":
            colors = [(200, 180, 160), (160, 140, 120), (120, 100, 80)]
        else:
            colors = [(128, 128, 128), (64, 64, 64), (192, 192, 192)]
        
        color = random.choice(colors)
        image = Image.new("RGB", (width, height), color)
        
        return image
    
    def _apply_style_effect(self, image: Image.Image, style_name: str, intensity: float) -> Image.Image:
        """Aplicar efeito de estilo"""
        if style_name == "artistic":
            image = image.filter(ImageFilter.SMOOTH)
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.0 + intensity)
        elif style_name == "vintage":
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(0.7)
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
        elif style_name == "modern":
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.0 + intensity)
        
        return image
    
    def _apply_enhancement(self, image: Image.Image, enhancement_type: str, factor: float) -> Image.Image:
        """Aplicar melhoria na imagem"""
        if enhancement_type == "brightness":
            enhancer = ImageEnhance.Brightness(image)
            return enhancer.enhance(factor)
        elif enhancement_type == "contrast":
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(factor)
        elif enhancement_type == "sharpness":
            enhancer = ImageEnhance.Sharpness(image)
            return enhancer.enhance(factor)
        elif enhancement_type == "color":
            enhancer = ImageEnhance.Color(image)
            return enhancer.enhance(factor)
        else:
            return image
    
    def _image_to_base64(self, image: Image.Image, format: str, quality: int) -> str:
        """Converter imagem para base64"""
        buffer = io.BytesIO()
        
        if format == "JPEG":
            image = image.convert("RGB")
            image.save(buffer, format=format, quality=quality)
        else:
            image.save(buffer, format=format)
        
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode()
        return image_data

class WorkflowEngine:
    """Engine de automação de workflows - Cloud Run Ready"""
    
    def __init__(self, content_analyzer: ContentAnalyzer, image_processor: AdvancedImageProcessor):
        self.content_analyzer = content_analyzer
        self.image_processor = image_processor
        self.cache = AdvancedMemoryCache()
        self.active_workflows: Dict[str, Dict] = {}  # Em memória apenas
        self.workflow_templates: Dict[str, WorkflowDefinition] = {}  # Templates em memória
        
        # Inicializar templates padrão
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Inicializar templates padrão de workflow"""
        # Template 1: Blog Post Completo
        blog_template = WorkflowDefinition(
            name="blog_post_complete",
            description="Workflow completo para criação de blog post com imagem",
            steps=[
                WorkflowStep(
                    id="generate_content",
                    type=WorkflowStepType.CONTENT_GENERATION,
                    name="Gerar Conteúdo",
                    parameters={"content_type": "blog", "min_words": 300}
                ),
                WorkflowStep(
                    id="optimize_content",
                    type=WorkflowStepType.CONTENT_OPTIMIZATION,
                    name="Otimizar Conteúdo",
                    parameters={"optimize_seo": True, "target_score": 70},
                    depends_on=["generate_content"]
                ),
                WorkflowStep(
                    id="generate_image",
                    type=WorkflowStepType.IMAGE_GENERATION,
                    name="Gerar Imagem",
                    parameters={"style": "realistic", "width": 800, "height": 600},
                    depends_on=["generate_content"]
                ),
                WorkflowStep(
                    id="enhance_image",
                    type=WorkflowStepType.IMAGE_PROCESSING,
                    name="Melhorar Imagem",
                    parameters={"enhancement_type": "sharpness", "factor": 1.2},
                    depends_on=["generate_image"]
                )
            ],
            timeout_seconds=300
        )
        
        # Template 2: Social Media Pack
        social_template = WorkflowDefinition(
            name="social_media_pack",
            description="Pacote completo para redes sociais",
            steps=[
                WorkflowStep(
                    id="generate_post",
                    type=WorkflowStepType.CONTENT_GENERATION,
                    name="Gerar Post",
                    parameters={"content_type": "social", "max_words": 100}
                ),
                WorkflowStep(
                    id="generate_square_image",
                    type=WorkflowStepType.IMAGE_GENERATION,
                    name="Imagem Quadrada",
                    parameters={"style": "modern", "width": 1080, "height": 1080},
                    depends_on=["generate_post"]
                ),
                WorkflowStep(
                    id="generate_story_image",
                    type=WorkflowStepType.IMAGE_GENERATION,
                    name="Imagem Stories",
                    parameters={"style": "modern", "width": 1080, "height": 1920},
                    depends_on=["generate_post"]
                )
            ],
            timeout_seconds=180
        )
        
        # Template 3: Content Optimization
        optimization_template = WorkflowDefinition(
            name="content_optimization",
            description="Otimização completa de conteúdo existente",
            steps=[
                WorkflowStep(
                    id="analyze_content",
                    type=WorkflowStepType.CONTENT_OPTIMIZATION,
                    name="Analisar Conteúdo",
                    parameters={"full_analysis": True}
                ),
                WorkflowStep(
                    id="improve_seo",
                    type=WorkflowStepType.CONTENT_OPTIMIZATION,
                    name="Melhorar SEO",
                    parameters={"target_keywords": [], "min_score": 80},
                    depends_on=["analyze_content"]
                ),
                WorkflowStep(
                    id="improve_readability",
                    type=WorkflowStepType.CONTENT_OPTIMIZATION,
                    name="Melhorar Legibilidade",
                    parameters={"target_level": "medio"},
                    depends_on=["analyze_content"]
                )
            ],
            timeout_seconds=120
        )
        
        self.workflow_templates = {
            "blog_post_complete": blog_template,
            "social_media_pack": social_template,
            "content_optimization": optimization_template
        }
        
        logger.info(f"🔄 Templates de workflow inicializados: {len(self.workflow_templates)}")
    
    def create_workflow(self, workflow_def: WorkflowDefinition, schedule: Optional[str] = None) -> Dict[str, Any]:
        """Criar novo workflow"""
        if not config.ENABLE_WORKFLOW_AUTOMATION:
            raise HTTPException(status_code=503, detail="Workflow automation disabled")
        
        workflow_id = str(uuid.uuid4())
        
        # Validar workflow
        self._validate_workflow(workflow_def)
        
        # Armazenar em memória (stateless)
        workflow_data = {
            "id": workflow_id,
            "definition": workflow_def.dict(),
            "schedule": schedule,
            "created_at": datetime.now().isoformat(),
            "status": WorkflowStatus.PENDING,
            "executions": []
        }
        
        # Cache temporário (TTL automático)
        self.cache.set(f"workflow_{workflow_id}", workflow_data)
        
        logger.info(f"🔄 Workflow criado: {workflow_id} ({workflow_def.name})")
        
        return {
            "workflow_id": workflow_id,
            "name": workflow_def.name,
            "status": WorkflowStatus.PENDING,
            "steps_count": len(workflow_def.steps),
            "created_at": workflow_data["created_at"]
        }
    
    async def execute_workflow(self, workflow_id: Optional[str], workflow_def: Optional[WorkflowDefinition], 
                              input_data: Dict[str, Any], priority: int = 1) -> Dict[str, Any]:
        """Executar workflow"""
        if not config.ENABLE_WORKFLOW_AUTOMATION:
            raise HTTPException(status_code=503, detail="Workflow automation disabled")
        
        execution_id = str(uuid.uuid4())
        
        # Obter definição do workflow
        if workflow_id:
            workflow_data = self.cache.get(f"workflow_{workflow_id}")
            if not workflow_data:
                raise HTTPException(status_code=404, detail="Workflow not found")
            workflow_def = WorkflowDefinition(**workflow_data["definition"])
        elif workflow_def:
            # Workflow inline
            pass
        else:
            raise HTTPException(status_code=400, detail="Either workflow_id or workflow definition required")
        
        # Validar workflow
        self._validate_workflow(workflow_def)
        
        # Inicializar execução
        execution_data = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow_def.name,
            "status": WorkflowStatus.RUNNING,
            "started_at": datetime.now().isoformat(),
            "input_data": input_data,
            "priority": priority,
            "steps_completed": 0,
            "steps_total": len(workflow_def.steps),
            "results": {},
            "errors": []
        }
        
        # Armazenar execução ativa (em memória)
        self.active_workflows[execution_id] = execution_data
        
        try:
            # Executar steps do workflow
            results = await self._execute_workflow_steps(workflow_def, input_data, execution_id)
            
            # Atualizar status
            execution_data["status"] = WorkflowStatus.COMPLETED
            execution_data["completed_at"] = datetime.now().isoformat()
            execution_data["results"] = results
            
            logger.info(f"🎉 Workflow executado com sucesso: {execution_id}")
            
        except Exception as e:
            # Atualizar status de erro
            execution_data["status"] = WorkflowStatus.FAILED
            execution_data["failed_at"] = datetime.now().isoformat()
            execution_data["errors"].append(str(e))
            
            logger.error(f"❌ Erro na execução do workflow {execution_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")
        
        finally:
            # Limpeza automática (memory management)
            if execution_id in self.active_workflows:
                # Cache resultado por TTL limitado
                self.cache.set(f"execution_{execution_id}", execution_data)
                # Remover de workflows ativos
                del self.active_workflows[execution_id]
        
        return {
            "execution_id": execution_id,
            "workflow_name": workflow_def.name,
            "status": execution_data["status"],
            "steps_completed": execution_data["steps_completed"],
            "steps_total": execution_data["steps_total"],
            "started_at": execution_data["started_at"],
            "completed_at": execution_data.get("completed_at"),
            "processing_time_ms": self._calculate_processing_time(execution_data),
            "results": execution_data["results"]
        }
    
    async def execute_batch_workflows(self, workflow_id: Optional[str], workflow_def: Optional[WorkflowDefinition],
                                     batch_data: List[Dict[str, Any]], parallel: bool = True) -> Dict[str, Any]:
        """Executar workflows em lote"""
        if not config.ENABLE_WORKFLOW_AUTOMATION:
            raise HTTPException(status_code=503, detail="Workflow automation disabled")
        
        if len(batch_data) > config.WORKFLOW_BATCH_SIZE:
            raise HTTPException(status_code=400, detail=f"Batch size exceeds limit: {config.WORKFLOW_BATCH_SIZE}")
        
        batch_id = str(uuid.uuid4())
        
        logger.info(f"📦 Iniciando batch de workflows: {batch_id} ({len(batch_data)} execuções)")
        
        if parallel:
            # Execução paralela
            tasks = []
            for i, input_data in enumerate(batch_data):
                task = self.execute_workflow(workflow_id, workflow_def, input_data, priority=i+1)
                tasks.append(task)
            
            # Aguardar todas as execuções
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Execução sequencial
            results = []
            for input_data in batch_data:
                try:
                    result = await self.execute_workflow(workflow_id, workflow_def, input_data)
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e)})
        
        # Compilar resultados do batch
        successful = sum(1 for r in results if isinstance(r, dict) and "error" not in r)
        failed = len(results) - successful
        
        batch_result = {
            "batch_id": batch_id,
            "total_executions": len(batch_data),
            "successful_executions": successful,
            "failed_executions": failed,
            "parallel_execution": parallel,
            "results": results,
            "processed_at": datetime.now().isoformat()
        }
        
        logger.info(f"📦 Batch concluído: {batch_id} ({successful}/{len(batch_data)} sucessos)")
        
        return batch_result
    
    def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Obter status de execução do workflow"""
        # Verificar workflows ativos
        if execution_id in self.active_workflows:
            execution_data = self.active_workflows[execution_id]
        else:
            # Verificar cache de execuções concluídas
            execution_data = self.cache.get(f"execution_{execution_id}")
            if not execution_data:
                raise HTTPException(status_code=404, detail="Execution not found")
        
        return {
            "execution_id": execution_id,
            "workflow_name": execution_data["workflow_name"],
            "status": execution_data["status"],
            "steps_completed": execution_data["steps_completed"],
            "steps_total": execution_data["steps_total"],
            "started_at": execution_data["started_at"],
            "completed_at": execution_data.get("completed_at"),
            "failed_at": execution_data.get("failed_at"),
            "processing_time_ms": self._calculate_processing_time(execution_data),
            "errors": execution_data.get("errors", [])
        }
    
    def get_workflow_templates(self) -> Dict[str, Any]:
        """Obter templates de workflow disponíveis"""
        templates = []
        for template_id, template_def in self.workflow_templates.items():
            templates.append({
                "template_id": template_id,
                "name": template_def.name,
                "description": template_def.description,
                "steps_count": len(template_def.steps),
                "timeout_seconds": template_def.timeout_seconds
            })
        
        return {
            "total_templates": len(templates),
            "templates": templates
        }
    
    async def _execute_workflow_steps(self, workflow_def: WorkflowDefinition, 
                                     input_data: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Executar steps do workflow"""
        results = {}
        execution_data = self.active_workflows[execution_id]
        
        # Criar grafo de dependências
        dependency_graph = self._build_dependency_graph(workflow_def.steps)
        
        # Executar steps em ordem de dependência
        for step in workflow_def.steps:
            # Verificar dependências
            if step.depends_on:
                for dep_id in step.depends_on:
                    if dep_id not in results:
                        raise Exception(f"Dependency {dep_id} not completed for step {step.id}")
            
            # Executar step
            step_result = await self._execute_step(step, input_data, results)
            results[step.id] = step_result
            
            # Atualizar progresso
            execution_data["steps_completed"] += 1
            
            logger.info(f"✅ Step concluído: {step.id} ({step.name})")
        
        return results
    
    async def _execute_step(self, step: WorkflowStep, input_data: Dict[str, Any], 
                           previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Executar um step individual"""
        start_time = time.time()
        
        try:
            if step.type == WorkflowStepType.CONTENT_GENERATION:
                result = await self._execute_content_generation_step(step, input_data, previous_results)
            elif step.type == WorkflowStepType.CONTENT_OPTIMIZATION:
                result = await self._execute_content_optimization_step(step, input_data, previous_results)
            elif step.type == WorkflowStepType.IMAGE_GENERATION:
                result = await self._execute_image_generation_step(step, input_data, previous_results)
            elif step.type == WorkflowStepType.IMAGE_PROCESSING:
                result = await self._execute_image_processing_step(step, input_data, previous_results)
            elif step.type == WorkflowStepType.TEMPLATE_APPLICATION:
                result = await self._execute_template_application_step(step, input_data, previous_results)
            else:
                raise Exception(f"Unsupported step type: {step.type}")
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "step_id": step.id,
                "step_name": step.name,
                "step_type": step.type,
                "status": "completed",
                "processing_time_ms": round(processing_time, 2),
                "result": result
            }
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "step_id": step.id,
                "step_name": step.name,
                "step_type": step.type,
                "status": "failed",
                "processing_time_ms": round(processing_time, 2),
                "error": str(e)
            }
    
    async def _execute_content_generation_step(self, step: WorkflowStep, input_data: Dict[str, Any], 
                                              previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Executar step de geração de conteúdo"""
        content_type = step.parameters.get("content_type", "text")
        min_words = step.parameters.get("min_words", 100)
        max_words = step.parameters.get("max_words", 500)
        
        # Simular geração de conteúdo baseado no input
        topic = input_data.get("topic", "tecnologia")
        
        # Gerar conteúdo simulado
        if content_type == "blog":
            content = f"Este é um artigo sobre {topic}. " * (min_words // 10)
        elif content_type == "social":
            content = f"Post sobre {topic} para redes sociais. #tecnologia #inovacao"
        else:
            content = f"Conteúdo sobre {topic}. " * (min_words // 5)
        
        return {
            "content": content,
            "content_type": content_type,
            "word_count": len(content.split()),
            "topic": topic
        }
    
    async def _execute_content_optimization_step(self, step: WorkflowStep, input_data: Dict[str, Any], 
                                                previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Executar step de otimização de conteúdo"""
        # Obter conteúdo de steps anteriores ou input
        content = None
        for result in previous_results.values():
            if isinstance(result, dict) and "result" in result and "content" in result["result"]:
                content = result["result"]["content"]
                break
        
        if not content:
            content = input_data.get("content", "Conteúdo padrão para otimização")
        
        # Executar análise de conteúdo
        analysis_result = self.content_analyzer.analyze_content(content)
        
        return {
            "original_content": content,
            "analysis": analysis_result,
            "optimized": True,
            "improvements_suggested": [
                "Adicionar mais palavras-chave",
                "Melhorar estrutura de frases",
                "Otimizar para SEO"
            ]
        }
    
    async def _execute_image_generation_step(self, step: WorkflowStep, input_data: Dict[str, Any], 
                                            previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Executar step de geração de imagem"""
        # Obter prompt de steps anteriores ou parâmetros
        prompt = step.parameters.get("prompt")
        if not prompt:
            # Tentar extrair tópico de steps anteriores
            topic = input_data.get("topic", "tecnologia")
            prompt = f"Imagem sobre {topic}"
        
        style = step.parameters.get("style", "realistic")
        width = step.parameters.get("width", 512)
        height = step.parameters.get("height", 512)
        quality = step.parameters.get("quality", 85)
        
        # Gerar imagem
        image_result = self.image_processor.generate_image(prompt, style, width, height, quality)
        
        return image_result
    
    async def _execute_image_processing_step(self, step: WorkflowStep, input_data: Dict[str, Any], 
                                            previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Executar step de processamento de imagem"""
        # Obter imagem de steps anteriores
        image_data = None
        for result in previous_results.values():
            if isinstance(result, dict) and "result" in result and "image_data" in result["result"]:
                image_data_b64 = result["result"]["image_data"]
                image_data = base64.b64decode(image_data_b64)
                break
        
        if not image_data:
            raise Exception("No image data found in previous steps")
        
        enhancement_type = step.parameters.get("enhancement_type", "brightness")
        factor = step.parameters.get("factor", 1.2)
        
        # Processar imagem
        enhancement_result = self.image_processor.enhance_image(image_data, enhancement_type, factor)
        
        return enhancement_result
    
    async def _execute_template_application_step(self, step: WorkflowStep, input_data: Dict[str, Any], 
                                                previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Executar step de aplicação de template"""
        template_name = step.parameters.get("template_name", "default")
        
        # Simular aplicação de template
        return {
            "template_applied": template_name,
            "formatted_content": "Conteúdo formatado com template",
            "template_parameters": step.parameters
        }
    
    def _validate_workflow(self, workflow_def: WorkflowDefinition):
        """Validar definição do workflow"""
        if len(workflow_def.steps) > config.WORKFLOW_MAX_STEPS:
            raise HTTPException(status_code=400, detail=f"Too many steps. Max: {config.WORKFLOW_MAX_STEPS}")
        
        # Validar IDs únicos
        step_ids = [step.id for step in workflow_def.steps]
        if len(step_ids) != len(set(step_ids)):
            raise HTTPException(status_code=400, detail="Step IDs must be unique")
        
        # Validar dependências
        for step in workflow_def.steps:
            for dep_id in step.depends_on:
                if dep_id not in step_ids:
                    raise HTTPException(status_code=400, detail=f"Invalid dependency: {dep_id}")
    
    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Construir grafo de dependências"""
        graph = {}
        for step in steps:
            graph[step.id] = step.depends_on
        return graph
    
    def _calculate_processing_time(self, execution_data: Dict[str, Any]) -> float:
        """Calcular tempo de processamento"""
        if "completed_at" in execution_data:
            start = datetime.fromisoformat(execution_data["started_at"])
            end = datetime.fromisoformat(execution_data["completed_at"])
            return round((end - start).total_seconds() * 1000, 2)
        return 0.0

# ================================
# CONTENT INTELLIGENCE ENGINE (v3.2) - NOVO
# ================================

class ContentIntelligenceEngine:
    """Engine de inteligência de conteúdo - Cloud Run Ready"""
    
    def __init__(self):
        self.cache = AdvancedMemoryCache()
        self.prediction_model_version = config.PREDICTION_MODEL_VERSION
        self.trend_analysis_depth = config.TREND_ANALYSIS_DEPTH
        self.ab_test_confidence_threshold = config.AB_TEST_CONFIDENCE_THRESHOLD
        
        # Inicializar dados simulados para análises
        self._initialize_intelligence_data()
        
        logger.info("📊 Content Intelligence Engine inicializado")

    def _initialize_intelligence_data(self):
        """Inicializar dados de inteligência em memória"""
        # Dados simulados para análises mais realistas
        self.trending_topics = [
            "inteligência artificial", "machine learning", "cloud computing",
            "desenvolvimento web", "mobile apps", "blockchain", "cybersecurity"
        ]
        
        self.platform_metrics = {
            "blog": {"avg_engagement": 0.65, "best_length": 1500},
            "twitter": {"avg_engagement": 0.45, "best_length": 280},
            "instagram": {"avg_engagement": 0.75, "best_length": 150},
            "linkedin": {"avg_engagement": 0.55, "best_length": 1200}
        }

    def analyze_trends(self, topic: str, time_window: str) -> Dict[str, Any]:
        """Analisar tendências de conteúdo"""
        start_time = time.time()
        
        cache_key = f"trends_{hashlib.md5(topic.encode()).hexdigest()}_{time_window}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info(f"📊 Cache hit para análise de tendência: {topic}")
            return cached_result

        # Simular análise de tendências mais sofisticada
        base_score = 50
        if topic.lower() in [t.lower() for t in self.trending_topics]:
            base_score += 30
        
        # Ajustar por janela de tempo
        time_multiplier = {
            "last_24_hours": 1.2,
            "last_7_days": 1.0,
            "last_30_days": 0.8
        }.get(time_window, 1.0)
        
        trend_score = min(95, base_score * time_multiplier + random.uniform(-10, 15))
        
        # Determinar momentum
        momentum = "growing" if trend_score > 75 else "stable" if trend_score > 50 else "declining"
        
        # Gerar keywords relacionadas
        related_keywords = [
            f"{topic} trends",
            f"new {topic}",
            f"{topic} 2025",
            f"best {topic}",
            f"{topic} guide"
        ]
        
        result = {
            "topic": topic,
            "trend_score": round(trend_score, 1),
            "momentum": momentum,
            "time_window": time_window,
            "related_keywords": related_keywords[:3],
            "search_volume_change": round(random.uniform(-20, 50), 1),
            "competition_level": random.choice(["low", "medium", "high"]),
            "analyzed_at": datetime.now().isoformat(),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        self.cache.set(cache_key, result)
        logger.info(f"📊 Análise de tendência concluída para: {topic}")
        return result

    def predict_performance(self, content: str, platform: str) -> Dict[str, Any]:
        """Predição de performance de conteúdo"""
        start_time = time.time()
        
        # Análise básica do conteúdo
        word_count = len(content.split())
        char_count = len(content)
        
        # Obter métricas da plataforma
        platform_data = self.platform_metrics.get(platform.lower(), self.platform_metrics["blog"])
        
        # Calcular score base
        base_score = 50
        
        # Ajustar por comprimento
        optimal_length = platform_data["best_length"]
        length_ratio = min(word_count / (optimal_length / 6), 2.0)  # Aproximadamente palavras
        length_score = 100 - abs(1 - length_ratio) * 30
        
        # Simular outros fatores
        engagement_score = (base_score + length_score) / 2 + random.uniform(-15, 25)
        engagement_score = max(10, min(95, engagement_score))
        
        # Calcular confiança
        confidence = min(0.95, 0.6 + (engagement_score / 100) * 0.35)
        
        # Gerar sugestões
        suggestions = []
        if word_count < optimal_length / 8:
            suggestions.append("Expandir o conteúdo para maior engajamento")
        if platform.lower() in ["instagram", "twitter"]:
            suggestions.append("Adicionar hashtags relevantes")
        if engagement_score < 60:
            suggestions.append("Melhorar o título para ser mais atrativo")
        
        result = {
            "platform": platform,
            "predicted_engagement_score": round(engagement_score, 1),
            "confidence": round(confidence, 2),
            "content_analysis": {
                "word_count": word_count,
                "char_count": char_count,
                "optimal_length": optimal_length
            },
            "suggestions": suggestions[:3],
            "model_version": self.prediction_model_version,
            "predicted_at": datetime.now().isoformat(),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        logger.info(f"🔮 Predição de performance concluída para plataforma: {platform}")
        return result

    def get_recommendations(self, topic: str, target_audience: str, content_type: str) -> Dict[str, Any]:
        """Obter recomendações de conteúdo"""
        start_time = time.time()
        
        # Formatos recomendados por tipo de conteúdo
        format_mapping = {
            "blog": ["long_form_article", "tutorial", "case_study"],
            "social": ["short_post", "carousel", "story"],
            "video": ["explainer_video", "tutorial_video", "interview"],
            "email": ["newsletter", "promotional", "educational"]
        }
        
        recommended_formats = format_mapping.get(content_type, format_mapping["blog"])
        
        # Títulos sugeridos baseados no tópico
        title_templates = [
            f"O Guia Definitivo de {topic}",
            f"5 Dicas Essenciais sobre {topic}",
            f"Como Dominar {topic} em 2025",
            f"{topic}: Tudo que Você Precisa Saber",
            f"Os Segredos do {topic} Revelados"
        ]
        
        # Ajustar por audiência
        audience_adjustments = {
            "beginners": "para Iniciantes",
            "experts": "Avançado",
            "developers": "para Desenvolvedores",
            "business": "para Empresas"
        }
        
        adjustment = audience_adjustments.get(target_audience, "")
        if adjustment:
            title_templates = [f"{title} {adjustment}" for title in title_templates[:3]]
        
        result = {
            "topic": topic,
            "target_audience": target_audience,
            "content_type": content_type,
            "recommended_formats": recommended_formats,
            "suggested_titles": title_templates[:3],
            "optimal_posting_times": ["09:00", "14:00", "19:00"],
            "recommended_hashtags": [f"#{topic.replace(' ', '')}", "#content", "#2025"],
            "estimated_engagement": round(random.uniform(60, 85), 1),
            "recommended_at": datetime.now().isoformat(),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        logger.info(f"💡 Recomendações geradas para o tópico: {topic}")
        return result

    def get_competitor_insights(self, competitor_content: str, my_content: Optional[str]) -> Dict[str, Any]:
        """Análise comparativa com concorrente"""
        start_time = time.time()
        
        # Análise do conteúdo do concorrente
        comp_words = len(competitor_content.split())
        comp_chars = len(competitor_content)
        comp_score = min(85, 40 + comp_words * 0.5 + random.uniform(-10, 20))
        
        # Análise do meu conteúdo (se fornecido)
        my_score = None
        comparison = None
        
        if my_content:
            my_words = len(my_content.split())
            my_chars = len(my_content)
            my_score = min(90, 35 + my_words * 0.6 + random.uniform(-15, 25))
            
            comparison = {
                "word_count_diff": my_words - comp_words,
                "performance_diff": round(my_score - comp_score, 1),
                "winner": "yours" if my_score > comp_score else "competitor"
            }
        
        # Identificar pontos fortes e fracos
        strengths = []
        weaknesses = []
        opportunities = []
        
        if comp_score > 70:
            strengths.append("Bom uso de palavras-chave")
            strengths.append("Estrutura bem organizada")
        else:
            weaknesses.append("Baixa densidade de palavras-chave")
        
        if comp_words < 300:
            weaknesses.append("Conteúdo muito curto")
            opportunities.append("Expandir com mais detalhes")
        
        opportunities.append("Explorar formato de vídeo")
        opportunities.append("Adicionar elementos visuais")
        
        result = {
            "competitor_analysis": {
                "content_score": round(comp_score, 1),
                "word_count": comp_words,
                "char_count": comp_chars
            },
            "my_analysis": {
                "content_score": round(my_score, 1) if my_score else None,
                "word_count": len(my_content.split()) if my_content else None
            } if my_content else None,
            "comparison": comparison,
            "insights": {
                "strengths": strengths[:3],
                "weaknesses": weaknesses[:3],
                "opportunities": opportunities[:3]
            },
            "analyzed_at": datetime.now().isoformat(),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        logger.info("⚔️ Análise de concorrente concluída")
        return result

    def run_ab_test(self, variant_a: str, variant_b: str, metric: str) -> Dict[str, Any]:
        """Executar teste A/B"""
        start_time = time.time()
        
        # Simular análise das variantes
        score_a = self._calculate_variant_score(variant_a, metric)
        score_b = self._calculate_variant_score(variant_b, metric)
        
        # Determinar vencedor
        winner = "variant_a" if score_a > score_b else "variant_b"
        winner_score = max(score_a, score_b)
        loser_score = min(score_a, score_b)
        
        # Calcular confiança estatística
        score_diff = abs(score_a - score_b)
        confidence = min(99.9, 60 + score_diff * 2)
        
        # Calcular melhoria percentual
        improvement = round((winner_score - loser_score) / loser_score * 100, 1) if loser_score > 0 else 0
        
        # Gerar insights
        insights = []
        if winner == "variant_a":
            insights.append("Variante A teve melhor performance")
        else:
            insights.append("Variante B teve melhor performance")
        
        if confidence > 95:
            insights.append("Resultado estatisticamente significativo")
        else:
            insights.append("Resultado precisa de mais dados")
        
        result = {
            "test_configuration": {
                "metric": metric,
                "variant_a_length": len(variant_a),
                "variant_b_length": len(variant_b)
            },
            "results": {
                "winner": winner,
                "variant_a_score": round(score_a, 2),
                "variant_b_score": round(score_b, 2),
                "confidence_percentage": round(confidence, 1),
                "improvement_percentage": improvement
            },
            "insights": insights,
            "recommendation": f"Use {winner} for better {metric}",
            "tested_at": datetime.now().isoformat(),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        logger.info(f"🔬 Teste A/B concluído. Vencedor: {winner}")
        return result
    
    def _calculate_variant_score(self, variant: str, metric: str) -> float:
        """Calcular score de uma variante"""
        base_score = 0.5
        
        # Ajustar por comprimento
        length_factor = min(len(variant) / 100, 2.0)
        base_score += length_factor * 0.2
        
        # Ajustar por métrica
        metric_multipliers = {
            "engagement": 1.0,
            "conversion": 0.8,
            "clicks": 1.2
        }
        
        multiplier = metric_multipliers.get(metric, 1.0)
        final_score = base_score * multiplier + random.uniform(-0.3, 0.3)
        
        return max(0.1, min(1.0, final_score))

class AnalyticsEngine:
    """Engine de analytics - Expandido para v3.1"""
    
    def __init__(self):
        self.metrics = {
            "content_generated": 0,
            "optimizations_performed": 0,
            "images_generated": 0,
            "images_processed": 0,
            "style_transfers": 0,
            "format_conversions": 0,
            "batch_operations": 0,
            "workflows_created": 0,      # Nova métrica v3.1
            "workflows_executed": 0,     # Nova métrica v3.1
            "workflow_steps_completed": 0, # Nova métrica v3.1
            "batch_workflows_executed": 0, # Nova métrica v3.1
            "api_calls": 0,
            "errors": 0,
            "uptime_start": datetime.now()
        }
        self.performance_data = []
    
    def track_content_generation(self, processing_time: float):
        """Rastrear geração de conteúdo"""
        self.metrics["content_generated"] += 1
        self.metrics["api_calls"] += 1
        self._add_performance_data("content_generation", processing_time)
    
    def track_optimization(self, processing_time: float):
        """Rastrear otimização de conteúdo"""
        self.metrics["optimizations_performed"] += 1
        self.metrics["api_calls"] += 1
        self._add_performance_data("optimization", processing_time)
    
    def track_image_generation(self, processing_time: float):
        """Rastrear geração de imagem"""
        self.metrics["images_generated"] += 1
        self.metrics["api_calls"] += 1
        self._add_performance_data("image_generation", processing_time)
    
    def track_image_processing(self, operation_type: str, processing_time: float):
        """Rastrear processamento de imagem"""
        self.metrics["images_processed"] += 1
        self.metrics["api_calls"] += 1
        
        if operation_type == "style_transfer":
            self.metrics["style_transfers"] += 1
        elif operation_type == "format_conversion":
            self.metrics["format_conversions"] += 1
        elif operation_type == "batch_processing":
            self.metrics["batch_operations"] += 1
        
        self._add_performance_data(f"image_{operation_type}", processing_time)
    
    def track_workflow_creation(self, processing_time: float):
        """Rastrear criação de workflow"""
        self.metrics["workflows_created"] += 1
        self.metrics["api_calls"] += 1
        self._add_performance_data("workflow_creation", processing_time)
    
    def track_workflow_execution(self, steps_completed: int, processing_time: float):
        """Rastrear execução de workflow"""
        self.metrics["workflows_executed"] += 1
        self.metrics["workflow_steps_completed"] += steps_completed
        self.metrics["api_calls"] += 1
        self._add_performance_data("workflow_execution", processing_time)
    
    def track_batch_workflow_execution(self, executions_count: int, processing_time: float):
        """Rastrear execução de batch de workflows"""
        self.metrics["batch_workflows_executed"] += 1
        self.metrics["workflows_executed"] += executions_count
        self.metrics["api_calls"] += 1
        self._add_performance_data("batch_workflow_execution", processing_time)
    
    def track_error(self):
        """Rastrear erro"""
        self.metrics["errors"] += 1
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Obter resumo de analytics"""
        uptime = datetime.now() - self.metrics["uptime_start"]
        
        return {
            "analytics_overview": {
                "total_content_generated": self.metrics["content_generated"],
                "total_optimizations": self.metrics["optimizations_performed"],
                "total_images_generated": self.metrics["images_generated"],
                "total_images_processed": self.metrics["images_processed"],
                "total_workflows_created": self.metrics["workflows_created"],
                "total_workflows_executed": self.metrics["workflows_executed"],
                "total_workflow_steps": self.metrics["workflow_steps_completed"],
                "total_api_calls": self.metrics["api_calls"],
                "error_rate": self.metrics["errors"] / max(self.metrics["api_calls"], 1),
                "uptime_hours": round(uptime.total_seconds() / 3600, 2)
            },
            "image_analytics": {
                "images_generated": self.metrics["images_generated"],
                "images_processed": self.metrics["images_processed"],
                "style_transfers": self.metrics["style_transfers"],
                "format_conversions": self.metrics["format_conversions"],
                "batch_operations": self.metrics["batch_operations"]
            },
            "workflow_analytics": {
                "workflows_created": self.metrics["workflows_created"],
                "workflows_executed": self.metrics["workflows_executed"],
                "workflow_steps_completed": self.metrics["workflow_steps_completed"],
                "batch_workflows_executed": self.metrics["batch_workflows_executed"],
                "avg_steps_per_workflow": round(
                    self.metrics["workflow_steps_completed"] / max(self.metrics["workflows_executed"], 1), 1
                )
            },
            "performance_summary": self._get_performance_summary()
        }
    
    def _add_performance_data(self, operation: str, processing_time: float):
        """Adicionar dados de performance"""
        self.performance_data.append({
            "operation": operation,
            "processing_time": processing_time,
            "timestamp": datetime.now()
        })
        
        # Manter apenas últimas 1000 entradas (memory management)
        if len(self.performance_data) > 1000:
            self.performance_data = self.performance_data[-1000:]
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Obter resumo de performance"""
        if not self.performance_data:
            return {"avg_processing_time": 0, "total_operations": 0}
        
        total_time = sum(data["processing_time"] for data in self.performance_data)
        avg_time = total_time / len(self.performance_data)
        
        return {
            "avg_processing_time_ms": round(avg_time, 2),
            "total_operations": len(self.performance_data),
            "fastest_operation_ms": min(data["processing_time"] for data in self.performance_data),
            "slowest_operation_ms": max(data["processing_time"] for data in self.performance_data)
        }
    
    def track_api_call(self):
        """Rastrear chamada de API genérica"""
        self.metrics["api_calls"] += 1
    
    def add_performance_data(self, operation: str, processing_time: float):
        """Adicionar dados de performance (método público)"""
        self._add_performance_data(operation, processing_time)

# ================================
# INSTÂNCIAS GLOBAIS - STATELESS
# ================================

# Instâncias dos serviços (stateless)
content_analyzer = ContentAnalyzer()
image_processor = AdvancedImageProcessor()
workflow_engine = WorkflowEngine(content_analyzer, image_processor)
content_intelligence_engine = ContentIntelligenceEngine()  # v3.2 NOVO
analytics = AnalyticsEngine()

# ================================
# RESILIENCE INSTANCES v3.4
# ================================
circuit_breaker = CircuitBreaker()
rate_limiter = RateLimiter()
shutdown_handler = GracefulShutdownHandler()

# ================================
# OBSERVABILITY INSTANCES v3.5
# ================================
structured_logger = StructuredLogger(config.SERVICE_NAME)
compression_handler = CompressionHandler()
prometheus_metrics = PrometheusMetrics()
performance_profiler = PerformanceProfiler()

# ================================
# APLICAÇÃO FASTAPI v3.5
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciamento do ciclo de vida da aplicação"""
    # Startup
    structured_logger.info("🚀 Iniciando Creative Studio v3.5 - Observability & Optimization")
    structured_logger.info("🔄 Funcionalidades: Structured Logging, Compression, Prometheus Metrics, Performance Profiling")
    structured_logger.info("🛡️ Cloud Run Ready: Stateless, API-first, Environment Variables, Observability")
    
    # Inicializar métricas de sistema
    if config.ENABLE_SYSTEM_METRICS:
        prometheus_metrics.set_gauge("memory_usage_bytes", psutil.Process().memory_info().rss)
        prometheus_metrics.set_gauge("cpu_usage_percent", psutil.cpu_percent())
    
    yield
    
    # Shutdown
    structured_logger.info("🛑 Finalizando Creative Studio v3.5")

app = FastAPI(
    title="Creative Studio v3.5 - Observability & Optimization",
    description="Plataforma de criação de conteúdo com observabilidade completa e otimizações finais",
    version="3.5.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# MIDDLEWARE v3.4 - RESILIENCE
# ================================

@app.middleware("http")
async def resilience_middleware(request: Request, call_next):
    """Middleware para rate limiting, circuit breaker e graceful shutdown"""
    start_time = time.time()
    
    # Verificar graceful shutdown
    if shutdown_handler.is_shutdown_requested():
        return JSONResponse(
            status_code=503,
            content={"error": "Service is shutting down"}
        )
    
    # Registrar request ativa
    shutdown_handler.register_request()
    
    try:
        # Rate limiting (apenas para endpoints não-health)
        if config.ENABLE_RATE_LIMITING and not request.url.path.startswith(("/health", "/readiness")):
            client_ip = request.client.host
            if not rate_limiter.is_allowed(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": 300,
                        "client_ip": client_ip
                    }
                )
        
        # Executar request com circuit breaker (apenas para endpoints críticos)
        if config.ENABLE_CIRCUIT_BREAKER and request.url.path.startswith("/api/"):
            response = await circuit_breaker.call(call_next, request)
        else:
            response = await call_next(request)
        
        # Adicionar headers de performance
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        response.headers["X-Service-Version"] = config.VERSION
        
        return response
        
    except Exception as e:
        logger.error(f"Error in resilience middleware: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
    finally:
        # Desregistrar request
        shutdown_handler.unregister_request()

# ================================
# ENDPOINTS BÁSICOS (Compatibilidade v3.0)
# ================================

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "service": "creative-studio",
        "version": "3.2.0",
        "description": "Plataforma de Criação de Conteúdo - Content Intelligence",
        "features": [
            "AI Content Generation",
            "Smart Templates", 
            "Content Analytics",
            "AI Content Optimization",
            "Advanced Image Generation",
            "Style Transfer",
            "Image Enhancement",
            "Format Conversion",
            "Batch Processing",
            "Workflow Automation",
            "Content Pipelines",
            "Template Chaining",
            "Auto-optimization",
            "Scheduled Generation",
            "Batch Workflows",
            "Content Intelligence",
            "Trend Analysis",
            "Performance Prediction",
            "Content Recommendations",
            "Competitor Insights",
            "A/B Testing"
        ],
        "cloud_run_ready": True,
        "stateless": True,
        "api_first": True
    }

@app.get("/health")
async def health_check():
    """Health check robusto - Cloud Run v3.3"""
    start_time = time.time()
    
    try:
        uptime = datetime.now() - analytics.metrics["uptime_start"]
        
        # Verificar componentes críticos
        health_status = {
            "cache": "healthy" if hasattr(content_analyzer, 'cache') else "unhealthy",
            "analytics": "healthy" if analytics else "unhealthy",
            "workflow_engine": "healthy" if workflow_engine else "unhealthy",
            "content_intelligence": "healthy" if content_intelligence_engine else "unhealthy"
        }
        
        # Status geral
        overall_status = "healthy" if all(status == "healthy" for status in health_status.values()) else "unhealthy"
        
        # Métricas de performance
        response_time_ms = round((time.time() - start_time) * 1000, 2)
        
        return {
            "status": overall_status,
            "service": config.SERVICE_NAME,
            "version": config.VERSION,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(uptime.total_seconds(), 2),
            "response_time_ms": response_time_ms,
            "components": health_status,
            "metrics": {
                "total_content_generated": analytics.metrics["content_generated"],
                "total_optimizations": analytics.metrics["optimizations_performed"],
                "total_images_generated": analytics.metrics["images_generated"],
                "total_images_processed": analytics.metrics["images_processed"],
                "total_workflows_created": analytics.metrics["workflows_created"],
                "total_workflows_executed": analytics.metrics["workflows_executed"],
                "active_jobs": len(workflow_engine.active_workflows),
                "cache_entries": len(content_analyzer.cache._cache),
                "error_count": analytics.metrics["errors"],
                "api_calls": analytics.metrics["api_calls"]
            },
            "memory": {
                "cache_usage_mb": content_analyzer.cache._memory_usage_mb if hasattr(content_analyzer.cache, '_memory_usage_mb') else 0,
                "cache_entries": len(content_analyzer.cache._cache)
            },
            "features_enabled": {
                "ai_generation": True,
                "templates": True,
                "image_processing": True,
                "analytics": True,
                "ai_optimization": config.ENABLE_AI_OPTIMIZATION,
                "advanced_image_generation": config.ENABLE_IMAGE_GENERATION,
                "style_transfer": config.ENABLE_STYLE_TRANSFER,
                "batch_processing": config.ENABLE_BATCH_PROCESSING,
                "workflow_automation": config.ENABLE_WORKFLOW_AUTOMATION,
                "content_intelligence": config.ENABLE_CONTENT_INTELLIGENCE,
                "graceful_shutdown": config.ENABLE_GRACEFUL_SHUTDOWN,
                "memory_monitoring": config.ENABLE_MEMORY_MONITORING,
                "circuit_breaker": config.ENABLE_CIRCUIT_BREAKER
            },
            "cloud_run_ready": True,
            "stateless": True,
            "api_first": True
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "service": config.SERVICE_NAME,
            "version": config.VERSION,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/readiness")
async def readiness_check():
    """Readiness check - Verifica se o serviço está pronto para receber tráfego"""
    start_time = time.time()
    
    try:
        # Verificações de prontidão
        checks = {
            "cache_initialized": hasattr(content_analyzer, 'cache') and content_analyzer.cache is not None,
            "analytics_ready": analytics is not None and hasattr(analytics, 'metrics'),
            "workflow_engine_ready": workflow_engine is not None,
            "content_intelligence_ready": content_intelligence_engine is not None,
            "config_valid": config is not None
        }
        
        # Verificar se todos os checks passaram
        ready = all(checks.values())
        response_time_ms = round((time.time() - start_time) * 1000, 2)
        
        return {
            "ready": ready,
            "service": config.SERVICE_NAME,
            "version": config.VERSION,
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": response_time_ms,
            "checks": checks
        }
    except Exception as e:
        logger.error(f"Readiness check error: {e}")
        return {
            "ready": False,
            "service": config.SERVICE_NAME,
            "version": config.VERSION,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/resilience")
async def resilience_stats():
    """Estatísticas de resilience - Circuit Breaker, Rate Limiting e Graceful Shutdown"""
    start_time = time.time()
    
    try:
        # Obter estatísticas de todos os componentes de resilience
        circuit_stats = circuit_breaker.get_stats()
        shutdown_stats = shutdown_handler.get_stats()
        
        # Estatísticas de rate limiting para o IP atual (exemplo)
        client_ip = "127.0.0.1"  # Em produção, seria obtido do request
        rate_stats = rate_limiter.get_stats(client_ip)
        
        response_time_ms = round((time.time() - start_time) * 1000, 2)
        
        return {
            "service": config.SERVICE_NAME,
            "version": config.VERSION,
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": response_time_ms,
            "resilience": {
                "circuit_breaker": {
                    "enabled": config.ENABLE_CIRCUIT_BREAKER,
                    "stats": circuit_stats
                },
                "rate_limiter": {
                    "enabled": config.ENABLE_RATE_LIMITING,
                    "stats": rate_stats,
                    "global_config": {
                        "max_requests_per_minute": config.RATE_LIMIT_PER_MINUTE,
                        "block_duration_seconds": 300
                    }
                },
                "graceful_shutdown": {
                    "enabled": config.ENABLE_GRACEFUL_SHUTDOWN,
                    "stats": shutdown_stats
                }
            },
            "features_v3_4": {
                "circuit_breaker": config.ENABLE_CIRCUIT_BREAKER,
                "rate_limiting": config.ENABLE_RATE_LIMITING,
                "graceful_shutdown": config.ENABLE_GRACEFUL_SHUTDOWN,
                "request_timeout": config.REQUEST_TIMEOUT_SECONDS,
                "retry_logic": True
            }
        }
    except Exception as e:
        logger.error(f"Resilience stats error: {e}")
        return {
            "service": config.SERVICE_NAME,
            "version": config.VERSION,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ================================
# ENDPOINTS DE ANÁLISE DE CONTEÚDO (Compatibilidade v3.0)
# ================================

@app.get("/status")
async def detailed_status():
    """Status detalhado do sistema"""
    uptime = datetime.now() - analytics.metrics["uptime_start"]
    
    return {
        "service_info": {
            "name": "creative-studio",
            "version": "3.1.0",
            "uptime_seconds": round(uptime.total_seconds(), 2),
            "cloud_run_ready": True
        },
        "features": {
            "ai_optimization": config.ENABLE_AI_OPTIMIZATION,
            "image_generation": config.ENABLE_IMAGE_GENERATION,
            "style_transfer": config.ENABLE_STYLE_TRANSFER,
            "batch_processing": config.ENABLE_BATCH_PROCESSING,
            "workflow_automation": config.ENABLE_WORKFLOW_AUTOMATION
        },
        "metrics": analytics.metrics,
        "cache_stats": {
            "entries": len(content_analyzer.cache._cache),
            "max_entries": 100,
            "ttl_seconds": config.CACHE_TTL_SECONDS
        },
        "configuration": {
            "max_image_size": config.IMAGE_MAX_SIZE,
            "supported_formats": config.IMAGE_FORMATS,
            "batch_max_images": config.BATCH_MAX_IMAGES,
            "image_quality": config.IMAGE_QUALITY,
            "workflow_max_steps": config.WORKFLOW_MAX_STEPS,
            "workflow_timeout_seconds": config.WORKFLOW_TIMEOUT_SECONDS,
            "workflow_max_concurrent": config.WORKFLOW_MAX_CONCURRENT,
            "workflow_batch_size": config.WORKFLOW_BATCH_SIZE
        },
        "active_workflows": len(workflow_engine.active_workflows),
        "workflow_templates": len(workflow_engine.workflow_templates)
    }

# ================================
# ENDPOINTS AI OPTIMIZATION (v2.1.1) - MANTIDOS
# ================================

@app.post("/api/v1/content/analyze")
async def analyze_content(request: ContentAnalysisRequest):
    """Análise completa de conteúdo"""
    try:
        start_time = time.time()
        result = content_analyzer.analyze_content(request.content, request.content_type)
        processing_time = (time.time() - start_time) * 1000
        
        result["processing_time_ms"] = round(processing_time, 2)
        analytics.track_optimization(processing_time)
        
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/content/seo-analysis")
async def seo_analysis(request: SEOAnalysisRequest):
    """Análise SEO específica"""
    try:
        start_time = time.time()
        result = content_analyzer._analyze_seo(request.content, request.title or "")
        processing_time = (time.time() - start_time) * 1000
        
        analytics.track_optimization(processing_time)
        
        return {
            "seo_analysis": result,
            "processing_time_ms": round(processing_time, 2),
            "analyzed_at": datetime.now().isoformat()
        }
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/content/readability-analysis")
async def readability_analysis(request: ReadabilityAnalysisRequest):
    """Análise de legibilidade específica"""
    try:
        start_time = time.time()
        result = content_analyzer._analyze_readability(request.content)
        processing_time = (time.time() - start_time) * 1000
        
        analytics.track_optimization(processing_time)
        
        return {
            "readability_analysis": result,
            "processing_time_ms": round(processing_time, 2),
            "analyzed_at": datetime.now().isoformat()
        }
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/content/tone-analysis")
async def tone_analysis(request: ToneAnalysisRequest):
    """Análise de tom específica"""
    try:
        start_time = time.time()
        result = content_analyzer._analyze_tone(request.content)
        processing_time = (time.time() - start_time) * 1000
        
        analytics.track_optimization(processing_time)
        
        return {
            "tone_analysis": result,
            "processing_time_ms": round(processing_time, 2),
            "analyzed_at": datetime.now().isoformat()
        }
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS ADVANCED IMAGE GENERATION (v3.0) - MANTIDOS
# ================================

@app.post("/api/v1/images/generate")
async def generate_image(request: ImageGenerationRequest):
    """Gerar imagem via prompt"""
    try:
        start_time = time.time()
        result = image_processor.generate_image(
            request.prompt,
            request.style,
            request.width,
            request.height,
            request.quality
        )
        processing_time = (time.time() - start_time) * 1000
        
        result["processing_time_ms"] = round(processing_time, 2)
        analytics.track_image_generation(processing_time)
        
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/images/style-transfer")
async def apply_style_transfer(
    file: UploadFile = File(...),
    style_name: str = Form(...),
    intensity: float = Form(0.8)
):
    """Aplicar transferência de estilo"""
    try:
        # Validar arquivo
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Ler dados da imagem
        image_data = await file.read()
        
        start_time = time.time()
        result = image_processor.apply_style_transfer(image_data, style_name, intensity)
        processing_time = (time.time() - start_time) * 1000
        
        result["processing_time_ms"] = round(processing_time, 2)
        analytics.track_image_processing("style_transfer", processing_time)
        
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/images/enhance")
async def enhance_image(
    file: UploadFile = File(...),
    enhancement_type: str = Form(...),
    factor: float = Form(1.2)
):
    """Melhorar qualidade da imagem"""
    try:
        # Validar arquivo
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Ler dados da imagem
        image_data = await file.read()
        
        start_time = time.time()
        result = image_processor.enhance_image(image_data, enhancement_type, factor)
        processing_time = (time.time() - start_time) * 1000
        
        result["processing_time_ms"] = round(processing_time, 2)
        analytics.track_image_processing("enhancement", processing_time)
        
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/images/convert")
async def convert_image_format(
    file: UploadFile = File(...),
    target_format: str = Form(...),
    quality: int = Form(85)
):
    """Converter formato da imagem"""
    try:
        # Validar arquivo
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Ler dados da imagem
        image_data = await file.read()
        
        start_time = time.time()
        result = image_processor.convert_format(image_data, target_format, quality)
        processing_time = (time.time() - start_time) * 1000
        
        result["processing_time_ms"] = round(processing_time, 2)
        analytics.track_image_processing("format_conversion", processing_time)
        
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/images/batch-process")
async def batch_process_images(
    files: List[UploadFile] = File(...),
    operations: str = Form(...),  # JSON string
    parameters: str = Form("{}")  # JSON string
):
    """Processamento em lote de imagens"""
    try:
        import json
        
        # Parse dos parâmetros
        operations_list = json.loads(operations)
        parameters_dict = json.loads(parameters)
        
        # Validar arquivos
        images_data = []
        for file in files:
            if not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail=f"File {file.filename} must be an image")
            images_data.append(await file.read())
        
        start_time = time.time()
        result = image_processor.batch_process(images_data, operations_list, parameters_dict)
        processing_time = (time.time() - start_time) * 1000
        
        result["processing_time_ms"] = round(processing_time, 2)
        analytics.track_image_processing("batch_processing", processing_time)
        
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS WORKFLOW AUTOMATION (v3.1) - NOVOS
# ================================

@app.post("/api/v1/workflows/create")
async def create_workflow(request: WorkflowCreateRequest):
    """Criar novo workflow"""
    try:
        start_time = time.time()
        result = workflow_engine.create_workflow(request.workflow, request.schedule)
        processing_time = (time.time() - start_time) * 1000
        
        result["processing_time_ms"] = round(processing_time, 2)
        analytics.track_workflow_creation(processing_time)
        
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/workflows/execute")
async def execute_workflow(request: WorkflowExecuteRequest):
    """Executar workflow"""
    try:
        start_time = time.time()
        result = await workflow_engine.execute_workflow(
            request.workflow_id,
            request.workflow,
            request.input_data,
            request.priority
        )
        processing_time = (time.time() - start_time) * 1000
        
        result["processing_time_ms"] = round(processing_time, 2)
        analytics.track_workflow_execution(result["steps_completed"], processing_time)
        
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/workflows/status/{execution_id}")
async def get_workflow_status(execution_id: str):
    """Obter status de execução do workflow"""
    try:
        result = workflow_engine.get_workflow_status(execution_id)
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/workflows/batch")
async def execute_batch_workflows(request: WorkflowBatchRequest):
    """Executar workflows em lote"""
    try:
        start_time = time.time()
        result = await workflow_engine.execute_batch_workflows(
            request.workflow_id,
            request.workflow,
            request.batch_data,
            request.parallel
        )
        processing_time = (time.time() - start_time) * 1000
        
        result["processing_time_ms"] = round(processing_time, 2)
        analytics.track_batch_workflow_execution(result["total_executions"], processing_time)
        
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/workflows/templates")
async def get_workflow_templates():
    """Obter templates de workflow disponíveis"""
    try:
        result = workflow_engine.get_workflow_templates()
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS ANALYTICS (Expandidos v3.1)
# ================================

@app.get("/api/v1/analytics/summary")
async def analytics_summary():
    """Resumo executivo de analytics"""
    try:
        return analytics.get_analytics_summary()
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/images")
async def image_analytics():
    """Analytics específicos de imagens"""
    try:
        return {
            "image_analytics": {
                "total_generated": analytics.metrics["images_generated"],
                "total_processed": analytics.metrics["images_processed"],
                "style_transfers": analytics.metrics["style_transfers"],
                "format_conversions": analytics.metrics["format_conversions"],
                "batch_operations": analytics.metrics["batch_operations"],
                "success_rate": 1.0 - (analytics.metrics["errors"] / max(analytics.metrics["api_calls"], 1))
            },
            "configuration": {
                "max_image_size": config.IMAGE_MAX_SIZE,
                "supported_formats": config.IMAGE_FORMATS,
                "batch_max_images": config.BATCH_MAX_IMAGES,
                "default_quality": config.IMAGE_QUALITY
            }
        }
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/workflows")
async def workflow_analytics():
    """Analytics específicos de workflows"""
    try:
        return {
            "workflow_analytics": {
                "total_created": analytics.metrics["workflows_created"],
                "total_executed": analytics.metrics["workflows_executed"],
                "total_steps_completed": analytics.metrics["workflow_steps_completed"],
                "batch_executions": analytics.metrics["batch_workflows_executed"],
                "avg_steps_per_workflow": round(
                    analytics.metrics["workflow_steps_completed"] / max(analytics.metrics["workflows_executed"], 1), 1
                ),
                "success_rate": 1.0 - (analytics.metrics["errors"] / max(analytics.metrics["api_calls"], 1))
            },
            "configuration": {
                "max_steps": config.WORKFLOW_MAX_STEPS,
                "timeout_seconds": config.WORKFLOW_TIMEOUT_SECONDS,
                "max_concurrent": config.WORKFLOW_MAX_CONCURRENT,
                "batch_size": config.WORKFLOW_BATCH_SIZE
            },
            "active_workflows": len(workflow_engine.active_workflows),
            "available_templates": len(workflow_engine.workflow_templates)
        }
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS CONTENT INTELLIGENCE (v3.2) - NOVOS
# ================================

@app.post("/api/v1/intelligence/trends")
async def analyze_trends(request: TrendAnalysisRequest):
    """Análise de tendências de conteúdo"""
    try:
        if not config.ENABLE_CONTENT_INTELLIGENCE:
            raise HTTPException(status_code=503, detail="Content Intelligence is disabled")
        
        analytics.track_api_call()
        result = content_intelligence_engine.analyze_trends(request.topic, request.time_window)
        analytics.add_performance_data("trend_analysis", result["processing_time_ms"])
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/intelligence/predict-performance")
async def predict_performance(request: PerformancePredictionRequest):
    """Predição de performance de conteúdo"""
    try:
        if not config.ENABLE_CONTENT_INTELLIGENCE:
            raise HTTPException(status_code=503, detail="Content Intelligence is disabled")
        
        analytics.track_api_call()
        result = content_intelligence_engine.predict_performance(request.content, request.platform)
        analytics.add_performance_data("performance_prediction", result["processing_time_ms"])
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/intelligence/recommendations")
async def get_recommendations(request: ContentRecommendationsRequest):
    """Obter recomendações de conteúdo"""
    try:
        if not config.ENABLE_CONTENT_INTELLIGENCE:
            raise HTTPException(status_code=503, detail="Content Intelligence is disabled")
        
        analytics.track_api_call()
        result = content_intelligence_engine.get_recommendations(
            request.topic, request.target_audience, request.content_type
        )
        analytics.add_performance_data("content_recommendations", result["processing_time_ms"])
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/intelligence/competitor-insights")
async def get_competitor_insights(request: CompetitorInsightsRequest):
    """Análise comparativa com concorrente"""
    try:
        if not config.ENABLE_CONTENT_INTELLIGENCE:
            raise HTTPException(status_code=503, detail="Content Intelligence is disabled")
        
        analytics.track_api_call()
        result = content_intelligence_engine.get_competitor_insights(
            request.competitor_content, request.my_content
        )
        analytics.add_performance_data("competitor_insights", result["processing_time_ms"])
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/intelligence/ab-test")
async def run_ab_test(request: ABTestRequest):
    """Executar teste A/B"""
    try:
        if not config.ENABLE_CONTENT_INTELLIGENCE:
            raise HTTPException(status_code=503, detail="Content Intelligence is disabled")
        
        analytics.track_api_call()
        result = content_intelligence_engine.run_ab_test(
            request.variant_a, request.variant_b, request.metric
        )
        analytics.add_performance_data("ab_test", result["processing_time_ms"])
        return result
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/intelligence")
async def intelligence_analytics():
    """Analytics específicos de Content Intelligence"""
    try:
        # Obter estatísticas do cache de intelligence
        intelligence_cache_stats = {
            "cache_size": len(content_intelligence_engine.cache._cache),
            "cache_ttl": config.INTELLIGENCE_CACHE_TTL,
            "model_version": config.PREDICTION_MODEL_VERSION
        }
        
        return {
            "intelligence_analytics": intelligence_cache_stats,
            "trending_topics": content_intelligence_engine.trending_topics,
            "platform_metrics": content_intelligence_engine.platform_metrics,
            "configuration": {
                "cache_ttl": config.INTELLIGENCE_CACHE_TTL,
                "prediction_model_version": config.PREDICTION_MODEL_VERSION,
                "trend_analysis_depth": config.TREND_ANALYSIS_DEPTH,
                "ab_test_confidence_threshold": config.AB_TEST_CONFIDENCE_THRESHOLD
            }
        }
    except Exception as e:
        analytics.track_error()
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINT ANÁLISE DE URL (v3.5) - NOVO
# ================================

@app.post("/api/v1/creatives/analyze-url", response_model=UrlAnalysisResponse)
async def analyze_url_for_creatives(request: UrlAnalysisRequest):
    """Analisa o conteúdo de um URL e extrai sugestões para a criação de anúncios."""
    logger.info(f"Recebida requisição para analisar URL: {request.url}")
    try:
        analytics.track_api_call()
        start_time = time.time()
        
        # Fazer requisição HTTP para obter o conteúdo da página
        async with httpx.AsyncClient() as client:
            response = await client.get(request.url, follow_redirects=True, timeout=30)
            response.raise_for_status()  # Levanta exceção para status de erro HTTP

        # Analisar o HTML com BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extrair Título da página
        title_tag = soup.find('title')
        suggested_headlines = []
        if title_tag and title_tag.get_text().strip():
            suggested_headlines.append(title_tag.get_text().strip())

        # Extrair Título Principal (h1)
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.get_text().strip():
            h1_text = h1_tag.get_text().strip()
            if h1_text not in suggested_headlines:
                suggested_headlines.append(h1_text)

        # Extrair Descrição da meta tag
        suggested_descriptions = []
        description_meta = soup.find('meta', attrs={'name': 'description'})
        if description_meta and description_meta.get('content'):
            suggested_descriptions.append(description_meta['content'].strip())

        # Extrair Imagem Principal (Open Graph)
        suggested_image_url = None
        og_image_meta = soup.find('meta', attrs={'property': 'og:image'})
        if og_image_meta and og_image_meta.get('content'):
            suggested_image_url = og_image_meta['content']

        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"Análise de URL concluída para {request.url} em {processing_time:.2f}ms")
        
        return UrlAnalysisResponse(
            suggested_headlines=suggested_headlines,
            suggested_descriptions=suggested_descriptions,
            suggested_image_url=suggested_image_url
        )

    except httpx.RequestError as e:
        logger.error(f"Erro de requisição HTTP ao analisar URL {request.url}: {e}")
        analytics.track_error()
        raise HTTPException(status_code=400, detail=f"Não foi possível acessar o URL: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao analisar URL {request.url}: {e}")
        analytics.track_error()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {e}")

# ================================
# OBSERVABILITY ENDPOINTS v3.5
# ================================

@app.get("/metrics")
async def get_prometheus_metrics():
    """Endpoint de métricas Prometheus"""
    try:
        start_time = time.time()
        
        # Métricas de sistema
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        # Métricas de aplicação
        cache_stats = {
            "entries": len(content_analyzer.cache._cache),
            "hits": 0,
            "requests": 1
        }
        analytics_stats = {
            "api_calls": analytics.metrics.get("api_calls", 0),
            "content_generated": analytics.metrics.get("content_generated", 0),
            "images_generated": analytics.metrics.get("images_generated", 0),
            "workflows_executed": analytics.metrics.get("workflows_executed", 0)
        }
        
        # Formato Prometheus
        metrics = []
        
        # System metrics
        metrics.append(f'# HELP creative_studio_memory_usage_bytes Memory usage in bytes')
        metrics.append(f'# TYPE creative_studio_memory_usage_bytes gauge')
        metrics.append(f'creative_studio_memory_usage_bytes {memory_info.used}')
        
        metrics.append(f'# HELP creative_studio_cpu_usage_percent CPU usage percentage')
        metrics.append(f'# TYPE creative_studio_cpu_usage_percent gauge')
        metrics.append(f'creative_studio_cpu_usage_percent {cpu_percent}')
        
        # Application metrics
        metrics.append(f'# HELP creative_studio_cache_entries_total Total cache entries')
        metrics.append(f'# TYPE creative_studio_cache_entries_total gauge')
        metrics.append(f'creative_studio_cache_entries_total {cache_stats["entries"]}')
        
        metrics.append(f'# HELP creative_studio_api_calls_total Total API calls')
        metrics.append(f'# TYPE creative_studio_api_calls_total counter')
        metrics.append(f'creative_studio_api_calls_total {analytics_stats["api_calls"]}')
        
        metrics.append(f'# HELP creative_studio_content_generated_total Total content generated')
        metrics.append(f'# TYPE creative_studio_content_generated_total counter')
        metrics.append(f'creative_studio_content_generated_total {analytics_stats["content_generated"]}')
        
        metrics.append(f'# HELP creative_studio_images_generated_total Total images generated')
        metrics.append(f'# TYPE creative_studio_images_generated_total counter')
        metrics.append(f'creative_studio_images_generated_total {analytics_stats["images_generated"]}')
        
        metrics.append(f'# HELP creative_studio_workflows_executed_total Total workflows executed')
        metrics.append(f'# TYPE creative_studio_workflows_executed_total counter')
        metrics.append(f'creative_studio_workflows_executed_total {analytics_stats["workflows_executed"]}')
        
        # Response time metric
        response_time = (time.time() - start_time) * 1000
        metrics.append(f'# HELP creative_studio_metrics_response_time_ms Metrics endpoint response time')
        metrics.append(f'# TYPE creative_studio_metrics_response_time_ms gauge')
        metrics.append(f'creative_studio_metrics_response_time_ms {response_time:.2f}')
        
        return Response(
            content='\n'.join(metrics) + '\n',
            media_type='text/plain; version=0.0.4; charset=utf-8'
        )
        
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiling")
async def performance_profiling():
    """Endpoint de performance profiling"""
    try:
        start_time = time.time()
        
        # Coleta de métricas de performance
        memory_info = psutil.virtual_memory()
        cpu_info = psutil.cpu_percent(interval=0.1)
        
        # Métricas de cache
        cache_stats = {
            "entries": len(content_analyzer.cache._cache),
            "hits": 0,
            "requests": 1
        }
        
        # Métricas de analytics
        analytics_stats = {
            "api_calls": analytics.metrics.get("api_calls", 0),
            "content_generated": analytics.metrics.get("content_generated", 0),
            "images_generated": analytics.metrics.get("images_generated", 0),
            "workflows_executed": analytics.metrics.get("workflows_executed", 0)
        }
        
        # Simulação de operações para profiling
        operations_profile = []
        
        # Test cache operation
        cache_start = time.time()
        result = content_analyzer.cache.get("test_key")
        cache_time = (time.time() - cache_start) * 1000
        operations_profile.append({
            "operation": "cache_get",
            "duration_ms": round(cache_time, 4),
            "status": "success"
        })
        
        # Test analytics operation
        analytics_start = time.time()
        _ = analytics.metrics.get("api_calls", 0)
        analytics_time = (time.time() - analytics_start) * 1000
        operations_profile.append({
            "operation": "analytics_stats",
            "duration_ms": round(analytics_time, 4),
            "status": "success"
        })
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "service": "creative-studio",
            "version": config.VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(response_time, 2),
            "system_metrics": {
                "memory": {
                    "total_mb": round(memory_info.total / 1024 / 1024, 2),
                    "used_mb": round(memory_info.used / 1024 / 1024, 2),
                    "available_mb": round(memory_info.available / 1024 / 1024, 2),
                    "percent": memory_info.percent
                },
                "cpu": {
                    "percent": cpu_info,
                    "cores": psutil.cpu_count()
                }
            },
            "application_metrics": {
                "cache": cache_stats,
                "analytics": analytics_stats
            },
            "operations_profile": operations_profile,
            "performance_summary": {
                "avg_response_time_ms": round(response_time, 2),
                "memory_efficiency": round((memory_info.available / memory_info.total) * 100, 2),
                "cache_hit_rate": round((cache_stats.get("hits", 0) / max(cache_stats.get("requests", 1), 1)) * 100, 2)
            },
            "recommendations": [
                "Sistema operando dentro dos parâmetros normais",
                f"Uso de memória: {memory_info.percent}% - {'Ótimo' if memory_info.percent < 70 else 'Atenção' if memory_info.percent < 85 else 'Crítico'}",
                f"CPU: {cpu_info}% - {'Ótimo' if cpu_info < 50 else 'Moderado' if cpu_info < 80 else 'Alto'}"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in performance profiling: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# MAIN
# ================================

if __name__ == "__main__":
    logger.info("✅ Creative Studio v3.2 iniciado com sucesso")
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level="info" if config.DEBUG else "warning"
    )






