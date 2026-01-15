# Software Engineering Learning Roadmap
## Based on Your QuestPath Project

You've built a solid foundation. Here's what professional production applications have that you're missing, **prioritized by impact**.

---

## 🔴 CRITICAL (Learn These Next - Weeks 1-4)

### 1. **Automated Testing** (Week 1-2)
**Current State:** Minimal test coverage (< 10%)
**Production Standard:** 70-80% coverage

**Learn:**
- Unit tests (test individual functions)
- Integration tests (test API endpoints)
- Test fixtures and mocking
- pytest best practices

**Action Items:**
```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Create comprehensive tests
tests/
  test_users.py          # Test registration, login, profile
  test_goals.py          # Test CRUD operations
  test_quizzes.py        # Test quiz generation & submission
  test_progression.py    # Test XP awards, level unlocks
  test_ai_service.py     # Mock OpenAI, test error handling
```

**Example Test to Write:**
```python
# tests/test_users.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_user_registration():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 201
        assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_duplicate_registration_fails():
    # Test that registering same email twice fails
    pass

@pytest.mark.asyncio
async def test_weak_password_rejected():
    # Test password validation
    pass
```

**Learning Resources:**
- FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/
- Pytest Async: https://pytest-asyncio.readthedocs.io/
- **Practice Goal:** Get to 60% coverage in 2 weeks

**Why This Matters Most:**
- You can't confidently deploy without tests
- Enables CI/CD (next step)
- Catches bugs during development
- Documents how your code should work

---

### 2. **Error Handling & Observability** (Week 2-3)
**Current State:** Basic logging, no error tracking
**Production Standard:** Centralized error tracking + metrics

**Learn:**
- Exception handling patterns
- Error tracking (Sentry)
- Application metrics (Prometheus)
- Distributed tracing

**Action Items:**

**A. Add Sentry for Error Tracking:**
```bash
pip install sentry-sdk[fastapi]
```

```python
# app/main.py
import sentry_sdk

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.environment,
    traces_sample_rate=0.1,  # 10% of requests traced
)

# Now all unhandled exceptions automatically reported!
```

**B. Add Health Check Endpoint:**
```python
# app/health.py
@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # Check database
        await db.execute(text("SELECT 1"))
        
        # Check Redis
        await cache.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "cache": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")
```

**C. Add Request ID Tracing:**
```python
# app/middleware.py
import uuid
from fastapi import Request

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    logger.info("request_started", 
                request_id=request_id,
                method=request.method,
                path=request.url.path)
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

**Why This Matters:**
- Know about errors before users complain
- Debug production issues quickly
- Monitor application health
- Track performance bottlenecks

---

### 3. **CI/CD Pipeline** (Week 3-4)
**Current State:** Manual deployment
**Production Standard:** Automated testing + deployment

**Learn:**
- GitHub Actions
- Automated testing on PR
- Automated deployment
- Environment management

**Action Items:**

**Create `.github/workflows/test.yml`:**
```yaml
name: Test & Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:testpass@localhost:5432/testdb
          JWT_SECRET: test-secret
        run: |
          pytest --cov=app --cov-report=xml
      
      - name: Check coverage
        run: |
          coverage report --fail-under=60  # Fail if < 60% coverage
  
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: echo "Deploy to Render/Railway/Heroku"
```

**Why This Matters:**
- Tests run automatically on every change
- Prevents broken code from reaching production
- Faster deployment cycle
- Professional development workflow

---

## 🟠 HIGH PRIORITY (Weeks 5-8)

### 4. **Database Best Practices**
**Missing:**
- Connection pooling configuration
- Backup strategy
- Migration rollback testing
- Database indexes monitoring

**Add to your knowledge:**
```python
# app/db.py - Configure connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.log_sql_queries,
    pool_size=20,              # Max connections
    max_overflow=10,           # Additional connections when pool full
    pool_pre_ping=True,        # Verify connection health
    pool_recycle=3600,         # Recycle connections every hour
)
```

**Backup Strategy:**
```bash
# Create automated backup script
#!/bin/bash
# scripts/backup_db.sh
pg_dump $DATABASE_URL > backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

**Monitor Slow Queries:**
```python
# app/middleware.py
@app.middleware("http")
async def log_slow_queries(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    if duration > 1.0:  # Log requests over 1 second
        logger.warning("slow_request",
                      path=request.url.path,
                      duration_ms=int(duration * 1000))
    return response
```

---

### 5. **Security Hardening**
**What You're Missing:**
- Rate limiting (you have the file but is it applied?)
- Input validation everywhere
- SQL injection prevention (SQLAlchemy helps, but parameterize raw queries)
- CSRF protection
- Security headers

**Check Your Rate Limiting:**
<function_calls>
<invoke name="read_file">
<parameter name="filePath">c:\Users\abdux\OneDrive\Desktop\goal\app\rate_limiter.py