#!/bin/bash

# APEX System - Quick Start Script
# Inicialização rápida do sistema

set -e

echo "🚀 APEX System v4.0 - Quick Start"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker
echo -n "Checking Docker... "
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓${NC}"

# Check Docker Compose
echo -n "Checking Docker Compose... "
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓${NC}"

# Setup .env
echo -n "Setting up environment... "
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓${NC} (.env created)"
else
    echo -e "${YELLOW}⚠${NC} (.env already exists)"
fi

# Create logs directory
mkdir -p logs
chmod 777 logs

# Start infrastructure first
echo ""
echo "📦 Starting infrastructure services..."
docker-compose up -d mongodb redis prometheus grafana

# Wait for MongoDB
echo -n "Waiting for MongoDB... "
until docker-compose exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" &> /dev/null; do
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✓${NC}"

# Wait for Redis
echo -n "Waiting for Redis... "
until docker-compose exec -T redis redis-cli ping &> /dev/null; do
    echo -n "."
    sleep 1
done
echo -e " ${GREEN}✓${NC}"

# Start services
echo ""
echo "🚀 Starting microservices..."
echo -e "${YELLOW}Note: Some services may fail until they are fully refactored${NC}"
docker-compose up -d

# Show status
echo ""
echo "📊 Services Status:"
docker-compose ps

# Show URLs
echo ""
echo "🌐 Access Points:"
echo "=================================="
echo -e "API Gateway:         ${GREEN}http://localhost:8000${NC}"
echo -e "Ecosystem Platform:  ${GREEN}http://localhost:8002${NC}"
echo -e "Grafana:             ${GREEN}http://localhost:3000${NC} (admin/apex_admin)"
echo -e "Prometheus:          ${GREEN}http://localhost:9090${NC}"
echo ""
echo "📚 Documentation:"
echo -e "README:              ${GREEN}./README.md${NC}"
echo -e "Next Steps:          ${GREEN}./NEXT_STEPS.md${NC}"
echo -e "Full Refactoring:    ${GREEN}./REFACTORING_COMPLETE.md${NC}"
echo ""
echo "📋 Useful Commands:"
echo "  docker-compose logs -f         # View logs"
echo "  docker-compose ps              # Check status"
echo "  docker-compose down            # Stop all"
echo "  docker-compose restart <srv>   # Restart service"
echo ""
echo -e "${GREEN}✅ APEX System is starting!${NC}"
echo "Please wait 2-3 minutes for all services to be ready."
