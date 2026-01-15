# QuestPath API

QuestPath is a gamified learning platform that transforms educational goals into RPG-style progression systems with AI-powered roadmaps.

## 🚀 Features

- **AI-Powered Roadmaps**: Generate personalized learning paths using OpenAI
- **Progressive Learning**: Unlock levels by completing topics and passing quizzes
- **Gamification**: Earn XP, track progress, and compete on leaderboards
- **Quiz System**: AI-generated quizzes to validate knowledge
- **User Progression**: Track completed levels and overall learning progress

## 🛠️ Tech Stack

- **FastAPI**: Modern, fast Python web framework
- **PostgreSQL**: Robust relational database
- **SQLAlchemy 2.0**: Async ORM for database operations
- **Alembic**: Database migrations
- **OpenAI API**: AI-powered content generation
- **JWT**: Secure authentication
- **Docker**: PostgreSQL containerization

## 📦 Installation

### Prerequisites

- Python 3.11+
- Docker (for PostgreSQL)
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd goal
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # Windows
   # or
   source .venv/bin/activate      # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your values:
   # - DATABASE_URL
   # - JWT_SECRET
   # - OPENAI_API_KEY
   ```

5. **Start PostgreSQL**
   ```bash
   docker run -d \
     --name questpath-postgres \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=questpath \
     -p 6543:5432 \
     postgres:16
   ```

6. **Run migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the server**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login with credentials
- `GET /auth/me` - Get current user info

### Goals
- `POST /goals` - Create goal with AI-generated roadmap
- `GET /goals/me` - List user's goals
- `GET /goals/{id}` - Get goal details with roadmap

### Levels & Topics
- `PATCH /levels/{id}/topics/{index}` - Mark topic as completed

### Quizzes
- `GET /levels/{id}/quiz` - Get AI-generated quiz
- `POST /levels/{id}/quiz/submit` - Submit quiz answers

### Progression
- `GET /progression/stats` - Get user stats (XP, levels completed)
- `GET /leaderboard` - View global leaderboard

## 🗄️ Database Schema

- **users**: User accounts with XP tracking
- **goals**: Learning goals with metadata
- **roadmaps**: Learning paths for goals
- **levels**: Individual learning stages
- **Topics**: JSON array with completion tracking

## 🧪 Development

### Running Tests
```bash
pytest
```

### Creating Migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 🚢 Deployment

(Add your deployment instructions here)

## 📝 License

MIT License

## 👤 Author

Abduxalilov Shaxboz
# Automated deployment test
