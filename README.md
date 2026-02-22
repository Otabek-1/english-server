# Backend structure & plan English site.

## Setup

Copy `.env.example` to `.env` and set at least:
- `DATABASE_URL`, `SECRET_KEY`, `REFRESH_SECRET_KEY`, `SESSION_SECRET_KEY`
- CORS ochiq (*) — public route'lar (gTTS va b.) boshqa loyihalardan ishlatiladi
- `KEY_PASSWORD` if using Gemini features (must match client `VITE_GEMINI_KEY_PASSWORD`)

## Texnologiyalar:
 - FastAPI
 - sqlalchemy (PosgreSQL)
 - OAuth2 (Google)

## Features:
 - Login/Register
 - Take mocks/exams/tests
 - Level / gamification
 - Email notification
 - Role (admin/user)

part 4:
 - tfn => True False Not given
 - ynn => Yes No Not given