# SelfTracker
A full-stack book tracking app with a visual 3D bookshelf, personal reviews, reading stats, and AI-powered recommendations.

## Tech Stack
* Frontend - HTML + CSS + JS 
* Backend API - FastAPI
* Database - SQLAlchemy + SQLite
* Authorization - JWT (python-jose + bycrypt)
* Validation - Pydantic v2
* AI - Google AI 

## Features
- Authentication — Register & log in with JWT-secured sessions
- Visual Bookshelf — Books rendered as 3D CSS spines on a wooden shelf, colour-coded by status
- Full CRUD — Add, edit, delete books; update reading progress
- Reviews — Star ratings + written reviews per book
- Reading Stats — Pages read, completion rate, genre breakdown, average rating
- AI Recommendations — Google AI analyses users shelf and suggests their next read

## Project Structure

shelf-tracker/
├── app/
│   ├── main.py        # FastAPI app + all route handlers
│   ├── models.py      # SQLAlchemy ORM models (User, Book, Review)
│   ├── schemas.py     # Pydantic request/response schemas
│   ├── auth.py        # JWT creation & validation
│   └── database.py    # SQLAlchemy engine & session factory
├── static/
│   ├── css/styles.css
│   └── js/api.js      # Fetch wrapper + auth helpers
├── templates/
│   ├── login.html     # Login / signup page
│   ├── bookshelf.html # Main shelf with 3D book visualisation
│   ├── book.html      # Book detail, progress tracker & review editor
│   └── stats.html     # Reading stats + AI recommendations
├── requirements.txt
└── .env.example
```

### Side Notes
http://localhost:8000 — the SQLite database is created automatically on first run.

## API Reference

All endpoints are prefixed with `/api`. Authenticated routes require:
```
Authorization: Bearer <token>
```

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/signup` | Register a new user |
| `POST` | `/api/auth/login` | Log in, receive JWT |
| `GET` | `/api/users/me` | Get current user |

### Books
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/books` | List all books (optional `?status=` filter) |
| `POST` | `/api/books` | Add a book |
| `GET` | `/api/books/{id}` | Get a single book |
| `PUT` | `/api/books/{id}` | Update book details / progress |
| `DELETE` | `/api/books/{id}` | Remove from shelf |

### Reviews
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/books/{id}/review` | Get review for a book |
| `POST` | `/api/books/{id}/review` | Create or update review |

### Stats & AI
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/stats` | Aggregated reading stats |
| `POST` | `/api/recommendations` | AI book recommendations via Claude |

Interactive docs available at `http://localhost:8000/docs`.

## Key Design Decisions

- **SQLAlchemy ORM** with relationship-level cascades (`cascade="all, delete-orphan"`) keeps data consistent when books or users are deleted
- **Pydantic v2 validators** enforce business rules at the schema layer (e.g. status whitelist, rating range)
- **JWT stored in localStorage** on the client, attached as a Bearer token to every fetch request via the `api.js` wrapper
- **Spine width** is calculated from page count so thicker books appear wider on the shelf
- **Auto-timestamps** — `started_at` / `completed_at` are set server-side when status changes, removing client-side trust
