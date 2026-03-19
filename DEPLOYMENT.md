# Aviothic AI Medical Platform - Deployment Guide

## Production Deployment

This guide covers deploying the Aviothic AI Medical Platform for production use.

## Prerequisites

- Docker and Docker Compose
- MongoDB (or use the provided container)
- Python 3.9+ (for local development)

## Quick Start with Docker Compose

The easiest way to deploy the application is using Docker Compose:

```bash
# Clone the repository
git clone <repository-url>
cd Aviothic.ai.pvt.ltd

# Copy environment file and customize
cp backend/.env.example backend/.env
# Edit backend/.env with your production settings

# Build and start services
docker-compose up -d
```

The application will be available at `http://localhost:8000`.

## Production Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required - Change this for production!
SECRET_KEY=your_production_secret_key_here_change_this

# MongoDB (for production, consider MongoDB Atlas)
MONGO_URI=mongodb://mongo:27017/aviothic_db

# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=False  # Always set to False in production
LOG_LEVEL=INFO
```

### Security Hardening

1. **Secret Key**: Generate a strong secret key for JWT tokens
2. **HTTPS**: Use SSL/TLS certificates in production
3. **Firewall**: Restrict access to necessary ports only
4. **Monitoring**: Enable proper logging and monitoring

## Frontend Deployment

The frontend can be deployed separately:

```bash
cd frontend
npm install
npm run build
```

Then serve the `build` directory with a web server like Nginx.

## Docker Configuration

The provided `Dockerfile` is optimized for production:

- Multi-stage build for smaller image size
- Non-root user for security
- Proper environment configuration
- Health checks

## Nginx Reverse Proxy

Use the provided `nginx.conf` for production deployments:

```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # For image uploads
        client_max_body_size 10M;
    }
}
```

## Database Configuration

For production, consider using MongoDB Atlas or a managed MongoDB service:

```bash
# Example MongoDB Atlas connection string
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/database_name
```

## Scaling

The application is designed to be horizontally scalable:

- Stateless API server
- External database
- Shared static file storage (consider S3 for production)

## Backup and Maintenance

- Regular MongoDB backups
- Monitor disk space for uploaded images
- Log rotation
- Security updates

## Troubleshooting

Common issues:

1. **Database Connection**: Ensure MongoDB is accessible
2. **Static Files**: Verify static directories have proper permissions
3. **Environment Variables**: Check all required variables are set
4. **Port Conflicts**: Ensure ports 8000 and 27017 are available

## Monitoring

Monitor these key metrics:

- API response times
- Database connection pool
- Disk space for uploads
- Memory and CPU usage
- Error rates

---

The Aviothic AI Medical Platform is now production-ready and can be deployed using these instructions.