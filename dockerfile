# =========================================
# Frontend Build
# =========================================

FROM node:20 AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./

RUN yarn install

COPY frontend .

RUN yarn run build


# =========================================
# Backend Runtime
# =========================================

FROM python:3.11-slim

WORKDIR /app

# =========================================
# FFmpeg
# =========================================

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nginx \
        ffmpeg \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# =========================================
# Python
# =========================================

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir 'uvicorn[standard]'

# =========================================
# Backend
# =========================================

COPY . .

# =========================================
# Frontend dist
# =========================================

COPY --from=frontend-build \
    /frontend/dist \
    /usr/share/nginx/html

# =========================================
# Nginx Config
# =========================================

COPY nginx.conf /etc/nginx/sites-enabled/default

# =========================================
# Start Script
# =========================================

RUN chmod +x start.sh

# =========================================
# Ports
# =========================================

EXPOSE 80

# =========================================
# Start
# =========================================

CMD ["./start.sh"]