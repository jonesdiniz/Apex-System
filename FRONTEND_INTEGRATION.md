# 🎨 FRONTEND INTEGRATION GUIDE

**APEX System v4.0** - Backend API Documentation for Frontend Developers

---

## 📡 BASE URLs

```
Production (Docker):
├── API Gateway:  http://localhost:8000
├── RL Engine:    http://localhost:8008
└── Ecosystem:    http://localhost:8002

Development (Local):
├── API Gateway:  http://localhost:8000
└── RL Engine:    http://localhost:8008
```

---

## 🔐 AUTHENTICATION - OAuth 2.0 Flow

### **Supported Platforms**
- Google (Ads + Analytics)
- LinkedIn (Ads)
- Meta/Facebook (Business)
- Twitter/X (API v2)
- TikTok (Creator)

### **OAuth Flow Endpoints**

#### **1. Initiate Authorization**
```http
GET /auth/{platform}/authorize?user_id={user_id}
```

**Parameters:**
- `platform`: google | linkedin | meta | twitter | tiktok
- `user_id`: Unique user identifier

**Response:**
- Redirects to platform's authorization page
- User authenticates on platform
- Platform redirects back to callback

**Example:**
```bash
curl "http://localhost:8000/auth/google/authorize?user_id=user_123"
# → Redirects to Google OAuth
```

---

#### **2. Callback (Handled Automatically)**
```http
GET /auth/{platform}/callback?code={code}&state={state}
```

**This endpoint is called by the OAuth provider after user approval.**

**Response:**
- Redirects to frontend with status: `http://localhost:3000/settings/credentials?platform={platform}&status=success`
- Token is stored in backend MongoDB

---

#### **3. Get Token**
```http
GET /auth/{platform}/token?user_id={user_id}
```

**Parameters:**
- `platform`: google | linkedin | meta | twitter | tiktok
- `user_id`: User identifier

**Response:**
```json
{
  "platform": "google",
  "access_token": "ya29.a0AfH6SMA...",
  "expires_at": "2025-11-22T15:30:00Z",
  "user_id": "user_123"
}
```

**Status Codes:**
- `200`: Token found and valid
- `404`: No token found
- `401`: Token expired (refresh needed)

**Example:**
```bash
curl "http://localhost:8000/auth/google/token?user_id=user_123"
```

---

#### **4. Refresh Token**
```http
POST /auth/{platform}/refresh?user_id={user_id}
```

**Response:**
```json
{
  "platform": "google",
  "access_token": "ya29.a0AfH6SMA...",
  "expires_at": "2025-11-22T16:30:00Z",
  "refreshed": true
}
```

---

#### **5. Revoke Token**
```http
DELETE /auth/{platform}/revoke?user_id={user_id}
```

**Response:**
```json
{
  "platform": "google",
  "user_id": "user_123",
  "revoked": true,
  "timestamp": "2025-11-22T14:30:00Z"
}
```

---

## 🧠 RL ENGINE - Campaign Optimization

### **Generate Optimal Action**

```http
POST /api/v1/actions/generate
Content-Type: application/json
```

**Request Body:**
```json
{
  "current_state": {
    "strategic_context": "MAXIMIZE_ROAS",
    "campaign_type": "conversion",
    "risk_appetite": "moderate",
    "competition": "moderate",
    "ctr": 2.5,
    "cpm": 10.0,
    "cpc": 0.5,
    "impressions": 10000,
    "clicks": 250,
    "conversions": 25,
    "spend": 125.0,
    "revenue": 300.0,
    "roas": 2.4,
    "budget_utilization": 0.8,
    "reach": 8000,
    "frequency": 1.25
  }
}
```

**Response:**
```json
{
  "action": "focus_high_value_audiences",
  "confidence": 0.85,
  "reasoning": "Exploitation: best action from 127 experiences",
  "context": {
    "strategic_context": "MAXIMIZE_ROAS",
    "normalized_context": "MAXIMIZE_ROAS",
    "campaign_type": "conversion"
  },
  "timestamp": "2025-11-22T14:30:00Z",
  "dual_buffer_status": {
    "active_buffer_size": 5,
    "history_size": 120,
    "total_strategies": 15
  }
}
```

**Available Actions:**
- `optimize_bidding_strategy`
- `increase_bid_conversion_keywords`
- `reduce_bid_conservative`
- `focus_high_value_audiences`
- `expand_reach_campaigns`
- `pause_campaign`
- `increase_budget_moderate`
- `reduce_budget_drastic`
- `optimize_for_ctr`
- `optimize_for_reach`
- `adjust_targeting_narrow`
- `adjust_targeting_broad`

---

### **Get Available Actions**

```http
GET /api/v1/actions/available
```

**Response:**
```json
{
  "actions": [
    {
      "action": "optimize_bidding_strategy",
      "description": "Optimize Bidding Strategy"
    },
    {
      "action": "focus_high_value_audiences",
      "description": "Focus High Value Audiences"
    }
    // ... 12 total actions
  ],
  "count": 12
}
```

---

### **Get Learning Metrics**

```http
GET /api/v1/metrics
```

**Response:**
```json
{
  "total_actions": 1523,
  "total_learning_sessions": 45,
  "total_experiences_processed": 682,
  "total_strategies": 28,
  "avg_confidence": 0.782,
  "avg_reward": 0.654,
  "avg_q_value": 0.723,
  "max_q_value": 0.956,
  "dual_buffer_metrics": {
    "active_buffer_size": 12,
    "active_buffer_max": 25,
    "active_buffer_utilization_percent": 48.0,
    "history_buffer_size": 645,
    "history_buffer_max": 1000,
    "history_buffer_utilization_percent": 64.5
  },
  "hyperparameters": {
    "learning_rate": 0.1,
    "discount_factor": 0.95,
    "exploration_rate": 0.15
  }
}
```

---

### **Get All Learned Strategies**

```http
GET /api/v1/strategies
```

**Response:**
```json
{
  "strategies": {
    "MAXIMIZE_ROAS": {
      "context": "MAXIMIZE_ROAS",
      "best_action": "focus_high_value_audiences",
      "best_q_value": 0.856,
      "total_experiences": 127,
      "actions_count": 5,
      "confidence": 0.85,
      "created_at": "2025-11-20T10:00:00Z",
      "last_updated": "2025-11-22T14:00:00Z"
    }
  },
  "count": 28,
  "timestamp": "2025-11-22T14:30:00Z"
}
```

---

## 🏥 HEALTH CHECKS

### **API Gateway Health**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "version": "4.0.0",
  "timestamp": "2025-11-22T14:30:00Z",
  "dependencies": {
    "mongodb": "connected",
    "redis": "connected",
    "event_bus": "connected"
  }
}
```

### **RL Engine Health**
```http
GET http://localhost:8008/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "rl-engine",
  "version": "4.0.0",
  "strategies": 28,
  "experiences": 12,
  "experience_history": 645,
  "timestamp": "2025-11-22T14:30:00Z"
}
```

---

## 🔄 REAL-TIME UPDATES (Event-Driven)

The RL Engine learns automatically from events. No need to manually call `/learn` endpoint!

### **How It Works:**
1. Traffic Manager publishes `traffic.request_completed` event
2. RL Engine receives event automatically
3. RL Engine calculates reward from metrics
4. RL Engine learns and updates strategies
5. Frontend can poll `/api/v1/metrics` for updated stats

### **Polling Recommendations:**

**Dashboard Metrics:**
```javascript
// Poll every 30 seconds for learning metrics
setInterval(async () => {
  const response = await fetch('http://localhost:8008/api/v1/metrics');
  const metrics = await response.json();
  updateDashboard(metrics);
}, 30000);
```

**Strategy Updates:**
```javascript
// Poll every 60 seconds for strategy updates
setInterval(async () => {
  const response = await fetch('http://localhost:8008/api/v1/strategies');
  const strategies = await response.json();
  updateStrategiesList(strategies);
}, 60000);
```

---

## 🎨 FRONTEND IMPLEMENTATION EXAMPLES

### **React - OAuth Flow**

```typescript
// OAuthButton.tsx
import React from 'react';

interface OAuthButtonProps {
  platform: 'google' | 'linkedin' | 'meta' | 'twitter' | 'tiktok';
  userId: string;
}

export const OAuthButton: React.FC<OAuthButtonProps> = ({ platform, userId }) => {
  const handleOAuth = () => {
    const authUrl = `http://localhost:8000/auth/${platform}/authorize?user_id=${userId}`;
    window.location.href = authUrl;
  };

  return (
    <button onClick={handleOAuth}>
      Connect {platform}
    </button>
  );
};
```

### **React - Get Action Recommendation**

```typescript
// ActionRecommendation.tsx
import React, { useState } from 'react';

interface CampaignState {
  strategic_context: string;
  campaign_type: string;
  ctr: number;
  roas: number;
  conversions: number;
  // ... other metrics
}

export const ActionRecommendation: React.FC = () => {
  const [action, setAction] = useState<any>(null);

  const getRecommendation = async (state: CampaignState) => {
    const response = await fetch('http://localhost:8008/api/v1/actions/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_state: state })
    });

    const result = await response.json();
    setAction(result);
  };

  return (
    <div>
      {action && (
        <div>
          <h3>Recommended Action: {action.action}</h3>
          <p>Confidence: {(action.confidence * 100).toFixed(1)}%</p>
          <p>Reasoning: {action.reasoning}</p>
        </div>
      )}
    </div>
  );
};
```

### **React - Learning Metrics Dashboard**

```typescript
// MetricsDashboard.tsx
import React, { useEffect, useState } from 'react';

export const MetricsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    // Initial fetch
    fetchMetrics();

    // Poll every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    const response = await fetch('http://localhost:8008/api/v1/metrics');
    const data = await response.json();
    setMetrics(data);
  };

  if (!metrics) return <div>Loading...</div>;

  return (
    <div className="metrics-dashboard">
      <h2>RL Engine Metrics</h2>
      <div>Total Actions: {metrics.total_actions}</div>
      <div>Total Strategies: {metrics.total_strategies}</div>
      <div>Avg Confidence: {(metrics.avg_confidence * 100).toFixed(1)}%</div>
      <div>Active Buffer: {metrics.dual_buffer_metrics.active_buffer_size}/{metrics.dual_buffer_metrics.active_buffer_max}</div>
    </div>
  );
};
```

---

## 🚨 ERROR HANDLING

### **HTTP Status Codes**

```
200: Success
201: Created
400: Bad Request (invalid parameters)
401: Unauthorized (token expired/invalid)
404: Not Found (resource doesn't exist)
500: Internal Server Error
503: Service Unavailable
```

### **Error Response Format**

```json
{
  "detail": "Error message",
  "error_code": "INVALID_STATE",
  "timestamp": "2025-11-22T14:30:00Z"
}
```

### **Example Error Handling**

```typescript
const handleRequest = async () => {
  try {
    const response = await fetch('http://localhost:8000/auth/google/token?user_id=user_123');

    if (!response.ok) {
      if (response.status === 404) {
        // No token found - redirect to OAuth
        window.location.href = 'http://localhost:8000/auth/google/authorize?user_id=user_123';
      } else if (response.status === 401) {
        // Token expired - refresh
        await fetch('http://localhost:8000/auth/google/refresh?user_id=user_123', {
          method: 'POST'
        });
      }
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Request failed:', error);
  }
};
```

---

## 📊 CORS Configuration

The backend is configured to accept requests from any origin in development:

```python
allow_origins=["*"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

**For production, update to specific frontend URL:**
```python
allow_origins=["https://your-frontend-domain.com"]
```

---

## 🔗 API Gateway Service Discovery

All services register with the API Gateway. Frontend should only communicate with:

**Primary Gateway:**
- `http://localhost:8000` - All OAuth endpoints

**RL Engine (Optional Direct Access):**
- `http://localhost:8008` - All Q-Learning endpoints

**Ecosystem Platform (Internal Only):**
- `http://localhost:8002` - Do NOT access directly from frontend

---

## 📝 CHANGELOG

**v4.0.0** (2025-11-22):
- ✅ OAuth 2.0 for 5 platforms
- ✅ Q-Learning algorithm
- ✅ Event-Driven Learning
- ✅ Dual Buffer
- ✅ Clean Architecture
- ✅ MongoDB persistence

---

## 🆘 TROUBLESHOOTING

### **"CORS error"**
- Ensure backend is running on `localhost:8000`
- Check browser console for exact error
- Verify `allow_origins` in backend config

### **"404 - Token not found"**
- User needs to complete OAuth flow first
- Redirect to `/auth/{platform}/authorize`

### **"503 - Service Unavailable"**
- Check if Docker containers are running: `docker-compose ps`
- Check health endpoint: `curl http://localhost:8000/health`

### **"Connection refused"**
- Ensure Docker services are up: `docker-compose up -d`
- Check MongoDB: `docker-compose ps mongodb`
- Check Redis: `docker-compose ps redis`

---

## 📞 SUPPORT

For integration questions or issues:
1. Check health endpoints first
2. Review error response messages
3. Check Docker logs: `docker-compose logs api-gateway`
4. Verify infrastructure: `docker-compose ps`

---

**Last Updated**: 2025-11-22
**API Version**: 4.0.0
**Backend Status**: ✅ Production Ready
