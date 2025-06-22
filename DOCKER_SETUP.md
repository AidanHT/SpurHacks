# 🐳 Docker Setup for Promptly

This document explains the complete Docker containerization setup for both frontend and backend services.

## 📦 Container Architecture

| Container | Service | Port | Purpose |
|-----------|---------|------|---------|
| `promptly-web` | Frontend | 3000 | React app (Nginx) |
| `promptly-api` | Backend | 8000 | FastAPI server |
| `promptly-mongo` | Database | 27017 | MongoDB database |
| `promptly-redis` | Cache | 6379 | Redis cache/rate limiting |
| `promptly-minio` | Storage | 9000/9001 | S3-compatible file storage |

## 🚀 Quick Start

### Production Environment
```bash
# Start all services
python run_docker.py prod

# Access applications
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
# MinIO Console: http://localhost:9001
```

### Development Environment (Hot Reload)
```bash
# Start with hot reload
python run_docker.py dev

# Access applications
# Frontend: http://localhost:5173 (hot reload)
# Backend: http://localhost:8000 (auto-reload)
```

## 📁 Docker Files Structure

```
SpurHacks/
├── frontend/
│   ├── Dockerfile          # Production build (multi-stage)
│   ├── Dockerfile.dev      # Development with hot reload
│   ├── nginx.conf          # Nginx configuration
│   └── .dockerignore       # Build optimization
├── backend/
│   ├── Dockerfile          # Python FastAPI container
│   └── .dockerignore       # (existing)
├── infra/
│   ├── docker-compose.yml     # Production services
│   ├── docker-compose.dev.yml # Development overrides
│   └── .env                   # Environment variables
└── run_docker.py              # Docker management script
```

## 🏗️ Container Details

### Frontend Container (`promptly-web`)

**Production (Dockerfile):**
- Multi-stage build: Node.js → Nginx
- Optimized static file serving
- Gzip compression enabled
- Security headers configured
- Health checks included

**Development (Dockerfile.dev):**
- Single-stage Node.js container
- Vite dev server with hot reload
- Volume mounting for live editing
- Fast iteration cycles

### Backend Container (`promptly-api`)

**Features:**
- Python 3.11 slim base image
- Poetry for dependency management
- Non-root user for security
- Health checks via `/ping` endpoint
- Auto-reload in development mode

### Infrastructure Services

**MongoDB:**
- Official Mongo 7 image
- Persistent data volumes
- Health checks with mongosh

**Redis:**
- Alpine-based for smaller size
- Password protection
- Persistent data with AOF

**MinIO:**
- S3-compatible object storage
- Web console interface
- Bucket auto-creation

## 🛠️ Docker Management Commands

### Using `run_docker.py` Script

```bash
# Build all containers
python run_docker.py build

# Build specific service
python run_docker.py build --service web

# Start development environment
python run_docker.py dev

# Start production environment
python run_docker.py prod

# View logs (all services)
python run_docker.py logs

# View logs (specific service)
python run_docker.py logs --service api

# Stop all containers
python run_docker.py stop

# Clean up everything
python run_docker.py clean
```

### Manual Docker Compose Commands

```bash
cd infra

# Production
docker-compose up -d
docker-compose down

# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# View logs
docker-compose logs -f
docker-compose logs api

# Rebuild specific service
docker-compose build web
```

## 🔧 Configuration

### Environment Variables

The containers use environment variables from your `.env` file:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000
GEMINI_API_KEY=your-api-key-here

# Database
MONGODB_URL=mongodb://mongo:27017/promptly
REDIS_URL=redis://:redispassword@redis:6379

# Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Security
JWT_SECRET_KEY=your-secret-key
```

### Volume Mounts

**Production:**
- Named volumes for data persistence
- No source code mounting

**Development:**
- Source code mounted for live editing
- `node_modules` volume to prevent conflicts

## 🔍 Health Checks

All containers include health checks:

```bash
# Check container health
docker ps

# Manually test health endpoints
curl http://localhost:8000/ping      # Backend
curl http://localhost:3000/health    # Frontend
```

## 📊 Resource Requirements

**Minimum System Requirements:**
- 8GB RAM
- 20GB disk space
- Docker Desktop running

**Container Resource Usage:**
- Frontend: ~50MB (production), ~200MB (development)
- Backend: ~200MB
- MongoDB: ~100MB + data
- Redis: ~20MB
- MinIO: ~50MB + data

## 🚀 Development Workflow

### Frontend Development
```bash
# Start only frontend in dev mode
python run_docker.py dev --service web

# Or use local development for faster iteration
npm run dev  # In frontend directory
```

### Backend Development
```bash
# Start only backend in dev mode
python run_docker.py dev --service api

# Or use local development for debugging
python run_backend.py  # In root directory
```

### Full Stack Development
```bash
# Start everything in development mode
python run_docker.py dev

# Monitor logs in real-time
python run_docker.py logs
```

## 🐛 Troubleshooting

### Common Issues

**Docker not starting:**
```bash
# Check Docker Desktop status
docker ps

# Restart Docker Desktop if needed
```

**Port conflicts:**
```bash
# Check what's using ports
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Stop conflicting processes or change ports in docker-compose.yml
```

**Build failures:**
```bash
# Clean and rebuild
python run_docker.py clean
python run_docker.py build

# Check logs for specific errors
python run_docker.py logs --service web
```

**Environment variable issues:**
```bash
# Verify .env file is loaded
docker-compose config

# Check container environment
docker exec -it promptly-api env
```

### Performance Optimization

**Faster builds:**
- Use `.dockerignore` files
- Layer caching with multi-stage builds
- Only install required dependencies

**Development speed:**
- Use development compose override
- Volume mount source code
- Use hot reload features

## 📝 Production Deployment

For production deployment:

1. **Set production environment variables**
2. **Use production docker-compose.yml**
3. **Configure reverse proxy (nginx/traefik)**
4. **Set up SSL certificates**
5. **Configure backups for volumes**

```bash
# Production deployment
ENVIRONMENT=production python run_docker.py prod
```

## 🔐 Security Considerations

- Non-root users in containers
- Security headers in nginx
- Environment variable protection
- Network isolation with custom network
- Regular security updates for base images

---

🎉 **Your Promptly application is now fully containerized!** Both frontend and backend run seamlessly in Docker with development and production configurations. 