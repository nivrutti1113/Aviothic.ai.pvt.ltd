# Aviothic AI Medical Imaging Platform - Backend

Production-ready FastAPI backend for medical AI breast cancer detection with Grad-CAM explainability.

## 🏥 Healthcare Startup Ready Features

### 🔒 Security & Authentication
- **JWT Authentication** with bcrypt password hashing
- **Role-Based Access Control** (Admin, Doctor roles)
- **Rate Limiting** to prevent abuse (10 requests/minute)
- **CORS Hardening** with configurable allowed origins
- **Secure Token Management** with 30-minute expiration

### 🛡️ Medical Audit Compliance
- **Structured Logging** with request tracing
- **Model Usage Auditing** for regulatory compliance
- **Error Handling** without internal tracebacks
- **Database Indexing** for audit query performance
- **Request ID Tracking** for incident investigation

### 🚀 Production Features
- **Single Model Load** pattern (not per request)
- **MongoDB Integration** with proper indexing
- **Static File Serving** for Grad-CAM images
- **Health Check Endpoints** for monitoring
- **Docker Deployment** with security hardening
- **Multi-worker Support** for scalability

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.9+
- 4GB+ RAM recommended

## 🚀 Quick Start

### 1. Environment Setup

Create `.env` file in backend directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database
MONGO_ROOT_PASSWORD=your_secure_mongo_password
MONGO_URI=mongodb://admin:your_secure_mongo_password@localhost:27017/aviothic_db?authSource=admin

# Security
SECRET_KEY=your_production_secret_key_here_change_this_to_a_very_long_random_string
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Model Configuration
MODEL_PATH=./app/models/model.pt
MODEL_VERSION=v1.0.0

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60
```

### 2. Start Services

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Initialize Admin User

```bash
# Create first admin user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@hospital.com",
    "password": "SecurePassword123!",
    "full_name": "System Administrator",
    "hospital": "Aviothic Medical Center",
    "role": "admin"
  }'
```

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/logout` - User logout

### Medical Prediction
- `POST /api/v1/predict` - Run medical image prediction (requires doctor/admin role)
- `GET /api/v1/health` - Health check endpoint
- `GET /api/v1/statistics` - Inference statistics

### Protected Endpoints
All endpoints except `/api/v1/auth/login` and `/api/v1/health` require:
- Valid JWT Bearer token in Authorization header
- Appropriate user role (doctor or admin for predictions)

## 🔧 Development Setup

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start MongoDB (if not using Docker)
mongod --dbpath ./data/db

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing Authentication

```bash
# 1. Register a doctor user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@hospital.com",
    "password": "DoctorPassword123!",
    "full_name": "Dr. Jane Smith",
    "hospital": "City Hospital",
    "role": "doctor"
  }'

# 2. Login to get token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@hospital.com",
    "password": "DoctorPassword123!"
  }'

# 3. Use token for prediction
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@path/to/medical/image.jpg"
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── models/          # Pydantic models and schemas
│   ├── routes/          # API route handlers
│   ├── services/        # Business logic services
│   ├── middleware/      # Authentication and security middleware
│   ├── static/          # Static files (uploads, Grad-CAM)
│   ├── config.py        # Configuration management
│   ├── db.py            # Database connection
│   └── main.py          # FastAPI application
├── Dockerfile           # Production Docker image
├── docker-compose.yml   # Multi-service deployment
├── mongo-init.js        # MongoDB initialization
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables
```

## 🛡️ Security Features

### Authentication Flow
1. User registers with email/password
2. Password hashed with bcrypt (12 rounds)
3. JWT token generated with 30-minute expiration
4. Token required for all protected endpoints
5. Role-based access control enforced

### Rate Limiting
- 10 requests per minute per IP address
- Prevents abuse and DoS attacks
- Configurable via environment variables

### CORS Configuration
- Restricted to configured origins only
- No wildcard `*` in production
- Secure headers only allowed

## 📈 Monitoring & Logging

### Structured Logging
All requests are logged with:
- Request ID for tracing
- User ID (when authenticated)
- Processing time
- Client IP address
- Error details (when applicable)

### Health Monitoring
- `/` - Basic service status
- `/api/v1/health` - Detailed health check
- Docker health checks configured
- Request/response metrics

## ⚠️ Production Considerations

### Security Hardening
- [ ] Change default SECRET_KEY
- [ ] Use HTTPS in production
- [ ] Configure proper ALLOWED_ORIGINS
- [ ] Set up SSL/TLS termination
- [ ] Implement proper backup strategy
- [ ] Set up monitoring and alerting

### Model Deployment
- [ ] Replace dummy model with real trained model
- [ ] Validate model performance metrics
- [ ] Implement model versioning
- [ ] Set up model monitoring
- [ ] Configure proper GPU resources if needed

### Scaling
- [ ] Configure load balancer
- [ ] Set up Redis for session storage
- [ ] Implement database connection pooling
- [ ] Configure auto-scaling policies
- [ ] Set up CDN for static files

## 🆘 Troubleshooting

### Common Issues

**MongoDB Connection Failed**
```bash
# Check if MongoDB is running
docker-compose ps mongodb

# View MongoDB logs
docker-compose logs mongodb
```

**Authentication Errors**
```bash
# Check JWT token validity
# Ensure SECRET_KEY is properly set
# Verify token expiration time
```

**Rate Limiting**
```bash
# Check current rate limit settings
# Monitor logs for rate limit violations
# Adjust RATE_LIMIT_* variables if needed
```

## 📞 Support

For production deployment assistance, contact the Aviothic AI engineering team.

**DUMMY MODEL WARNING**: This deployment uses a dummy model for demonstration purposes. Replace with real trained medical model before production use.