# 🚀 APEX System v4.0 - Autonomous Traffic Agent

> **Sistema de Inteligência Artificial Autônoma para Tráfego Pago**
> Agente totalmente automatizado com capacidades de auto-cura, predição e orquestração inteligente.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green.svg)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0-red.svg)](https://redis.io/)
[![License](https://img.shields.io/badge/License-Private-yellow.svg)]()

---

## 📋 Índice

- [Sobre](#-sobre)
- [Arquitetura](#-arquitetura)
- [Funcionalidades](#-funcionalidades)
- [Início Rápido](#-início-rápido)
- [Documentação](#-documentação)
- [Desenvolvimento](#-desenvolvimento)
- [Monitoramento](#-monitoramento)

---

## 🎯 Sobre

O **APEX System** é uma plataforma de **microserviços avançada** projetada para criar um ecossistema de IA autônoma com capacidades de:

- 🔄 **Auto-Cura** (Self-Healing)
- 🔮 **Previsão Proativa** (Future Casting)
- 🎼 **Orquestração Inteligente**
- 📊 **Analytics em Tempo Real**
- 🛡️ **Sistema Imunológico Digital**

### 🌟 Diferenciais

✨ **100% Local** - Sem dependências de cloud proprietário
✨ **Modular** - Arquitetura limpa e testável
✨ **Observável** - Prometheus + Grafana integrados
✨ **Escalável** - Pronto para Kubernetes
✨ **Seguro** - Best practices de segurança aplicadas

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        APEX SYSTEM v4.0                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   API Gateway   │────│ Ecosystem       │                    │
│  │   (Port 8000)   │    │ Platform        │                    │
│  │                 │    │ (Port 8002)     │                    │
│  └─────────────────┘    └─────────────────┘                    │
│           │                       │                            │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐│
│  │ Creative Studio │    │ Future Casting  │    │ Immune       ││
│  │   (Port 8003)   │    │   (Port 8004)   │    │ System       ││
│  │                 │    │                 │    │ (Port 8005)  ││
│  └─────────────────┘    └─────────────────┘    └──────────────┘│
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────────┐               │
│  │ Proactive       │    │ RL Engine            │               │
│  │ Conversation    │    │ (Port 8008)          │               │
│  │ (Port 8006)     │    │                      │               │
│  └─────────────────┘    └──────────────────────┘               │
│                                                                 │
│  ┌──────────────┐   ┌──────────┐   ┌──────────┐               │
│  │   MongoDB    │   │  Redis   │   │Prometheus│               │
│  │   :27017     │   │  :6379   │   │  :9090   │               │
│  └──────────────┘   └──────────┘   └──────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

### Microserviços

| Serviço | Porta | Função |
|---------|-------|--------|
| **API Gateway** | 8000 | Roteamento inteligente, Auth, Rate Limiting |
| **Ecosystem Platform** | 8002 | Service Registry, Analytics Engine |
| **Creative Studio** | 8003 | Geração de conteúdo criativo |
| **Future Casting** | 8004 | Predições ML e ações preventivas |
| **Immune System** | 8005 | Auto-scaling e auto-cura |
| **Proactive Conversation** | 8006 | Orquestração autônoma |
| **RL Engine** | 8008 | Aprendizado por reforço |

---

## ⚡ Funcionalidades

### 🤖 IA Autônoma

- ✅ **Self-Healing** - Detecta e corrige falhas automaticamente
- ✅ **Predictive Scaling** - Antecipa picos de tráfego e escala preventivamente
- ✅ **Smart Orchestration** - Coordena ações entre serviços de forma inteligente
- ✅ **Anomaly Detection** - Identifica comportamentos anômalos

### 📊 Analytics

- ✅ **Real-time Metrics** - Métricas em tempo real de todos os serviços
- ✅ **Historical Trends** - Análise de tendências históricas
- ✅ **Performance Monitoring** - Monitoramento de performance
- ✅ **Audit Logs** - Logs de auditoria completos

### 🛡️ Resiliência

- ✅ **Circuit Breakers** - Proteção contra falhas em cascata
- ✅ **Retry Logic** - Retentativas com exponential backoff
- ✅ **Health Checks** - Probes para Kubernetes
- ✅ **Graceful Shutdown** - Desligamento seguro

---

## 🚀 Início Rápido

### Pré-requisitos

- Docker 20.10+
- Docker Compose 2.0+
- (Opcional) Python 3.11+ para desenvolvimento

### Instalação

```bash
# 1. Clone o repositório
git clone <repo-url>
cd Apex-System

# 2. Configure variáveis de ambiente
cp .env.example .env

# 3. (Opcional) Edite .env com suas configurações
nano .env

# 4. Inicie todo o sistema
docker-compose up -d

# 5. Verifique os logs
docker-compose logs -f

# 6. Aguarde todos os serviços iniciarem (2-3 minutos)
```

### Verificação

```bash
# Health checks
curl http://localhost:8002/health  # Ecosystem Platform
curl http://localhost:8000/health  # API Gateway

# Acesse as interfaces
open http://localhost:3000  # Grafana (admin/apex_admin)
open http://localhost:9090  # Prometheus
```

---

## 📚 Documentação

- [📖 Documentação Completa da Refatoração](./REFACTORING_COMPLETE.md)
- [🏗️ Arquitetura Detalhada](./docs/ARCHITECTURE.md) *(a criar)*
- [🔌 Documentação das APIs](./docs/API.md) *(a criar)*
- [🚢 Guia de Deploy](./docs/DEPLOYMENT.md) *(a criar)*
- [💻 Guia do Desenvolvedor](./docs/DEVELOPMENT.md) *(a criar)*

### API Documentation (Swagger)

Acesse a documentação interativa das APIs:

- API Gateway: http://localhost:8000/docs
- Ecosystem Platform: http://localhost:8002/docs
- Future Casting: http://localhost:8004/docs
- Immune System: http://localhost:8005/docs

---

## 💻 Desenvolvimento

### Setup Local

```bash
# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements/dev.txt

# Rode um serviço específico
cd src/services/ecosystem_platform
uvicorn main:app --reload --port 8002
```

### Estrutura do Projeto

```
apex-system/
├── src/
│   ├── common/           # Código compartilhado
│   ├── infrastructure/   # MongoDB, Redis, Config
│   └── services/         # Microserviços
├── docker/               # Dockerfiles
├── config/               # Configurações
├── requirements/         # Dependências Python
├── tests/                # Testes
└── docs/                 # Documentação
```

### Testes

```bash
# Rodar todos os testes
pytest

# Com cobertura
pytest --cov=src --cov-report=html

# Testes de um serviço específico
pytest tests/services/ecosystem_platform/
```

---

## 📊 Monitoramento

### Prometheus

Acesse: http://localhost:9090

**Queries úteis**:
```promql
# Taxa de requisições
rate(ecosystem_platform_requests_total[5m])

# Latência média
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Serviços saudáveis
ecosystem_platform_healthy_services
```

### Grafana

Acesse: http://localhost:3000

- **Usuário**: admin
- **Senha**: apex_admin

**Dashboards disponíveis**:
- APEX System Overview
- Service Health
- Performance Metrics
- Predictions & Actions

---

## 🔧 Comandos Úteis

```bash
# Iniciar sistema
docker-compose up -d

# Parar sistema
docker-compose down

# Rebuild de um serviço
docker-compose up -d --build ecosystem-platform

# Ver logs em tempo real
docker-compose logs -f ecosystem-platform

# Executar comando em container
docker-compose exec ecosystem-platform sh

# Limpar volumes (CUIDADO: apaga dados)
docker-compose down -v
```

---

## 🐛 Troubleshooting

### Problemas Comuns

**Erro: "Cannot connect to MongoDB"**
```bash
# Verifique se MongoDB está rodando
docker-compose ps mongodb

# Verifique logs
docker-compose logs mongodb
```

**Erro: "Port already in use"**
```bash
# Identifique processo usando a porta
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Pare o processo ou mude a porta no docker-compose.yml
```

**Serviço não inicia**
```bash
# Verifique dependências
docker-compose ps

# Rebuild do serviço
docker-compose up -d --build <service-name>

# Verifique logs detalhados
docker-compose logs --tail=100 <service-name>
```

---

## 🤝 Contribuição

Este é um projeto privado. Para contribuir:

1. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
2. Commit suas mudanças: `git commit -m 'Add nova funcionalidade'`
3. Push para a branch: `git push origin feature/nova-funcionalidade`
4. Abra um Pull Request

---

## 📝 Licença

Este projeto é **privado** e proprietário. Todos os direitos reservados.

---

## 👨‍💻 Autor

**Jones Diniz**

Desenvolvido com auxílio de:
- Gemini (Google)
- Manus AI
- Claude (Anthropic)

---

## 🙏 Agradecimentos

- FastAPI por um framework incrível
- MongoDB e Redis pela infraestrutura sólida
- Prometheus e Grafana pela observabilidade
- Docker pela conteinerização

---

## 📞 Suporte

Para questões ou suporte, consulte a [documentação completa](./REFACTORING_COMPLETE.md) ou os logs dos serviços.

---

<p align="center">
  <strong>APEX System v4.0</strong><br>
  Autonomous · Intelligent · Resilient
</p>
