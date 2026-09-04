# Deployment & Operations 🚀

This document covers operational guidance, environment configurations, and production deployment recipes for **FallenWiki Crawler**.

---

## 1. Installation & Quickstart

```bash
# 1. Install required Python packages
pip install fastapi uvicorn requests

# 2. Launch the server
python app.py
```

---

## 2. Nginx Reverse Proxy Setup (SSE Streaming)

When hosting behind Nginx, **proxy buffering must be disabled** so Server-Sent Events stream in real-time:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    # Mandatory for Server-Sent Events (SSE)
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding on;
}
```
