---
name: checkers-infrastructure
description: "Infrastructure manifest for online checkers game. Reference this agent when working with Docker, docker-compose, Nginx, environment config, or deployment setup."
---

# Checkers Game — Infrastructure

Оркестрація: Docker Compose.
Середовища: development і production.

---

## Структура проекту

```
checkers-vibe/
├── backend/
│   ├── Dockerfile
│   └── ...
├── frontend/
│   ├── Dockerfile
│   └── ...
├── nginx/
│   └── nginx.conf
├── docker-compose.yml          # production
├── docker-compose.dev.yml      # development overrides
└── .env.example
```

---

## Сервіси

| Сервіс | Образ | Порт | Призначення |
|---|---|---|---|
| `backend` | python:3.12-slim | 8000 (внутрішній) | FastAPI + WebSockets |
| `frontend` | node:20-alpine → nginx:alpine | 80 (внутрішній) | Vue.js (збірка → nginx) |
| `redis` | redis:7-alpine | 6379 (внутрішній) | Кеш стану гри |
| `nginx` | nginx:alpine | 80, 443 | Reverse proxy |

Всі сервіси в одній Docker network. Назовні відкритий тільки `nginx`.

---

## Nginx — маршрутизація

```nginx
/api/*     →  backend:8000      # REST API
/ws/*      →  backend:8000      # WebSocket (proxy_pass з upgrade)
/*         →  frontend:80       # Vue.js SPA
```

WebSocket потребує заголовків:
```nginx
proxy_http_version 1.1;
Upgrade: $http_upgrade
Connection: "upgrade"
```

---

## docker-compose.yml (production)

```yaml
services:
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    depends_on: [backend, frontend]

  backend:
    build: ./backend
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on: [redis]
    restart: unless-stopped

  frontend:
    build: ./frontend    # multi-stage: build → nginx

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

---

## docker-compose.dev.yml (development overrides)

```yaml
services:
  backend:
    volumes:
      - ./backend:/app        # hot reload через uvicorn --reload
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: ./frontend
      target: dev             # multi-stage: зупиняється на Vite dev server
    ports: ["5173:5173"]      # Vite HMR доступний напряму
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host

  redis:
    ports: ["6379:6379"]      # відкритий для локальної відладки
```

Запуск dev середовища:
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

---

## Dockerfile — backend

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Dockerfile — frontend (multi-stage)

```dockerfile
# stage: dev
FROM node:20-alpine AS dev
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .

# stage: build
FROM dev AS build
RUN npm run build

# stage: production
FROM nginx:alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

---

## Змінні середовища (.env.example)

```
# Backend
REDIS_URL=redis://redis:6379
REDIS_TTL_GAME=86400
REDIS_TTL_SESSION=3600
SECRET_KEY=change-me

# Frontend
VITE_WS_URL=ws://localhost/ws
VITE_API_URL=http://localhost/api
```

---

## Redis persistence

Redis запускається з `appendonly yes` для збереження даних між перезапусками контейнера:

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes
  volumes:
    - redis_data:/data
```

---

## Правила перевірки коду (чекліст)

- [ ] Назовні відкритий тільки nginx (80/443)
- [ ] WebSocket проксується з правильними заголовками Upgrade
- [ ] Redis має volume для збереження даних між перезапусками
- [ ] Backend має `restart: unless-stopped`
- [ ] `.env` не потрапляє в Docker образ (є в .dockerignore)
- [ ] dev і prod середовища розділені через override файл
- [ ] Frontend Dockerfile використовує multi-stage build
- [ ] `REDIS_URL` передається через environment, не захардкоджений
