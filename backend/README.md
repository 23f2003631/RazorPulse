# RazorPulse Backend

FastAPI-based backend for RazorPulse risk investigation system.

## Project Structure

```
backend/
├── README.md
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config/              # Configuration management
│   ├── api/                 # API endpoints
│   │   ├── __init__.py
│   │   └── routes/          # Route handlers
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic validation schemas
│   ├── services/            # Business logic layer
│   │   ├── razorpay/        # Razorpay integration
│   │   ├── exa/             # Exa AI discovery
│   │   ├── gemini/          # Gemini verification
│   │   ├── scoring/         # Corroboration scoring engine
│   │   └── investigation/   # Investigation orchestration
│   ├── repositories/        # Data access layer
│   ├── core/                # Core utilities
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── logging.py       # Logging configuration
│   │   └── security.py      # Security utilities
│   └── utils/               # Helper functions
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── fixtures/            # Test fixtures and mocks
└── scripts/                 # Utility scripts
```

## Architecture

### Layered Architecture

1. **API Layer** (`api/routes/`): HTTP endpoints, request validation
2. **Service Layer** (`services/`): Business logic and orchestration
3. **Data Access Layer** (`repositories/`): Database operations
4. **Models/Schemas** (`models/`, `schemas/`): Data structures
5. **Core** (`core/`): Shared utilities, exceptions, logging

### Service Responsibility Separation

Each service module has a specific responsibility:

- **razorpay/**: Razorpay API integration, webhook handling
- **exa/**: Exa AI external event discovery
- **gemini/**: Gemini LLM evidence interpretation
- **scoring/**: Deterministic corroboration rules engine
- **investigation/**: Investigation workflow orchestration

## Setup (Planned)

### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Configuration
```bash
cp .env.example .env.local
# Edit .env.local with your actual values
```

### Run Application
```bash
uvicorn app.main:app --reload
```

### Run Tests
```bash
pytest tests/
```

## Dependencies (Planned)

Core dependencies will include:
- FastAPI: Web framework
- Pydantic: Data validation
- SQLAlchemy: ORM
- psycopg2: PostgreSQL adapter
- requests: HTTP client
- python-dotenv: Environment configuration

See `requirements.txt` for complete list.

## Configuration

Configuration is managed through:
- Environment variables (`.env`)
- Pydantic `Settings` class in `app/config/`
- Application startup in `app/main.py`

## Database

Database interactions are abstracted through the **Repository Pattern** in `repositories/`. Models are defined in `models/` using SQLAlchemy.

## Testing Strategy

- **Unit Tests** (`tests/unit/`): Service and utility logic
- **Integration Tests** (`tests/integration/`): API endpoints and database operations
- **Fixtures** (`tests/fixtures/`): Mock data and test utilities

## Security Notes

- All secrets must be in `.env.local` and never committed
- API keys for external services are server-side only
- No payment operations are performed by the backend
- All operations are read-only or investigation-supporting

## Status

**Phase 0 - Repository Initialization**

No application logic has been implemented. This is a structural skeleton only.

Future phases will implement:
1. Razorpay webhook ingestion
2. Exa AI discovery integration
3. Gemini verification pipeline
4. Scoring engine
5. Supabase persistence
