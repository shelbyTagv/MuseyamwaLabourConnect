# MuseyamwaLabourConnect 🇿🇼

> A dynamic, tokenized, real-time job and labour marketplace PWA for Zimbabwe.

## 🏗️ Tech Stack

| Layer       | Technology                                          |
| ----------- | --------------------------------------------------- |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy (async), PostgreSQL |
| **Frontend**| React 18, Vite, Tailwind CSS, Zustand               |
| **Realtime**| WebSockets (location, chat, notifications)           |
| **Maps**    | Leaflet.js with heatmap overlay                      |
| **Payments**| Pesepay API (EcoCash / Innbucks)                     |
| **Auth**    | JWT (access + refresh tokens), RBAC                  |
| **DevOps**  | Docker, Docker Compose, Nginx                        |
| **PWA**     | Vite PWA plugin, service worker, manifest            |

## 📁 Project Structure

```
museyamwa-labour-connect/
├── backend/
│   ├── app/
│   │   ├── models/       # SQLAlchemy ORM (11 models)
│   │   ├── routes/       # FastAPI API routes (/api/v1)
│   │   ├── services/     # Business logic (auth, tokens, jobs, etc.)
│   │   ├── tests/        # Pytest test suite
│   │   ├── config.py     # Pydantic-settings config
│   │   ├── database.py   # Async engine & session
│   │   ├── schemas.py    # Pydantic request/response models
│   │   ├── main.py       # FastAPI app entrypoint
│   │   └── seed.py       # Sample data seeder
│   ├── alembic/          # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # Layout, shared UI
│   │   ├── hooks/        # useAuth, useWebSocket, useGeolocation
│   │   ├── pages/        # 10 pages (dashboard, chat, map, etc.)
│   │   └── services/     # Axios API client with JWT interceptors
│   ├── public/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.sample
└── .gitignore
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OR: Python 3.12+, Node 20+, PostgreSQL 16+

### With Docker
```bash
cp .env.sample .env     # Edit values as needed
docker compose up --build
```
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### Without Docker

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev   # → http://localhost:5173
```

### Seed Database
```bash
cd backend
python -m app.seed
```

## 🔐 API Endpoints

| Group         | Path                    | Description                          |
| ------------- | ----------------------- | ------------------------------------ |
| Auth          | `/api/v1/auth/`         | Register, login, refresh, /me        |
| Users         | `/api/v1/users/`        | Profile management                   |
| Jobs          | `/api/v1/jobs/`         | CRUD + status lifecycle              |
| Offers        | `/api/v1/offers/`       | Negotiate job offers                 |
| Tokens        | `/api/v1/tokens/`       | Wallet balance, purchase, history    |
| Payments      | `/api/v1/payments/`     | Pesepay webhook + status             |
| Locations     | `/api/v1/locations/`    | GPS update, nearby, heatmap + WS     |
| Messages      | `/api/v1/messages/`     | Chat REST + WebSocket                |
| Ratings       | `/api/v1/ratings/`      | Submit & retrieve ratings            |
| Notifications | `/api/v1/notifications/`| Notification list + mark read        |
| Admin         | `/api/v1/admin/`        | Dashboard, user mgmt, audit logs     |

## 🎨 Features

- **GPS Heatmap**: Live map of online workers with profession filters
- **Token Economy**: Purchase tokens via EcoCash/Innbucks to post jobs
- **Real-time Chat**: WebSocket-powered instant messaging
- **Job Lifecycle**: Full state machine (requested → rated)
- **PWA**: Installable, offline support, push-ready
- **Admin Panel**: Platform stats, user management, audit trail
- **Role-based Access**: Employer, Employee, Admin roles with RBAC

## 🧪 Testing

```bash
cd backend
pytest                # Run backend tests
```

## 🔑 Environment Variables

See `.env.sample` for all required variables.

## 📄 License

MIT
