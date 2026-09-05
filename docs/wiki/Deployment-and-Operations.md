# Deployment & Operations 🚀

Comprehensive deployment recipes, platform configurations, and operational best practices for **FallenWiki Crawler**.

---

## 1. Local Deployment

### Prerequisites
- Python 3.10+ (Python 3.11+ recommended)
- `pip` package manager

### A. One-Click Launchers
- **Windows**: Double-click `run.bat` or run in CMD:
  ```cmd
  run.bat
  ```
- **macOS / Linux**:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```

### B. Manual Command Line
```bash
# 1. Clone repository
git clone https://github.com/IqbalZarar-Khan/FallenWikiCrawler.git
cd FallenWikiCrawler

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch application
python main.py
```
Open **[http://localhost:8000](http://localhost:8000)** for the Landing Page or **[http://localhost:8000/crawler](http://localhost:8000/crawler)** for the Crawler Tool.

---

## 2. Railway Deployment

Railway detects `railway.json` and automatically deploys the application.

1. Create a new project on [Railway.app](https://railway.app).
2. Select **Deploy from GitHub repo** and choose `FallenWikiCrawler`.
3. Railway reads `railway.json` and `requirements.txt` automatically.
4. **Configuration Details**:
   - **Builder**: Nixpacks (Python 3.11)
   - **Start Command**: `python main.py`
   - **Port**: Dynamically assigned by Railway (`$PORT`), handled automatically by `main.py`.

---

## 3. Render Deployment

Render uses the included `render.yaml` Blueprint or can be configured manually.

### A. Automatic Blueprint (render.yaml)
1. Go to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** $\to$ **Blueprint**.
3. Connect `FallenWikiCrawler` repository and apply the blueprint.

### B. Manual Web Service Setup
- **Environment**: `Python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py` (or `uvicorn app:app --host 0.0.0.0 --port $PORT`)
- **Health Check Path**: `/health`

---

## 4. Docker & Container Deployment

A lightweight `Dockerfile` based on `python:3.11-slim` is included.

### Build and Run:
```bash
# Build the Docker image
docker build -t fallenwiki-crawler .

# Run container on port 8000
docker run -d -p 8000:8000 --name crawler fallenwiki-crawler
```

### Docker Compose (`docker-compose.yml`):
```yaml
version: '3.8'
services:
  crawler:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - HOST=0.0.0.0
    restart: unless-stopped
```

---

## 5. Generic Cloud / Nept / Koyeb / Fly.io / Heroku

For any cloud platform:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`
- **Port**: `8000` (or leave blank if dynamically bound via `$PORT`)
- **Health Check**: `/health` or `/healthz`

> [!TIP]
> Always use `python main.py` as the start command rather than hardcoded shell strings. `main.py` parses `$PORT` safely with fallback defaults across all cloud hosts.

---

## 6. Nginx Reverse Proxy Setup (SSE Streaming)

When hosting behind Nginx, **proxy buffering must be disabled** so Server-Sent Events stream in real-time without buffering delay:

```nginx
server {
    listen 80;
    server_name wiki.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Mandatory settings for Server-Sent Events (SSE)
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding on;
    }
}
```

---

## 7. Health Check API

Cloud orchestrators and uptime monitors can query the health endpoint:

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "app": "FallenWiki Crawler"
}
```
