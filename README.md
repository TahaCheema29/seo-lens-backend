# SEO Lens Backend

FastAPI backend for SEO analysis, keyword research, and site crawling.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Make (optional, for convenience commands)

### Run with Docker (Recommended)

```bash
# Start all services (app + postgres + redis)
make docker-up
```

This will:
1. Build Docker images
2. Start PostgreSQL, Redis, and API
3. Run database migrations automatically
4. Start the API on http://localhost:8000

**API Documentation:** http://localhost:8000/docs

---

## All Commands

### Docker Commands

| Command | When to Use | Description |
|---------|-------------|-------------|
| `make docker-up` | Starting project | Build & start all services |
| `make docker-down` | Stopping project | Stop all running services |
| `make docker-logs` | Debugging issues | View live application logs |
| `make docker-build` | Dependency changes | Rebuild Docker images |

### Database Commands (Docker)

| Command | When to Use | Description |
|---------|-------------|-------------|
| `make docker-migrate` | Pulling new code | Apply existing migrations |
| `make docker-migrate-create MSG="..."` | After model changes | Create new migration file |
| `make docker-migrate-init` | Fresh project setup | Initialize database from scratch |
| `make docker-db-tables` | Checking tables | List all database tables |
| `make docker-db-shell` | Manual DB queries | Open PostgreSQL shell |
| `make docker-db-reset` | Starting over | Drop all tables and re-run migrations |

### Development Commands (Local without Docker)

| Command | When to Use | Description |
|---------|-------------|-------------|
| `make install` | First time setup | Install Python dependencies |
| `make dev` | Local development | Run API with hot-reload |
| `make test` | Running tests | Execute test suite |
| `make clean` | Cleaning up | Remove cache files |

### Database Commands (Local)

| Command | When to Use | Description |
|---------|-------------|-------------|
| `make migrate` | Pulling new code | Apply existing migrations |
| `make create-migrate MSG="..."` | After model changes | Create new migration file |
| `make init-db` | Fresh setup | Initialize database locally |

---

## Project Structure

```
src/
├── admin/              # Admin authentication & user management
│   ├── auth/          # Admin login, register
│   └── users/         # Admin manage users
├── auth/              # User authentication
├── keyword_rank/       # Keyword ranking analysis
├── keyword_suggestion/ # Keyword suggestions
├── seo_insight/        # SEO site analysis
├── models/            # SQLAlchemy models
├── core/              # Security, utilities
├── config/            # Database, Redis, Settings
└── seo_tools/         # Existing SEO tools

alembic/               # Database migrations
scripts/               # Utility scripts
```

---

## For New Team Members

```bash
# 1. Clone repository
git clone <repo-url>
cd seo-lens-backend

# 2. Set up environment
cp .env.docker .env.local

# 3. Start everything
make docker-up

# 4. Check API
open http://localhost:8000/docs
```

---

## After Model Changes

```bash
# 1. Change model in src/models/
# 2. Create migration
make docker-migrate-create MSG="add user table"

# 3. Migration file created in alembic/versions/
# 4. Commit the new migration file
git add alembic/versions/xxx_add_user_table.py
git commit -m "feat: add user table migration"
```

---

## When Team Pulls Your Changes

```bash
# After pulling code with new migrations
git pull
make docker-migrate    # Apply new migrations
```

---

## Environment Variables

Create `.env.local` file (use `.env.example` as template):

```env
# App
DEBUG=false
APP_NAME=SEO Lens

# Database (Docker)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/seo_lens

# Redis (Docker)
REDIS_URL=redis://redis:6379

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Google API Keys
GOOGLE_CLOUD_API_KEY_1=your-key
GOOGLE_CLOUD_API_KEY_2=your-key
GOOGLE_CLOUD_API_KEY_3=your-key
GOOGLE_CLOUD_CSE=your-cse-id
PAGESPEED_API_KEY=your-key
```

---

## API Endpoints

| Module | Prefix | Description |
|--------|--------|-------------|
| User Auth | `/auth` | Login, register, profile |
| Admin Auth | `/admin/auth` | Admin login, register |
| Admin Users | `/admin/users` | Manage users |
| Keyword Rank | `/keyword-rank` | Keyword ranking analysis |
| Keyword Suggestion | `/keyword-suggestion` | Keyword research |
| SEO Insight | `/seo-insight` | Site SEO analysis |
| SEO Tools | `/seo-tools` | Public SEO tools |

---

## Troubleshooting

### Port already in use
```bash
# Check what's using port
sudo lsof -i :8000
sudo lsof -i :5432

# Stop local PostgreSQL
sudo systemctl stop postgresql
```

### Container won't start
```bash
# View logs
make docker-logs

# Rebuild everything
make docker-down
make docker-build
make docker-up
```

### Database tables missing
```bash
# Check tables
make docker-db-tables

# Apply migrations
make docker-migrate
```

### Reset everything
```bash
# Stop and remove volumes
docker compose down -v

# Start fresh
make docker-up
```

---

## Tech Stack

- **Python 3.12**
- **FastAPI** - Web framework
- **SQLAlchemy 2.0** - ORM (async)
- **PostgreSQL** - Database
- **Redis** - Caching/WebSocket
- **Playwright** - Browser automation
- **Alembic** - Database migrations
- **Docker** - Containerization

---

## License

Private repository.