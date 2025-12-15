# USSR Leaders Platform - Backend (FastAPI)

Modern async Python backend for the USSR Leaders Platform.

## Features

- 🚀 **FastAPI** - Modern, fast async web framework
- 🗄️ **PostgreSQL** - Production-grade database
- ⚡ **Async SQLAlchemy 2.0** - Async ORM
- 🔐 **JWT Authentication** - Secure token-based auth
- 🤖 **OpenAI Integration** - AI-generated historical facts
- 📊 **Redis Caching** - Performance optimization
- ✅ **Pydantic v2** - Data validation
- 📝 **Auto-generated API docs** - OpenAPI/Swagger

## Requirements

- Python 3.11+
- PostgreSQL 14+
- Redis 7+ (optional, for caching)

## Installation

### 1. Install Dependencies

```bash
cd backend-new
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

**Important**: Set a strong `SECRET_KEY` in production!

### 3. Start PostgreSQL

Using Docker:
```bash
docker run -d \
  --name ussr-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ussr_leaders \
  -p 5432:5432 \
  postgres:16-alpine
```

### 4. Initialize Database

```bash
python -m app.db.init_db
```

This will:
- Create all database tables
- Seed 7 USSR leaders
- Create admin user (admin@usssr.local / admin123)

### 5. Run Development Server

```bash
python -m app.main
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /` - API info

### Leaders
- `GET /api/v1/leaders` - Get all leaders
- `GET /api/v1/leaders/{id}` - Get leader by ID
- `GET /api/v1/leaders/{id}/facts` - Get AI-generated facts
- `GET /api/v1/leaders/search?q=query` - Search leaders
- `POST /api/v1/leaders` - Create leader (Admin)
- `PUT /api/v1/leaders/{id}` - Update leader (Editor/Admin)
- `DELETE /api/v1/leaders/{id}` - Delete leader (Admin)

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user

### Videos
- `GET /videos/{video_id}.mp4` - Stream video file

## Project Structure

```
backend-new/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # API endpoints
│   │       │   ├── leaders.py
│   │       │   └── auth.py
│   │       └── __init__.py
│   ├── core/
│   │   ├── config.py          # Configuration
│   │   ├── security.py        # Security utilities
│   │   └── exceptions.py      # Custom exceptions
│   ├── db/
│   │   ├── database.py        # Database connection
│   │   ├── init_db.py         # Database initialization
│   │   └── repositories/      # Data access layer
│   ├── models/
│   │   ├── user.py            # User model
│   │   └── leader.py          # Leader & Fact models
│   ├── schemas/
│   │   ├── user.py            # User schemas
│   │   └── leader.py          # Leader schemas
│   ├── services/
│   │   ├── auth_service.py    # Authentication logic
│   │   ├── leader_service.py  # Leader business logic
│   │   └── ai_service.py      # AI integration
│   └── main.py                # FastAPI application
├── tests/                     # Tests
├── requirements.txt
├── .env.example
└── README.md
```

## Development

### Code Quality

```bash
# Format code
black app/

# Sort imports
isort app/

# Lint
flake8 app/

# Type checking
mypy app/
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html
```

## OpenAI Integration

To enable real AI-generated facts:

1. Get an API key from https://platform.openai.com/
2. Add to `.env`:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```
3. Restart the server

Without an API key, the system uses mock facts.

## Database Migrations

Using Alembic (to be configured):

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Security

### Default Credentials

**⚠️ IMPORTANT**: Change default admin password in production!

Default admin user:
- Email: `admin@usssr.local`
- Password: `admin123`

### Production Checklist

- [ ] Change `SECRET_KEY` to a strong random string
- [ ] Change admin password
- [ ] Set `DEBUG=false`
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS
- [ ] Set up rate limiting
- [ ] Configure Redis for caching
- [ ] Set up monitoring and logging
- [ ] Regular security updates

## User Roles

- **Anonymous** - Can view leaders and facts
- **User** - Can bookmark, comment, rate (when implemented)
- **Editor** - Can edit leader information
- **Admin** - Full access, can manage users

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key (must be strong!)
- `OPENAI_API_KEY` - OpenAI API key (optional)
- `REDIS_URL` - Redis connection string (optional)
- `CORS_ORIGINS` - Allowed frontend origins

## Troubleshooting

### Database Connection Error

Make sure PostgreSQL is running:
```bash
docker ps | grep postgres
```

### Import Errors

Ensure virtual environment is activated:
```bash
source venv/bin/activate
```

### Port Already in Use

Change port in `.env`:
```
PORT=8001
```

## API Documentation

Full interactive API documentation is available at `/api/docs` when running in development mode.

## License

Educational project.
