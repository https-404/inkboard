# InkBoard — A Modern Publishing Platform

InkBoard is a Medium-like blogging platform built with **FastAPI**, designed to help you learn and apply real-world backend development concepts — authentication, role-based access, async ORM, background jobs, caching, and testing — all in a monolithic structure.

---

## Features

* JWT authentication with refresh tokens
* Role-based authorization (`admin`, `author`, `reader`)
* CRUD for posts, tags, and comments
* Markdown and sanitized HTML support
* Async database operations using SQLAlchemy
* Redis caching and Celery task queue
* Docker-based PostgreSQL and Redis setup
* Test coverage with `pytest` and `pytest-asyncio`

---

## Project Setup

### 1. Clone the Repository

```bash
git clone https://github.com/https-404/inkboard.git
cd inkboard
```

### 2. Setup Python Environment

Run the setup script to prepare everything automatically:

```bash
chmod +x setup.sh
./setup.sh
```

This will:

* Verify Python 3.12 is installed (via pyenv if necessary)
* Create a `.venv` virtual environment
* Install all dependencies listed in `requirements.txt`

To activate the virtual environment manually:

```bash
source .venv/bin/activate
```

To deactivate:

```bash
deactivate
```

---

## Running the Application

### 1. Environment Variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/inkboard
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 2. Start Postgres and MinIO with Docker (recommended for dev)

This repo includes `docker-compose.yaml` for Postgres and MinIO. The app service is provided but commented out so you can decide when to run the backend in Docker.

Run only services (db + storage):

```bash
docker compose up -d postgres minio minio-init
docker compose ps
```

Services:
- Postgres: `localhost:5432` (user `inkboardadmin`, password `inkboardadmin123`, db `inkboarddb`)
- MinIO S3 API: `http://127.0.0.1:9000`, Console: `http://127.0.0.1:9001` (login `inkboardadmin` / `inkboardadmin123`)

Keep the `app` service commented out for local development with hot reload. When ready to containerize the app, uncomment the `app` service in `docker-compose.yaml` and run:

```bash
docker compose up --build -d app
# or to run all services
docker compose up --build -d
```

### 3. Apply Database Migrations

```bash
alembic upgrade head
```

### 4. Run the FastAPI Server (local)

```bash
uvicorn app.main:app --reload
```

Now open:

```
http://localhost:8000/docs
```

You’ll see Swagger UI. ReDoc is available at `http://localhost:8000/redoc`.

### 5. Seed dummy data

Run the async seed script to insert users (with hashed passwords), tags, articles, follows, claps, and comments:

```bash
python -m app.scripts.seed
```

The script prints the plain password used for all generated users (default: `Password123!`).

---

## Running Tests

```bash
pytest --asyncio-mode=auto --cov=app
```

---

## Project Structure

```
inkboard/
├── app/
│   ├── core/              # Config, security, utils
│   ├── auth/              # JWT auth, registration, login
│   ├── users/             # Profiles, follows
│   ├── posts/             # Articles, tags, likes
│   ├── comments/          # Comment system
│   ├── background/        # Celery tasks
│   ├── tests/             # Test suites
│   ├── main.py            # App entrypoint
│   └── db/                # SQLAlchemy models & migrations
├── alembic/
├── docker-compose.yml
├── .env
├── setup.sh
├── README.md
└── requirements.txt
```

---

## Deployment Notes

* Use `gunicorn` with `uvicorn.workers.UvicornWorker` for production.
* Configure environment variables through a `.env` or managed secrets system.
* For background jobs, run:

  ```bash
  celery -A app.background.worker worker --loglevel=info
  ```
* Use `nginx` or `traefik` as a reverse proxy in deployment.

