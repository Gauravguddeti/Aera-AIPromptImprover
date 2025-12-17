# Aera Backend

Backend API for the Aera AI Prompt Enhancement Tool.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install in development mode:
```bash
pip install -e .
```

## Development

Run the development server:
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Testing

Run tests:
```bash
pytest
```

Run specific test categories:
```bash
pytest -m contract    # Contract tests
pytest -m integration # Integration tests  
pytest -m unit        # Unit tests
```

## Code Quality

Format code:
```bash
black src tests
isort src tests
```

Lint code:
```bash
flake8 src tests
mypy src
```

## API Documentation

When the server is running, view API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc