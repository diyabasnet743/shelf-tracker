from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ─── Auth ────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, hyphens and underscores")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


# ─── Books ───────────────────────────────────────────────────────────────────

VALID_STATUSES = {"want_to_read", "reading", "completed"}
COVER_COLORS = [
    "#7B2D2D", "#2D4A7B", "#2D7B4A", "#6B2D7B",
    "#7B5A2D", "#2D7B7B", "#7B2D5A", "#4A4A7B",
    "#5A7B2D", "#7B3D2D", "#2D5A7B", "#7B6B2D",
]


class BookCreate(BaseModel):
    title: str
    author: str
    genre: Optional[str] = None
    isbn: Optional[str] = None
    status: str = "want_to_read"
    pages: Optional[int] = None
    current_page: int = 0
    cover_color: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return v


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    status: Optional[str] = None
    pages: Optional[int] = None
    current_page: Optional[int] = None
    rating: Optional[float] = None
    cover_color: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return v

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 <= v <= 5):
            raise ValueError("Rating must be between 0 and 5")
        return v


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    genre: Optional[str]
    isbn: Optional[str]
    status: str
    pages: Optional[int]
    current_page: int
    rating: Optional[float]
    cover_color: str
    spine_width: int
    progress_pct: float
    added_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ─── Reviews ─────────────────────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    content: str
    rating: float

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: float) -> float:
        if not (0 <= v <= 5):
            raise ValueError("Rating must be between 0 and 5")
        return v

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("Review must be at least 10 characters")
        return v


class ReviewResponse(BaseModel):
    id: int
    content: str
    rating: float
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ─── Stats ───────────────────────────────────────────────────────────────────

class GenreCount(BaseModel):
    genre: str
    count: int


class StatsResponse(BaseModel):
    total_books: int
    completed: int
    reading: int
    want_to_read: int
    total_pages_read: int
    average_rating: Optional[float]
    genres: List[GenreCount]
    completion_rate: float


# ─── Recommendations ─────────────────────────────────────────────────────────

class BookRecommendation(BaseModel):
    title: str
    author: str
    genre: str
    reason: str


class RecommendationsResponse(BaseModel):
    recommendations: List[BookRecommendation]
