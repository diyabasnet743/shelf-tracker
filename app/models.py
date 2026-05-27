from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """Represents a registered user of the application."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    books = relationship("Book", back_populates="owner", cascade="all, delete-orphan")


class Book(Base):
    """
    Represents a book on a user's shelf.
    Status values: 'want_to_read' | 'reading' | 'completed'
    """
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=False)
    genre = Column(String(100), nullable=True)
    isbn = Column(String(20), nullable=True)

    status = Column(String(20), nullable=False, default="want_to_read")
    pages = Column(Integer, nullable=True)
    current_page = Column(Integer, default=0)
    rating = Column(Float, nullable=True)

    # Visual representation on the shelf
    cover_color = Column(String(7), nullable=False, default="#8B4513")
    spine_width = Column(Integer, default=38)  # px – thicker = more pages

    added_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="books")
    review = relationship("Review", back_populates="book", uselist=False, cascade="all, delete-orphan")

    @property
    def progress_pct(self) -> float:
        """Reading progress as a 0-100 percentage."""
        if not self.pages or self.pages == 0:
            return 0.0
        return round((self.current_page / self.pages) * 100, 1)


class Review(Base):
    """A user's written review of a book."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    content = Column(Text, nullable=False)
    rating = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    book = relationship("Book", back_populates="review")
