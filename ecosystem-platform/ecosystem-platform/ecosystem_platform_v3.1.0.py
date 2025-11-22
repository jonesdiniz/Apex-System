#!/usr/bin/env python3
"""
🛡️ ECOSYSTEM PLATFORM v3.1 - ULTRA-ROBUSTA
Versão com correções de estabilidade + Analytics Engine
100% Google Cloud Run Ready - Configurações conservadoras
"""

import asyncio
import json
import logging
import os
import time
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import httpx
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# ============================================================================
# CONFIGURAÇÃO ULTRA-ROBUSTA (GOOGLE CLOUD RUN READY)
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ecosystem-platform")

# Environment Variables (Cloud Run Ready)
PORT = int(os.getenv("PORT", "8002"))
HOST = os.getenv("HOST", "0.0.0.0")

# CONFIGURAÇÕES ULTRA-CONSERVADORAS PARA ESTABILIDADE
DISCOVERY_INTERVAL = int(os.getenv("DISCOVERY_INTERVAL", "300"))  # 5 minutos (vs 30s)
HEALTH_CHECK_TIMEOUT = int(os.getenv("HEALTH_CHECK_TIMEOUT", "30"))  # 30s (vs 5s)
MAX_CONCURRENT_CHECKS = int(os.getenv("MAX_CONCURRENT_CHECKS", "3"))  # Limite conexões

# Analytics Configuration (Ultra-Conservadora)
ANALYTICS_WINDOW_SIZE = int(os.getenv("ANALYTICS_WINDOW_SIZE", "7200"))  # 2 horas
ANALYTICS_RETENTION = int(os.getenv("ANALYTICS_RETENTION", "43200"))    # 12 horas (vs 24h)
ANALYTICS_REFRESH_INTERVAL = int(os.getenv("ANALYTICS_REFRESH_INTERVAL", "600"))  # 10 min (vs 1min)

# Memory Management (Prevenção de leaks)
MAX_SERVICE_METRICS = int(os.getenv("MAX_SERVICE_METRICS", "100"))  # Limite por serviço
MAX_ECOSYSTEM_TRENDS = int(os.getenv("MAX_ECOSYSTEM_TRENDS", "144"))  # 12h de dados (5min cada)
MEMORY_CLEANUP_INTERVAL = int(os.getenv("MEMORY_CLEANUP_INTERVAL", "1800"))  # 30 min

TARGET_SERVICE_URLS = os.getenv("TARGET_SERVICE_URLS", "").split('#')

# ============================================================================
# MODELOS DE DADOS
# ============================================================================

class ServiceInfo(BaseModel):
    name: str
    version: str
    port: int
    url: str
    status: str
    last_check: str
    response_time_ms: float

class CoordinationRequest(BaseModel):
    action: str
    services: List[str]
    parameters: Dict[str, Any] = {}

class ServiceMetrics(BaseModel):
    service_name: str
    port: int
    total_checks: int
    successful_checks: int
    failed_checks: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    uptime_percentage: float
    last_seen: str

class EcosystemTrends(BaseModel):
    timestamp: str
    total_services: int
    healthy_services: int
    avg_ecosystem_response_time: float
    ecosystem_health_score: float

# ============================================================================
# ANALYTICS ENGINE ULTRA-ROBUSTA (STATELESS + MEMORY SAFE)
# ============================================================================

class UltraRobustaAnalyticsEngine:
    """
    Analytics Engine Ultra-Robusta:
    - 100% Cloud Run Ready
    - Memory leak prevention
    - Conservative resource usage
    - Automatic cleanup
    - Error recovery
    """
    
    def __init__(self):
        # Sliding windows com limites rígidos (prevenção de memory leak)
        self.service_metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=MAX_SERVICE_METRICS)
        )
        self.ecosystem_trends: deque = deque(maxlen=MAX_ECOSYSTEM_TRENDS)
        
        # Controle de recursos
        self.current_window_start = time.time()
        self.last_analytics_refresh = time.time()
        self.last_memory_cleanup = time.time()
        self.error_count = 0
        
        logger.info("🛡️ Analytics Engine Ultra-Robusta iniciado (memory-safe)")
    
    def _cleanup_memory(self):
        """Limpeza automática de memória (prevenção de leaks)"""
        try:
            current_time = time.time()
            cutoff_time = current_time - ANALYTICS_RETENTION
            
            # Limpar métricas antigas de serviços
            for service_name in list(self.service_metrics.keys()):
                metrics = self.service_metrics[service_name]
                
                # Remover dados antigos
                while metrics and metrics[0]['timestamp'] < cutoff_time:
                    metrics.popleft()
                
                # Remover serviços sem dados
                if not metrics:
                    del self.service_metrics[service_name]
            
            # Limpar trends antigos
            while (self.ecosystem_trends and 
                   self.ecosystem_trends[0]['timestamp'] < cutoff_time):
                self.ecosystem_trends.popleft()
            
            # Forçar garbage collection
            gc.collect()
            
            self.last_memory_cleanup = current_time
            logger.info(f"🧹 Memory cleanup: {len(self.service_metrics)} serviços, {len(self.ecosystem_trends)} trends")
            
        except Exception as e:
            logger.error(f"Erro no memory cleanup: {e}")
            self.error_count += 1
    
    def record_service_check(self, service_name: str, port: int, response_time: float, success: bool):
        """Registra check de serviço com proteção contra memory leak"""
        try:
            timestamp = time.time()
            
            # Verificar se precisa fazer cleanup
            if timestamp - self.last_memory_cleanup > MEMORY_CLEANUP_INTERVAL:
                self._cleanup_memory()
            
            metric_data = {
                'timestamp': timestamp,
                'response_time': response_time,
                'success': success,
                'port': port
            }
            
            # Adicionar com limite automático (deque maxlen)
            self.service_metrics[service_name].append(metric_data)
            
        except Exception as e:
            logger.error(f"Erro ao registrar service check: {e}")
            self.error_count += 1
    
    def record_ecosystem_snapshot(self, total_services: int, healthy_services: int, avg_response_time: float):
        """Registra snapshot do ecossistema com proteção"""
        try:
            timestamp = time.time()
            
            health_score = (healthy_services / total_services * 100) if total_services > 0 else 0
            
            trend_data = {
                'timestamp': timestamp,
                'total_services': total_services,
                'healthy_services': healthy_services,
                'avg_response_time': avg_response_time,
                'health_score': health_score
            }
            
            # Adicionar com limite automático
            self.ecosystem_trends.append(trend_data)
            
        except Exception as e:
            logger.error(f"Erro ao registrar ecosystem snapshot: {e}")
            self.error_count += 1
    
    def get_service_analytics(self, service_name: str) -> Optional[ServiceMetrics]:
        """Calcula métricas de um serviço com error handling"""
        try:
            if service_name not in self.service_metrics:
                return None
            
            metrics = list(self.service_metrics[service_name])
            if not metrics:
                return None
            
            # Calcular métricas com proteção
            total_checks = len(metrics)
            successful_checks = sum(1 for m in metrics if m.get('success', False))
            failed_checks = total_checks - successful_checks
            
            response_times = [m['response_time'] for m in metrics if m.get('success', False) and m.get('response_time', 0) > 0]
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)
            else:
                avg_response_time = min_response_time = max_response_time = 0
            
            uptime_percentage = (successful_checks / total_checks * 100) if total_checks > 0 else 0
            
            return ServiceMetrics(
                service_name=service_name,
                port=metrics[-1].get('port', 0),
                total_checks=total_checks,
                successful_checks=successful_checks,
                failed_checks=failed_checks,
                avg_response_time=round(avg_response_time, 2),
                min_response_time=round(min_response_time, 2),
                max_response_time=round(max_response_time, 2),
                uptime_percentage=round(uptime_percentage, 2),
                last_seen=datetime.fromtimestamp(metrics[-1]['timestamp']).isoformat()
            )
            
        except Exception as e:
            logger.error(f"Erro ao calcular analytics para {service_name}: {e}")
            self.error_count += 1
            return None
    
    def get_ecosystem_trends(self, hours: int = 12) -> List[EcosystemTrends]:
        """Retorna tendências com limite de horas"""
        try:
            # Limitar horas para evitar sobrecarga
            hours = min(hours, 24)
            cutoff_time = time.time() - (hours * 3600)
            
            trends = []
            for t in self.ecosystem_trends:
                if t.get('timestamp', 0) >= cutoff_time:
                    try:
                        trend = EcosystemTrends(
                            timestamp=datetime.fromtimestamp(t['timestamp']).isoformat(),
                            total_services=t.get('total_services', 0),
                            healthy_services=t.get('healthy_services', 0),
                            avg_ecosystem_response_time=round(t.get('avg_response_time', 0), 2),
                            ecosystem_health_score=round(t.get('health_score', 0), 2)
                        )
                        trends.append(trend)
                    except Exception as e:
                        logger.debug(f"Erro ao processar trend: {e}")
                        continue
            
            return trends
            
        except Exception as e:
            logger.error(f"Erro ao obter ecosystem trends: {e}")
            self.error_count += 1
            return []
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Resumo de performance com error handling robusto"""
        try:
            if not self.ecosystem_trends:
                return {
                    "status": "no_data",
                    "message": "Dados insuficientes para análise",
                    "error_count": self.error_count
                }
            
            # Usar dados mais recentes (última hora)
            recent_count = min(12, len(self.ecosystem_trends))  # Máximo 12 pontos
            recent_trends = list(self.ecosystem_trends)[-recent_count:]
            
            if not recent_trends:
                return {"status": "no_data", "error_count": self.error_count}
            
            # Calcular métricas com proteção
            valid_trends = [t for t in recent_trends if t.get('health_score') is not None]
            
            if not valid_trends:
                return {"status": "no_data", "error_count": self.error_count}
            
            avg_health_score = sum(t['health_score'] for t in valid_trends) / len(valid_trends)
            avg_response_time = sum(t.get('avg_response_time', 0) for t in valid_trends) / len(valid_trends)
            
            current_data = recent_trends[-1]
            
            return {
                "ecosystem_health": {
                    "current_score": round(current_data.get('health_score', 0), 2),
                    "avg_score_recent": round(avg_health_score, 2),
                    "status": "excellent" if avg_health_score >= 95 else "good" if avg_health_score >= 80 else "degraded"
                },
                "performance": {
                    "avg_response_time_recent": round(avg_response_time, 2),
                    "current_services": current_data.get('total_services', 0),
                    "healthy_services": current_data.get('healthy_services', 0)
                },
                "system_health": {
                    "error_count": self.error_count,
                    "data_points": len(recent_trends),
                    "memory_usage": f"{len(self.service_metrics)} services tracked"
                },
                "last_update": datetime.fromtimestamp(current_data['timestamp']).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar performance summary: {e}")
            self.error_count += 1
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}",
                "error_count": self.error_count
            }

# ============================================================================
# ESTADO GLOBAL ULTRA-ROBUSTA
# ============================================================================

class UltraRobustaEcosystemState:
    def __init__(self):
        self.discovered_services: Dict[str, ServiceInfo] = {}
        self.total_requests = 0
        self.total_coordinations = 0
        self.start_time = time.time()
        self.last_discovery = None
        self.error_count = 0
        
        # Analytics Engine ultra-robusta
        self.analytics = UltraRobustaAnalyticsEngine()
        
    def get_uptime(self) -> float:
        return time.time() - self.start_time

ecosystem_state = UltraRobustaEcosystemState()

# ============================================================================
# FASTAPI APP ULTRA-ROBUSTA
# ============================================================================

app = FastAPI(
    title="Ecosystem Platform v3.1 Ultra-Robusta",
    description="Orquestrador com Analytics Engine - Configurações Ultra-Conservadoras",
    version="3.1.0"
)

# ============================================================================
# SERVICE DISCOVERY ULTRA-ROBUSTA
# ============================================================================

async def discover_service_robust(base_url: str) -> Optional[ServiceInfo]:
    """Descobre serviço com máxima robustez e error handling via URL"""
    if not base_url:
        return None

    try:
        # Extrai a porta da URL para preencher o modelo de dados
        parsed_url = urlparse(base_url)
        port = parsed_url.port or (80 if parsed_url.scheme == 'http' else 443)

        # Configuração ultra-conservadora do cliente
        timeout_config = httpx.Timeout(
            connect=HEALTH_CHECK_TIMEOUT,
            read=HEALTH_CHECK_TIMEOUT,
            write=HEALTH_CHECK_TIMEOUT,
            pool=HEALTH_CHECK_TIMEOUT
        )

        async with httpx.AsyncClient(
            timeout=timeout_config,
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=0)
        ) as client:
            start_time = time.time()

            try:
                # Usa a URL base diretamente para o health check
                response = await client.get(f"{base_url}/health")
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    try:
                        data = response.json()
                    except:
                        data = {}

                    service_info = ServiceInfo(
                        name=data.get("service", f"service-{port}"),
                        version=data.get("version", "unknown"),
                        port=port,
                        url=base_url,
                        status="healthy",
                        last_check=datetime.now().isoformat(),
                        response_time_ms=round(response_time, 2)
                    )

                    ecosystem_state.analytics.record_service_check(
                        service_info.name, port, response_time, True
                    )

                    logger.debug(f"🔍 Descoberto: {service_info.name} v{service_info.version} na porta {port}")
                    return service_info

            except (httpx.RequestError, httpx.TimeoutException, Exception) as e:
                logger.debug(f"Health check falhou para url {base_url}: {e}")

                ecosystem_state.analytics.record_service_check(
                    f"service-{port}", port, 0, False
                )

    except Exception as e:
        logger.debug(f"Erro geral na descoberta da url {base_url}: {e}")
        ecosystem_state.error_count += 1

    return None

async def run_service_discovery_robust():
    """Executa descoberta com controle de concorrência"""
    logger.info("🔍 Iniciando descoberta ultra-robusta...")
    
    try:
        discovered_count = 0
        total_response_time = 0
        healthy_count = 0
        
        # Processar em lotes pequenos para evitar sobrecarga
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHECKS)
        
        async def discover_with_semaphore(port):
            async with semaphore:
                return await discover_service_robust(port)
        
        # Executar descoberta com limite de concorrência
        tasks = [discover_with_semaphore(url) for url in TARGET_SERVICE_URLS if url]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.debug(f"Erro na descoberta da porta {KNOWN_PORTS[i]}: {result}")
                ecosystem_state.error_count += 1
                continue
                
            if result:
                service_key = f"{result.name}-{result.port}"
                ecosystem_state.discovered_services[service_key] = result
                discovered_count += 1
                
                if result.status == "healthy":
                    healthy_count += 1
                    total_response_time += result.response_time_ms
        
        ecosystem_state.last_discovery = datetime.now().isoformat()
        
        # Registrar snapshot com proteção
        avg_response_time = (total_response_time / healthy_count) if healthy_count > 0 else 0
        ecosystem_state.analytics.record_ecosystem_snapshot(
            discovered_count, healthy_count, avg_response_time
        )
        
        logger.info(f"🎯 Descoberta concluída: {discovered_count} serviços, {healthy_count} saudáveis")
        
        return discovered_count
        
    except Exception as e:
        logger.error(f"Erro na descoberta robusta: {e}")
        ecosystem_state.error_count += 1
        return 0

async def periodic_discovery_robust():
    """Task em background ultra-conservadora"""
    while True:
        try:
            await run_service_discovery_robust()
            
            # Intervalo ultra-conservador (5 minutos)
            await asyncio.sleep(DISCOVERY_INTERVAL)
            
        except Exception as e:
            logger.error(f"Erro na descoberta periódica: {e}")
            ecosystem_state.error_count += 1
            
            # Em caso de erro, aguardar mais tempo
            await asyncio.sleep(DISCOVERY_INTERVAL * 2)

# ============================================================================
# ENDPOINTS ORIGINAIS (COMPATIBILIDADE TOTAL)
# ============================================================================

@app.get("/")
async def root():
    """Informações gerais ultra-robustas"""
    try:
        ecosystem_state.total_requests += 1
        
        return {
            "service": "ecosystem-platform",
            "version": "3.1.0",
            "description": "Orquestrador Ultra-Robusta com Analytics Engine",
            "uptime_seconds": round(ecosystem_state.get_uptime(), 2),
            "discovered_services": len(ecosystem_state.discovered_services),
            "total_requests": ecosystem_state.total_requests,
            "last_discovery": ecosystem_state.last_discovery,
            "stability": {
                "error_count": ecosystem_state.error_count,
                "analytics_errors": ecosystem_state.analytics.error_count,
                "configuration": "ultra-conservative"
            },
            "features": [
                "Service Discovery Ultra-Robusta",
                "Health Monitoring Conservador",
                "Analytics Engine Memory-Safe",
                "Error Recovery Automático",
                "Google Cloud Run Ready"
            ]
        }
    except Exception as e:
        logger.error(f"Erro no endpoint root: {e}")
        ecosystem_state.error_count += 1
        return {"error": "Internal server error", "status": "degraded"}

@app.get("/health")
async def health():
    """Health check ultra-robusta"""
    try:
        ecosystem_state.total_requests += 1
        
        return {
            "status": "healthy",
            "service": "ecosystem-platform",
            "version": "3.1.0",
            "uptime_seconds": round(ecosystem_state.get_uptime(), 2),
            "discovered_services": len(ecosystem_state.discovered_services),
            "analytics_enabled": True,
            "stability": {
                "error_count": ecosystem_state.error_count,
                "configuration": "ultra-robust"
            }
        }
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        ecosystem_state.error_count += 1
        return {"status": "degraded", "error": str(e)}

@app.post("/api/v1/coordinate")
async def coordinate_services(request: CoordinationRequest):
    """Coordenação ultra-robusta"""
    try:
        ecosystem_state.total_requests += 1
        ecosystem_state.total_coordinations += 1
        
        coordination_id = f"coord_{int(time.time())}_{ecosystem_state.total_coordinations}"
        
        logger.info(f"🎯 Coordenação {coordination_id}: {request.action} para {request.services}")
        
        return {"status": "coordinated", "coordination_id": coordination_id}
        
    except Exception as e:
        logger.error(f"Erro na coordenação: {e}")
        ecosystem_state.error_count += 1
        return {"status": "error", "error": str(e)}

@app.get("/api/v1/services")
async def get_discovered_services():
    """Lista serviços com error handling"""
    try:
        ecosystem_state.total_requests += 1
        
        services_list = []
        healthy_count = 0
        
        for service in ecosystem_state.discovered_services.values():
            try:
                services_list.append(service.dict())
                if service.status == "healthy":
                    healthy_count += 1
            except Exception as e:
                logger.debug(f"Erro ao processar serviço: {e}")
                continue
        
        return {
            "total_services": len(services_list),
            "healthy_services": healthy_count,
            "last_discovery": ecosystem_state.last_discovery,
            "services": services_list,
            "error_count": ecosystem_state.error_count
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar serviços: {e}")
        ecosystem_state.error_count += 1
        return {"error": str(e), "services": []}

@app.post("/api/v1/services/discover")
async def trigger_discovery():
    """Força descoberta com proteção"""
    try:
        ecosystem_state.total_requests += 1
        
        discovered_count = await run_service_discovery_robust()
        
        return {
            "status": "completed",
            "discovered_services": discovered_count,
            "timestamp": datetime.now().isoformat(),
            "error_count": ecosystem_state.error_count
        }
        
    except Exception as e:
        logger.error(f"Erro ao forçar descoberta: {e}")
        ecosystem_state.error_count += 1
        return {"status": "error", "error": str(e)}

@app.get("/api/v1/health/ecosystem")
async def ecosystem_health():
    """Saúde do ecossistema ultra-robusta"""
    try:
        ecosystem_state.total_requests += 1
        
        total_services = len(ecosystem_state.discovered_services)
        healthy_services = sum(1 for s in ecosystem_state.discovered_services.values() if s.status == "healthy")
        
        overall_status = "healthy" if healthy_services == total_services and total_services > 0 else "degraded"
        
        return {
            "ecosystem_health": {
                "overall_status": overall_status,
                "total_services": total_services,
                "healthy_services": healthy_services
            },
            "services": [s.dict() for s in ecosystem_state.discovered_services.values()],
            "last_check": datetime.now().isoformat(),
            "stability": {
                "error_count": ecosystem_state.error_count,
                "analytics_errors": ecosystem_state.analytics.error_count
            }
        }
        
    except Exception as e:
        logger.error(f"Erro no ecosystem health: {e}")
        ecosystem_state.error_count += 1
        return {"error": str(e), "status": "error"}

# ============================================================================
# ENDPOINTS ANALYTICS ULTRA-ROBUSTOS
# ============================================================================

@app.get("/api/v1/analytics/services")
async def get_services_analytics():
    """Analytics por serviço ultra-robusta"""
    try:
        ecosystem_state.total_requests += 1
        
        analytics_data = []
        
        for service_name in list(ecosystem_state.analytics.service_metrics.keys()):
            try:
                metrics = ecosystem_state.analytics.get_service_analytics(service_name)
                if metrics:
                    analytics_data.append(metrics.dict())
            except Exception as e:
                logger.debug(f"Erro ao processar analytics de {service_name}: {e}")
                continue
        
        return {
            "total_services_analyzed": len(analytics_data),
            "analytics_window_hours": ANALYTICS_WINDOW_SIZE / 3600,
            "services": analytics_data,
            "generated_at": datetime.now().isoformat(),
            "error_count": ecosystem_state.analytics.error_count
        }
        
    except Exception as e:
        logger.error(f"Erro no services analytics: {e}")
        ecosystem_state.error_count += 1
        return {"error": str(e), "services": []}

@app.get("/api/v1/analytics/trends")
async def get_ecosystem_trends(hours: int = 12):
    """Tendências ultra-robustas"""
    try:
        ecosystem_state.total_requests += 1
        
        # Limitar horas para evitar sobrecarga
        hours = min(max(hours, 1), 24)
        
        trends = ecosystem_state.analytics.get_ecosystem_trends(hours)
        
        return {
            "time_window_hours": hours,
            "data_points": len(trends),
            "trends": [trend.dict() for trend in trends],
            "generated_at": datetime.now().isoformat(),
            "error_count": ecosystem_state.analytics.error_count
        }
        
    except Exception as e:
        logger.error(f"Erro no trends analytics: {e}")
        ecosystem_state.error_count += 1
        return {"error": str(e), "trends": []}

@app.get("/api/v1/analytics/performance")
async def get_performance_analytics():
    """Performance analytics ultra-robusta"""
    try:
        ecosystem_state.total_requests += 1
        
        summary = ecosystem_state.analytics.get_performance_summary()
        
        return {
            "performance_summary": summary,
            "configuration": {
                "analytics_window_size": ANALYTICS_WINDOW_SIZE,
                "analytics_retention": ANALYTICS_RETENTION,
                "refresh_interval": ANALYTICS_REFRESH_INTERVAL,
                "discovery_interval": DISCOVERY_INTERVAL,
                "health_check_timeout": HEALTH_CHECK_TIMEOUT,
                "max_concurrent_checks": MAX_CONCURRENT_CHECKS
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro no performance analytics: {e}")
        ecosystem_state.error_count += 1
        return {"error": str(e), "status": "error"}

@app.get("/api/v1/analytics/summary")
async def get_analytics_summary():
    """Resumo executivo ultra-robusta"""
    try:
        ecosystem_state.total_requests += 1
        
        # Estatísticas com proteção
        total_services_tracked = len(ecosystem_state.analytics.service_metrics)
        total_data_points = sum(len(deque_data) for deque_data in ecosystem_state.analytics.service_metrics.values())
        ecosystem_data_points = len(ecosystem_state.analytics.ecosystem_trends)
        
        performance = ecosystem_state.analytics.get_performance_summary()
        
        return {
            "analytics_overview": {
                "services_tracked": total_services_tracked,
                "total_data_points": total_data_points,
                "ecosystem_data_points": ecosystem_data_points,
                "analytics_uptime": round(ecosystem_state.get_uptime(), 2)
            },
            "current_performance": performance,
            "stability": {
                "system_errors": ecosystem_state.error_count,
                "analytics_errors": ecosystem_state.analytics.error_count,
                "configuration": "ultra-conservative"
            },
            "data_retention": {
                "window_size_hours": ANALYTICS_WINDOW_SIZE / 3600,
                "retention_hours": ANALYTICS_RETENTION / 3600,
                "refresh_interval_seconds": ANALYTICS_REFRESH_INTERVAL,
                "discovery_interval_seconds": DISCOVERY_INTERVAL
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro no analytics summary: {e}")
        ecosystem_state.error_count += 1
        return {"error": str(e), "status": "error"}

# ============================================================================
# MÉTRICAS PROMETHEUS ULTRA-ROBUSTAS
# ============================================================================

@app.get("/metrics")
async def prometheus_metrics():
    """Métricas Prometheus com error handling"""
    try:
        ecosystem_state.total_requests += 1
        
        total_services = len(ecosystem_state.discovered_services)
        healthy_services = sum(1 for s in ecosystem_state.discovered_services.values() if s.status == "healthy")
        
        # Métricas do Analytics com proteção
        services_tracked = len(ecosystem_state.analytics.service_metrics)
        total_data_points = sum(len(deque_data) for deque_data in ecosystem_state.analytics.service_metrics.values())
        
        metrics = f"""# HELP ecosystem_platform_requests_total Total requests
# TYPE ecosystem_platform_requests_total counter
ecosystem_platform_requests_total {ecosystem_state.total_requests}

# HELP ecosystem_platform_uptime_seconds Uptime in seconds
# TYPE ecosystem_platform_uptime_seconds gauge
ecosystem_platform_uptime_seconds {ecosystem_state.get_uptime():.2f}

# HELP ecosystem_platform_discovered_services Total discovered services
# TYPE ecosystem_platform_discovered_services gauge
ecosystem_platform_discovered_services {total_services}

# HELP ecosystem_platform_healthy_services Healthy services
# TYPE ecosystem_platform_healthy_services gauge
ecosystem_platform_healthy_services {healthy_services}

# HELP ecosystem_platform_coordinations_total Total coordinations
# TYPE ecosystem_platform_coordinations_total counter
ecosystem_platform_coordinations_total {ecosystem_state.total_coordinations}

# HELP ecosystem_platform_analytics_services_tracked Services tracked by analytics
# TYPE ecosystem_platform_analytics_services_tracked gauge
ecosystem_platform_analytics_services_tracked {services_tracked}

# HELP ecosystem_platform_analytics_data_points Total analytics data points
# TYPE ecosystem_platform_analytics_data_points gauge
ecosystem_platform_analytics_data_points {total_data_points}

# HELP ecosystem_platform_errors_total Total system errors
# TYPE ecosystem_platform_errors_total counter
ecosystem_platform_errors_total {ecosystem_state.error_count}

# HELP ecosystem_platform_analytics_errors_total Total analytics errors
# TYPE ecosystem_platform_analytics_errors_total counter
ecosystem_platform_analytics_errors_total {ecosystem_state.analytics.error_count}

# HELP ecosystem_platform_info Service information
# TYPE ecosystem_platform_info gauge
ecosystem_platform_info{{version="3.1.0",service="ecosystem-platform",port="{PORT}",analytics="enabled",stability="ultra-robust"}} 1

# HELP ecosystem_platform_status Service status
# TYPE ecosystem_platform_status gauge
ecosystem_platform_status 1
"""
        
        return JSONResponse(content=metrics, media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Erro nas métricas: {e}")
        ecosystem_state.error_count += 1
        return JSONResponse(content="# Error generating metrics", media_type="text/plain")

@app.get("/status")
async def detailed_status():
    """Status detalhado ultra-robusta"""
    try:
        ecosystem_state.total_requests += 1
        
        return {
            "orquestrador": {
                "status": "healthy",
                "version": "3.1.0",
                "uptime_seconds": round(ecosystem_state.get_uptime(), 2),
                "stability": "ultra-robust"
            },
            "service_discovery": {
                "enabled": True,
                "interval_seconds": DISCOVERY_INTERVAL,
                "timeout_seconds": HEALTH_CHECK_TIMEOUT,
                "max_concurrent": MAX_CONCURRENT_CHECKS,
                "last_discovery": ecosystem_state.last_discovery,
                "discovered_services": len(ecosystem_state.discovered_services)
            },
            "analytics_engine": {
                "enabled": True,
                "services_tracked": len(ecosystem_state.analytics.service_metrics),
                "data_retention_hours": ANALYTICS_RETENTION / 3600,
                "window_size_hours": ANALYTICS_WINDOW_SIZE / 3600,
                "refresh_interval_seconds": ANALYTICS_REFRESH_INTERVAL,
                "memory_cleanup_interval_seconds": MEMORY_CLEANUP_INTERVAL
            },
            "ecosystem": {
                "total_services": len(ecosystem_state.discovered_services),
                "overall_status": "operational"
            },
            "error_tracking": {
                "system_errors": ecosystem_state.error_count,
                "analytics_errors": ecosystem_state.analytics.error_count
            }
        }
        
    except Exception as e:
        logger.error(f"Erro no status: {e}")
        ecosystem_state.error_count += 1
        return {"error": str(e), "status": "error"}

# ============================================================================
# STARTUP E SHUTDOWN ULTRA-ROBUSTOS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicialização ultra-robusta"""
    try:
        logger.info("🛡️ Iniciando Ecosystem Platform v3.1 Ultra-Robusta")
        logger.info(f"📊 Configurações conservadoras: Discovery={DISCOVERY_INTERVAL}s, Timeout={HEALTH_CHECK_TIMEOUT}s")
        
        # Descoberta inicial com proteção
        try:
            await run_service_discovery_robust()
        except Exception as e:
            logger.error(f"Erro na descoberta inicial: {e}")
            ecosystem_state.error_count += 1
        
        # Background task ultra-conservadora
        asyncio.create_task(periodic_discovery_robust())
        
        logger.info("✅ Ecosystem Platform v3.1 Ultra-Robusta iniciado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro no startup: {e}")
        ecosystem_state.error_count += 1

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown graceful ultra-robusta"""
    try:
        logger.info("🛑 Parando Ecosystem Platform v3.1 Ultra-Robusta...")
        logger.info("📊 Analytics Engine: dados em memória serão perdidos (stateless design)")
        logger.info(f"📈 Estatísticas finais: {ecosystem_state.error_count} erros de sistema, {ecosystem_state.analytics.error_count} erros de analytics")
        logger.info("✅ Shutdown concluído com sucesso")
        
    except Exception as e:
        logger.error(f"Erro no shutdown: {e}")

# ============================================================================
# MAIN ULTRA-ROBUSTA
# ============================================================================

if __name__ == "__main__":
    logger.info(f"🛡️ Iniciando Ecosystem Platform v3.1 Ultra-Robusta na porta {PORT}")
    logger.info("📊 Analytics Engine: 100% Google Cloud Run Ready (stateless + memory-safe)")
    logger.info(f"⚙️ Configurações: Discovery={DISCOVERY_INTERVAL}s, Timeout={HEALTH_CHECK_TIMEOUT}s, Analytics={ANALYTICS_REFRESH_INTERVAL}s")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")

