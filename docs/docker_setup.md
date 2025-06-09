# Docker Deployment Guide

This document describes how to run the microservice using Docker and Docker Compose.

## Prerequisites

- **Docker** 24 or newer
- **Docker Compose** plugin (`docker compose`) or `docker-compose` 1.29+

Verify your installation:

```bash
docker --version
docker compose version   # or docker-compose --version
```

## Configuration

1. Clone the repository and change into the project directory:

```bash
git clone https://github.com/yourusername/data-microservice.git
cd data-microservice
```

2. Copy the provided environment file and update it with your credentials:

```bash
cp .env.example .env
# edit .env to set database and S3 credentials
```

The file contains all variables consumed by the backend and worker containers (PostgreSQL, Redis, AWS, etc.).

## Building and Starting Services

Run the following command from the project root:

```bash
docker compose up -d --build
```

This builds the backend and frontend images and starts four services:

- **backend** – FastAPI server
- **celery_worker** – worker for asynchronous tasks
- **db** – PostgreSQL database
- **redis** – Redis broker
- **frontend** – production React application served via Nginx

Database migrations are applied automatically when the backend container starts. If needed you can run them manually:

```bash
docker compose exec backend alembic upgrade head
```

## Checking Running Containers

Use `docker compose ps` to verify the services are up:

```bash
docker compose ps
```

You can inspect logs with:

```bash
docker compose logs -f backend  # follow backend logs
```

The application should now be reachable at `http://localhost` and the API at `http://localhost:8000`.

## Stopping Services

To stop and remove all containers, run:

```bash
docker compose down
```

Add `-v` to also remove persistent volumes if you need a clean reset.

