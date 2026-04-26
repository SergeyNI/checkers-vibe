# Checkers Vibe — Project Guide

Онлайн гра в шашки. Бекенд: Python + FastAPI + WebSockets. Фронтенд: Vue.js 3 + Pinia + TypeScript. Кеш/черга: Redis. Оркестрація: Docker Compose.

Підтримуються три варіанти правил: **Ukrainian** (8×8), **Brazilian** (8×8), **International** (10×10).

## Агенти

Усі агенти знаходяться в `.claude/agents/`. Claude Code автоматично підключає їх за описом.

| Агент | Коли використовувати |
|---|---|
| `checkers-domain-model` | моделі, сервіси, Redis-серіалізація |
| `checkers-frontend` | Vue-компоненти, Pinia stores, WebSocket-клієнт |
| `checkers-infrastructure` | Docker, Nginx, змінні середовища |
| `checkers-tests` | написання і запуск тестів (pytest / Vitest / Playwright) |
| `checkers-task-setter` | постановка задачі, узгодження правил гри |
| `change-critic` | критичний огляд перед будь-якою зміною архітектури |
| `agent-sync` | оновлення агентів після змін у проекті |

## Структура репозиторію

```
checkers-vibe/
├── backend/          # FastAPI, домен, сервіси
├── frontend/         # Vue.js 3, Pinia stores, компоненти
├── e2e/              # Playwright тести
├── docker-compose.yml
├── docker-compose.dev.yml
└── .claude/
    └── agents/       # агенти Claude Code
```

## Команди

```bash
# Dev середовище (hot reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Бекенд тести
docker compose exec backend pytest

# Фронтенд тести
docker compose exec frontend npm run test

# E2E
docker compose exec frontend npx playwright test
```

## Підтримка агентів

Після кожної зміни що впливає на поведінку, правила, архітектуру або контракти проекту — запропонувати оновлення відповідних файлів у `.claude/agents/` через агент `agent-sync` і чекати підтвердження від користувача перед записом.

## Ключові інваріанти

- `Cell` — `@dataclass(frozen=True)`, використовується як ключ словника
- `Board` — незмінна геометрія, ініціалізується як константи `BOARD_8` / `BOARD_10`
- `Player.connected` не існує — стан з'єднання живе в `SessionManager`
- `GameTimer` серіалізується в Redis — час не скидається після reconnect
- Захоплення обов'язкове; фронт не обчислює валідність ходів самостійно
- `winner: None` + `state: FINISHED` = нічия
- По закінченню часу гравець програє; `GameTimer.vue` попереджає при ≤ 1/10 початкового часу
