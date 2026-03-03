# Prom CRM Monorepo

MVP CRM для товарів Prom з монорепо структурою:

- `backend` - FastAPI + SQLAlchemy + Alembic
- `frontend` - Next.js (App Router) адмін-панель
- `docker-compose.yml` - локальний запуск (з опціональним локальним Postgres)

## Функції MVP

1. Імпорт XLSX експорту Prom (2 листи: товари + групи), upsert по `prom_uid` (`Унікальний_ідентифікатор`).
2. Сторінка `Товари`: пошук, пагінація, редагування `price/qty/availability`.
3. Сторінка `Склад`: створення рухів `IN/OUT/ADJUST`, оновлення залишку, історія рухів.
4. Простий admin логін через `ADMIN_USER`/`ADMIN_PASS`.
5. R2 модуль: API для signed upload/download URL.
6. Синхронізація товарів і замовлень з Prom API (ручний запуск через API/UI).

## Структура

- `backend/`
- `frontend/`
- `docker-compose.yml`
- `.env.example`

## ENV

### Backend

- `DATABASE_URL`
- `ADMIN_USER`
- `ADMIN_PASS`
- `SECRET_KEY`
- `CORS_ORIGIN`
- `PROM_API_TOKEN`
- `PROM_API_BASE_URL` (default: `https://my.prom.ua/api/v1`)
- `PROM_PRODUCTS_ENDPOINT` (default: `/products/list`)
- `PROM_ORDERS_ENDPOINT` (default: `/orders/list`)
- `PROM_PAGE_SIZE` (default: `100`)
- `PROM_MAX_PAGES` (default: `50`)
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_ENDPOINT`

### Frontend

- `NEXT_PUBLIC_API_URL`

## Локальний запуск (без Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Вкажіть DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

## Локальний запуск (Docker Compose)

```bash
docker compose up --build
```

Сервіси:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Postgres: `localhost:5432`

## API огляд

### Auth

- `POST /auth/login` `{ "username": "...", "password": "..." }`

### Import

- `POST /import/prom-xlsx` (multipart form-data, поле `file`)

### Products

- `GET /products?q=&page=1&per_page=20`
- `PATCH /products/{id}` `{ "price": 123, "qty": 10, "availability": "available" }`

### Orders

- `GET /orders?page=1&per_page=20`

### Inventory

- `POST /inventory/movements`
- `GET /inventory/movements?limit=100`

### Prom Sync

- `POST /prom/sync/products`
- `POST /prom/sync/orders`
- `POST /prom/sync/all`

### R2

- `POST /r2/upload-url` `{ "object_key": "path/file.jpg", "mime": "image/jpeg" }`
- `POST /r2/download-url` `{ "object_key": "path/file.jpg" }`

## Railway + Supabase деплой

Нижче схема для **2 сервісів Railway** (`backend`, `frontend`) і окремої БД Supabase.

### 1. Створіть Supabase Postgres

1. У Supabase створіть проект.
2. Візьміть connection string формату `postgresql://...`.
3. Для зовнішніх підключень використовуйте URI з SSL (`?sslmode=require`, якщо потрібно вашим URI).

### 2. Railway: backend service

1. Створіть новий Railway service з коренем `backend`.
2. Build: Dockerfile (`backend/Dockerfile`).
3. Додайте ENV:
   - `DATABASE_URL=<supabase postgres url>`
   - `ADMIN_USER=<admin login>`
   - `ADMIN_PASS=<admin pass>`
   - `SECRET_KEY=<strong-random-secret>`
   - `CORS_ORIGIN=<your-frontend-railway-domain>`
   - `PROM_API_TOKEN=<prom bearer token>`
   - (optional) `PROM_API_BASE_URL`, `PROM_PRODUCTS_ENDPOINT`, `PROM_ORDERS_ENDPOINT`, `PROM_PAGE_SIZE`, `PROM_MAX_PAGES`
   - `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_ENDPOINT`
4. Start command у Dockerfile вже виконує:
   - `alembic upgrade head`
   - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 3. Railway: frontend service

1. Створіть другий Railway service з коренем `frontend`.
2. Build: Dockerfile (`frontend/Dockerfile`).
3. ENV:
   - `NEXT_PUBLIC_API_URL=https://<backend-domain>`

### 4. CORS

У backend встановіть `CORS_ORIGIN` рівно у домен frontend сервісу Railway.

### 5. Перевірка після деплою

1. `GET https://<backend-domain>/health` -> `{"status":"ok"}`
2. Увійдіть в frontend через `ADMIN_USER`/`ADMIN_PASS`
3. Запустіть синк товарів `POST /prom/sync/products`
4. Запустіть синк замовлень `POST /prom/sync/orders`
5. (Опційно) Завантажте XLSX через `POST /import/prom-xlsx`
6. Перевірте зміну товарів, замовлень і створення рухів складу

### (Опційно) Автооновлення з Prom на Railway

Створіть Railway Cron Job, який викликає `POST https://<backend-domain>/prom/sync/all` з Bearer токеном admin (отримати через `/auth/login`), наприклад кожні 5-15 хвилин.

## Примітки по валідації і помилках

- 401: невалідний токен або логін/пароль
- 403: доступ не admin
- 404: товар не знайдений
- 400: невалідний XLSX або некоректний складський рух (наприклад, OUT більше ніж qty)
- Pydantic валідує числові поля, мінімальні значення та обов'язковість

## Що можна додати далі

- Ролі користувачів і refresh token
- UI для XLSX імпорту та R2 завантажень
- Фільтри по групах, сортування, bulk-редагування
- Тести (pytest + Playwright)
