# Docker Deployment Guide

## Quick Start

```bash
# 1. Copy environment variables template
cp .env.example .env

# 2. Edit .env and add your secrets
# DB_PASSWORD, OPENAI_API_KEY, etc.

# 3. Build and start all services
docker-compose up --build

# 4. Access your app
http://localhost:8000/docs
http://localhost:8000/health
```

## Commands Reference

### Development
```bash
# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f app
docker-compose logs -f db

# Stop all services
docker-compose down

# Stop and remove volumes (deletes database!)
docker-compose down -v

# Rebuild after code changes
docker-compose up --build
```

### Production
```bash
# Build optimized image
docker build -t questpath:v1 .

# Run with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Debugging
```bash
# Execute command inside running container
docker-compose exec app bash

# View container resource usage
docker stats

# Inspect container details
docker inspect questpath-app
```

## Deployment to Ubuntu VM (Multipass)

### Step 1: Transfer Files
```bash
# From Windows
multipass transfer Dockerfile ubuntu:/home/ubuntu/questpath/
multipass transfer docker-compose.yml ubuntu:/home/ubuntu/questpath/
multipass transfer .env ubuntu:/home/ubuntu/questpath/
multipass transfer -r app ubuntu:/home/ubuntu/questpath/
```

### Step 2: SSH and Deploy
```bash
# SSH into VM
multipass shell ubuntu

# Navigate to project
cd questpath

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Step 3: Access from Windows
```bash
# Get VM IP
multipass list

# Access API
curl http://192.168.64.5:8000/health
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs app

# Check if port is already in use
netstat -ano | findstr :8000

# Remove old containers
docker-compose down
docker system prune
```

### Database connection failed
```bash
# Ensure database is healthy
docker-compose ps

# Check database logs
docker-compose logs db

# Verify connection string
docker-compose exec app env | grep DATABASE_URL
```

### Out of disk space
```bash
# Clean up unused images/containers
docker system prune -a

# Check disk usage
docker system df
```
