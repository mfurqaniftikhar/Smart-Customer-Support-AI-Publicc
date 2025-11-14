# backend/db.py
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()  # loads .env in project root (make sure .env is in same folder or adjust path)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()

# Optional helper to get a session (can be imported in FastAPI Depends)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Small convenience function to test connection (callable from a script)
async def test_connection():
    try:
        async with engine.connect() as conn:
            # Use text() to wrap raw SQL
            await conn.execute(text("SELECT 1"))
        print("✅ Database connection OK:", DATABASE_URL)
    except Exception as e:
        print("❌ Database connection failed:", e)
        raise