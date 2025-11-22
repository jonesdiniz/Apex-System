#!/bin/sh
# APEX System - Health Check Script
# Used by Docker to check service health

SERVICE_PORT=${APEX_SERVICE_PORT:-8000}

curl -f http://localhost:${SERVICE_PORT}/health || exit 1
