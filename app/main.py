"""
Shelf Tracker – FastAPI Backend
================================
Tech: FastAPI · SQLAlchemy · Pydantic · JWT · GEMINI API
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import json
import os

from dotenv import load_dotenv
load_dotenv()

from .database import engine, get_db, Base
from . import models, schemas
from .auth import (
    hash_password, verify_password,
    create_access_token, get_current_user,
)

# ─── App bootstrap ───────────────────────────────────────────────────────────

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Shelf Tracker API",
    description="Track your reading life with a beautiful virtual bookshelf.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ─── Helper: assign shelf cover colour ───────────────────────────────────────

_COLORS = [
    "#7B2D2D", "#2D4A7B", "#2D7B4A", "#6B2D7B",
    "#7B5A2D", "#2D7B7B", "#7B2D5A", "#4A4A7B",
    "#5A7B2D", "#7B3D2D", "#2D5A7B", "#7B6B2D",
]


def _next_color(db: Session, user_id: int) -> str:
    count = db.query(func.count(models.Book.id)).filter(
        models.Book.user_id == user_id
    ).scalar()
    return _COLORS[count % len(_COLORS)]


def _spine_width(pages: Optional[int]) -> int:
    """Map page count to spine pixel width (30–55 px)."""
    if not pages:
        return 38
    return max(30, min(55, 30 + pages // 30))


# ─── Auth routes ─────────────────────────────────────────────────────────────

@app.post("/api/auth/signup", response_model=schemas.Token, tags=["auth"])
def signup(body: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user and return a JWT."""
    if db.query(models.User).filter(models.User.email == body.email).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")
    if db.query(models.User).filter(models.User.username == body.username).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already taken")

    user = models.User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.Token(
        access_token=create_access_token(user.id),
        username=user.username,
    )


@app.post("/api/auth/login", response_model=schemas.Token, tags=["auth"])
def login(body: schemas.UserLogin, db: Session = Depends(get_db)):
    """Authenticate and return a JWT."""
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return schemas.Token(
        access_token=create_access_token(user.id),
        username=user.username,
    )


@app.get("/api/users/me", response_model=schemas.UserResponse, tags=["auth"])
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# ─── Book routes ─────────────────────────────────────────────────────────────

@app.get("/api/books", response_model=List[schemas.BookResponse], tags=["books"])
def list_books(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return all books on the authenticated user's shelf, optionally filtered by status."""
    q = db.query(models.Book).filter(models.Book.user_id == current_user.id)
    if status:
        q = q.filter(models.Book.status == status)
    return q.order_by(models.Book.added_at.desc()).all()


@app.post("/api/books", response_model=schemas.BookResponse, status_code=status.HTTP_201_CREATED, tags=["books"])
def add_book(
    body: schemas.BookCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Add a new book to the shelf."""
    book = models.Book(
        user_id=current_user.id,
        title=body.title,
        author=body.author,
        genre=body.genre,
        isbn=body.isbn,
        status=body.status,
        pages=body.pages,
        current_page=body.current_page,
        cover_color=body.cover_color or _next_color(db, current_user.id),
        spine_width=_spine_width(body.pages),
        started_at=datetime.utcnow() if body.status == "reading" else None,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@app.get("/api/books/{book_id}", response_model=schemas.BookResponse, tags=["books"])
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    book = db.query(models.Book).filter(
        models.Book.id == book_id,
        models.Book.user_id == current_user.id,
    ).first()
    if not book:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    return book


@app.put("/api/books/{book_id}", response_model=schemas.BookResponse, tags=["books"])
def update_book(
    book_id: int,
    body: schemas.BookUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update book details or reading progress."""
    book = db.query(models.Book).filter(
        models.Book.id == book_id,
        models.Book.user_id == current_user.id,
    ).first()
    if not book:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")

    update_data = body.model_dump(exclude_unset=True)

    # Auto-set timestamps when status changes
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == "reading" and book.status != "reading":
            update_data.setdefault("started_at", datetime.utcnow())
        if new_status == "completed" and book.status != "completed":
            update_data.setdefault("completed_at", datetime.utcnow())
            if book.pages:
                update_data.setdefault("current_page", book.pages)

    # Recalculate spine width if pages change
    if "pages" in update_data:
        update_data["spine_width"] = _spine_width(update_data["pages"])

    for field, value in update_data.items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)
    return book


@app.delete("/api/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["books"])
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    book = db.query(models.Book).filter(
        models.Book.id == book_id,
        models.Book.user_id == current_user.id,
    ).first()
    if not book:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    db.delete(book)
    db.commit()


# ─── Review routes ───────────────────────────────────────────────────────────

@app.get("/api/books/{book_id}/review", response_model=Optional[schemas.ReviewResponse], tags=["reviews"])
def get_review(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Review).filter(
        models.Review.book_id == book_id,
        models.Review.user_id == current_user.id,
    ).first()


@app.post("/api/books/{book_id}/review", response_model=schemas.ReviewResponse, tags=["reviews"])
def upsert_review(
    book_id: int,
    body: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create or update a review. Also syncs the rating on the book itself."""
    book = db.query(models.Book).filter(
        models.Book.id == book_id,
        models.Book.user_id == current_user.id,
    ).first()
    if not book:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")

    # Keep book.rating in sync with review rating
    book.rating = body.rating

    review = db.query(models.Review).filter(
        models.Review.book_id == book_id,
        models.Review.user_id == current_user.id,
    ).first()

    if review:
        review.content = body.content
        review.rating = body.rating
    else:
        review = models.Review(
            book_id=book_id,
            user_id=current_user.id,
            content=body.content,
            rating=body.rating,
        )
        db.add(review)

    db.commit()
    db.refresh(review)
    return review


# ─── Stats route ─────────────────────────────────────────────────────────────

@app.get("/api/stats", response_model=schemas.StatsResponse, tags=["stats"])
def get_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    books = db.query(models.Book).filter(models.Book.user_id == current_user.id).all()

    completed = [b for b in books if b.status == "completed"]
    reading = [b for b in books if b.status == "reading"]
    want = [b for b in books if b.status == "want_to_read"]

    rated = [b for b in completed if b.rating is not None]
    avg_rating = round(sum(b.rating for b in rated) / len(rated), 2) if rated else None

    total_pages = sum(b.pages or 0 for b in completed)

    genre_counts: dict[str, int] = {}
    for b in books:
        if b.genre:
            genre_counts[b.genre] = genre_counts.get(b.genre, 0) + 1

    genres = [schemas.GenreCount(genre=g, count=c) for g, c in
              sorted(genre_counts.items(), key=lambda x: -x[1])]

    completion_rate = round(len(completed) / len(books) * 100, 1) if books else 0.0

    return schemas.StatsResponse(
        total_books=len(books),
        completed=len(completed),
        reading=len(reading),
        want_to_read=len(want),
        total_pages_read=total_pages,
        average_rating=avg_rating,
        genres=genres,
        completion_rate=completion_rate,
    )


# ─── AI Recommendations ──────────────────────────────────────────────────────

@app.post("/api/recommendations", response_model=schemas.RecommendationsResponse, tags=["ai"])
async def get_recommendations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    import google.generativeai as genai
    import os

    books = db.query(models.Book).filter(models.Book.user_id == current_user.id).all()
    if not books:
        return schemas.RecommendationsResponse(recommendations=[])

    shelf_summary = "\n".join(
        f"- \"{b.title}\" by {b.author} | Genre: {b.genre or 'Unknown'} | Status: {b.status}"
        for b in books
    )

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(
        "You are a librarian. Based on this reading list, recommend exactly 5 books.\n\n"
        f"{shelf_summary}\n\n"
        "Respond ONLY with a valid JSON array:\n"
        '[{"title":"...", "author":"...", "genre":"...", "reason":"..."}]'
    )

    try:
        data = json.loads(response.text.strip())
        recs = [schemas.BookRecommendation(**item) for item in data[:5]]
    except Exception:
        recs = []

    return schemas.RecommendationsResponse(recommendations=recs)

# ─── Frontend routes ─────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def index():
    return FileResponse("templates/login.html")

@app.get("/bookshelf", include_in_schema=False)
def bookshelf():
    return FileResponse("templates/bookshelf.html")

@app.get("/book/{book_id}", include_in_schema=False)
def book_detail(book_id: int):
    return FileResponse("templates/book.html")

@app.get("/stats", include_in_schema=False)
def stats_page():
    return FileResponse("templates/stats.html")
