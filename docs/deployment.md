# Deployment Guide

## 1. Deployment Overview

The **Autonomous Economic Intelligence & Opportunity Engine** can be deployed in three primary topologies:
1. **Local Workstation / Developer Daemon:** Run natively via Python virtual environment on `127.0.0.1:8000`.
2. **Private Container / Single-Host Docker:** Containerized service running behind a reverse proxy (e.g., Caddy, NGINX).
3. **Enterprise VPC / Multi-Agent Cluster:** Decoupled deployment with dedicated egress proxies, out-of-process Open Policy Agent (OPA), and managed PostgreSQL/pgvector storage.

---

## 2. Docker Deployment

### 2.1 Minimal Dockerfile (Reference)
```dockerfile
FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifests
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY datasets/ ./datasets/
COPY .env.example .

# Expose internal API port
EXPOSE 8000

# Run unprivileged
USER 10001:10001

CMD ["python", "-m", "uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.2 Docker Compose Example
```yaml
version: "3.8"

services:
  engine:
    build: .
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - ENVIRONMENT=production
      - HOST=0.0.0.0
      - PORT=8000
      - DEFAULT_PROVIDER=omniroute
      - OMNIROUTE_BASE_URL=http://omniroute:20128
      - DATABASE_URL=sqlite:////app/data/intelligence_ledger.db
    volumes:
      - engine-data:/app/data
    restart: unless-stopped

volumes:
  engine-data:
```

---

## 3. Reverse Proxy & TLS Configuration

Never expose FastAPI directly to the public Internet without TLS termination and rate limiting.

### NGINX Reverse Proxy Snippet
```nginx
server {
    listen 443 ssl http2;
    server_name intelligence.example.com;

    ssl_certificate /etc/letsencrypt/live/intelligence.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/intelligence.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 4. Production Health Checks & Monitoring

* **Liveness Probe:**
  * Endpoint: `GET /api/status`
  * Expected Status Code: `200 OK`
  * Expected Response: `{"status": "healthy", ...}`
* **Metrics & Diagnostics:**
  * Endpoint: `GET /api/system-diagnostics`
  * Provides detailed ledger metrics, claim counts, provider latency, and memory utilization.

---

## 5. Security & Isolation Checklist

Prior to public or VPC deployment:
- [ ] Ensure `.env` is NOT packaged inside Docker images.
- [ ] Supply API credentials via orchestrator secrets (Kubernetes Secrets / ECS Parameter Store).
- [ ] Configure egress proxy allowlists to prevent rogue outbound connections.
- [ ] Mount database volumes with strict filesystem permissions (`chmod 600`).
- [ ] Confirm no administrative endpoints (`debug`, `eval`, or local proxy admins) are publicly reachable.
