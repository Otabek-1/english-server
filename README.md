# MockStream Backend

FastAPI backend for the MockStream English exam-prep platform.

## Stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- Google OAuth
- Mailjet
- Supabase

## Setup

1. Copy `.env.example` to `.env`
2. Fill at least:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `REFRESH_SECRET_KEY`
   - `SESSION_SECRET_KEY`
3. Normalize dependencies file if needed:

```bash
python fix_requirements_encoding.py
```

4. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

5. Run the server:

```bash
python -m uvicorn main:app --reload
```

## Verification

Syntax check:

```bash
python -m compileall .
```

Dependency file check:

```bash
python fix_requirements_encoding.py
```

Health endpoints:

- `GET /health`
- `GET /health/ready`

## Notes

- `AUTO_CREATE_DB=true` creates tables on startup/import. Turn it off in stricter deploy flows.
- `CORS_ALLOWED_ORIGINS` accepts a comma-separated list.
- Speaking uploads require Supabase credentials.
- Mail/contact and password reset require Mailjet credentials.
