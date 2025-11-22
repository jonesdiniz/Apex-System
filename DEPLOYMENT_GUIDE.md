# 🚀 DEPLOYMENT GUIDE - APEX System v4.0

Complete guide for deploying APEX System locally with Docker.

---

## 📋 PREREQUISITES

### **Required Software**
```bash
✅ Docker (v20.10+)
✅ Docker Compose (v2.0+)
✅ Python 3.11+ (for verification script)
✅ curl (for health checks)
```

### **Verify Prerequisites**
```bash
docker --version
docker-compose --version
python --version
```

---

## 🔍 STEP 1: VERIFY INSTALLATION

**Run the verification script BEFORE starting Docker:**

```bash
python verify_installation.py
```

This script checks:
- ✅ Python version (3.11+)
- ✅ Project structure
- ✅ Python dependencies
- ✅ Module imports (no syntax errors or circular dependencies)
- ✅ Infrastructure services (MongoDB, Redis)
- ✅ Docker configuration
- ✅ Service configurations

**Expected Output:**
```
============================================================
APEX SYSTEM - INSTALLATION VERIFICATION
============================================================

✓ Python Version
✓ Project Structure
✓ Python Dependencies
✓ Module Imports
⚠ Infrastructure Services (MongoDB not running - normal before docker-compose)
✓ Environment Files
✓ Docker Configuration
✓ API Gateway Config
✓ RL Engine Config

Results: 8/9 checks passed
```

> **Note**: It's normal for infrastructure to fail before starting Docker.

---

## 🐳 STEP 2: START INFRASTRUCTURE

**Start only MongoDB and Redis first:**

```bash
docker-compose up -d mongodb redis
```

**Wait for services to be healthy (30-40 seconds):**

```bash
docker-compose ps
```

**Verify health:**
```bash
# MongoDB
docker-compose exec mongodb mongosh --eval "db.runCommand('ping')"

# Redis
docker-compose exec redis redis-cli ping
```

---

## 🚀 STEP 3: START MICROSERVICES

**Start all services:**

```bash
docker-compose up -d
```

**Check logs to verify startup:**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway
docker-compose logs -f rl-engine
```

**Wait for all services to be healthy (1-2 minutes):**

```bash
watch -n 2 'docker-compose ps'
```

**Expected Status:**
```
NAME                    STATUS
apex-api-gateway        Up (healthy)
apex-rl-engine          Up (healthy)
apex-ecosystem-platform Up (healthy)
apex-mongodb            Up (healthy)
apex-redis              Up (healthy)
apex-prometheus         Up
apex-grafana            Up
```

---

## ✅ STEP 4: VERIFY DEPLOYMENT

### **Health Checks**

```bash
# API Gateway
curl http://localhost:8000/health

# RL Engine
curl http://localhost:8008/health

# Ecosystem Platform
curl http://localhost:8002/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "version": "4.0.0",
  "timestamp": "2025-11-22T14:30:00Z"
}
```

### **Test OAuth Endpoint**

```bash
# Should redirect to OAuth page (will fail with browser, but shows endpoint is working)
curl -I "http://localhost:8000/auth/google/authorize?user_id=test_user"
```

### **Test RL Engine**

```bash
# Get available actions
curl http://localhost:8008/api/v1/actions/available

# Get metrics
curl http://localhost:8008/api/v1/metrics
```

---

## 📊 STEP 5: ACCESS DASHBOARDS

### **Grafana (Metrics Visualization)**
```
URL: http://localhost:3000
Username: admin
Password: apex_admin
```

### **Prometheus (Metrics Database)**
```
URL: http://localhost:9090
```

### **MongoDB (Database)**
```
Host: localhost:27017
Username: apex_admin
Password: apex_password_change_in_production
Database: apex_system
```

**Connect with MongoDB Compass:**
```
mongodb://apex_admin:apex_password_change_in_production@localhost:27017/apex_system?authSource=admin
```

### **Redis (Cache & Event Bus)**
```
Host: localhost:6379
```

**Connect with Redis CLI:**
```bash
docker-compose exec redis redis-cli
```

---

## 🔧 TROUBLESHOOTING

### **Service Won't Start**

```bash
# Check logs
docker-compose logs service-name

# Restart specific service
docker-compose restart service-name

# Rebuild if code changed
docker-compose up -d --build service-name
```

### **Import Errors**

```bash
# Verify PYTHONPATH in container
docker-compose exec api-gateway env | grep PYTHONPATH
# Should show: PYTHONPATH=/app/src

# Check if src/ is mounted
docker-compose exec api-gateway ls -la /app/src/
```

### **MongoDB Connection Issues**

```bash
# Check if MongoDB is healthy
docker-compose ps mongodb

# Check MongoDB logs
docker-compose logs mongodb

# Restart MongoDB
docker-compose restart mongodb
```

### **Port Already in Use**

```bash
# Find process using port 8000
lsof -i :8000

# Kill process (macOS/Linux)
kill -9 <PID>

# Or change port in docker-compose.yml
```

### **Clean Start (Nuclear Option)**

```bash
# Stop all containers
docker-compose down

# Remove all volumes (DELETES DATA!)
docker-compose down -v

# Rebuild everything
docker-compose up -d --build
```

---

## 🔄 UPDATING CODE

**After making code changes:**

```bash
# Rebuild and restart affected service
docker-compose up -d --build api-gateway

# Or rebuild all services
docker-compose up -d --build
```

**For hot-reload development:**

```bash
# Run service locally instead of Docker
cd src/services/api_gateway
python presentation/main.py
```

---

## 📝 USEFUL COMMANDS

```bash
# View all running containers
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View logs (specific service, last 100 lines)
docker-compose logs --tail=100 api-gateway

# Stop all services
docker-compose stop

# Start all services
docker-compose start

# Restart specific service
docker-compose restart rl-engine

# Execute command in container
docker-compose exec api-gateway bash

# View resource usage
docker stats

# Clean up unused images
docker system prune -a

# View networks
docker network ls
```

---

## 🔐 SECURITY NOTES

### **For Production Deployment:**

1. **Change default passwords in docker-compose.yml:**
   - MongoDB password
   - Grafana password

2. **Set proper CORS origins:**
   ```python
   # In main.py files
   allow_origins=["https://your-frontend-domain.com"]
   ```

3. **Use environment variables for secrets:**
   ```bash
   # Create .env file
   MONGODB_PASSWORD=secure_password_here
   GRAFANA_PASSWORD=another_secure_password
   ```

4. **Enable TLS/SSL for MongoDB and Redis**

5. **Use Docker secrets for sensitive data**

---

## 📈 MONITORING

### **Check Service Health**

```bash
# Automated health check script
while true; do
  echo "=== Health Check ==="
  curl -s http://localhost:8000/health | jq .status
  curl -s http://localhost:8008/health | jq .status
  sleep 30
done
```

### **Monitor Logs**

```bash
# Follow logs from all services with timestamps
docker-compose logs -f --timestamps
```

### **Monitor Resources**

```bash
# Real-time resource usage
docker stats --no-stream

# Or continuous
docker stats
```

---

## 🎯 PRODUCTION CHECKLIST

Before deploying to production:

- [ ] Run `python verify_installation.py` successfully
- [ ] All health checks return "healthy"
- [ ] Changed default passwords
- [ ] Configured proper CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Configured backup strategy for MongoDB
- [ ] Set up log aggregation
- [ ] Configured monitoring alerts
- [ ] Load tested the system
- [ ] Reviewed and hardened security settings
- [ ] Documented environment variables
- [ ] Set up CI/CD pipeline

---

## 🆘 GETTING HELP

If you encounter issues:

1. **Check health endpoints first**
2. **Review service logs**: `docker-compose logs service-name`
3. **Verify environment variables**: `docker-compose config`
4. **Check MongoDB connectivity**: `docker-compose exec mongodb mongosh`
5. **Check Redis connectivity**: `docker-compose exec redis redis-cli ping`
6. **Review PYTHONPATH**: `docker-compose exec service-name env`

---

**Last Updated**: 2025-11-22
**Version**: 4.0.0
**Status**: ✅ Production Ready
