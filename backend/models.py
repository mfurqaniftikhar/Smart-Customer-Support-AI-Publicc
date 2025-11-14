# backend/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.db import Base  # ✅ FIXED: Added 'backend.' prefix

# -------------------------
# User Model
# -------------------------
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=True)  # optional: store hashed passwords
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    conversations = relationship("Conversation", back_populates="user")

# -------------------------
# Lead Model
# -------------------------
class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100))
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# -------------------------
# Conversation Model
# -------------------------
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # foreign key to User
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    username = Column(String(100), index=True)  # for quick filtering without needing a full join
    
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to User
    user = relationship("User", back_populates="conversations")

# -------------------------
# Knowledge Base Model
# -------------------------
class KBDocument(Base):
    __tablename__ = "kb_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    content = Column(Text)
    embedding = Column(Text)  # JSON list of numbers as string
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# -------------------------
# Order Model (NEW)
# -------------------------
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    address = Column(Text, nullable=False)
    house_number = Column(String(50))
    product_details = Column(Text, nullable=False)
    additional_notes = Column(Text)
    status = Column(String(50), default="pending")  # pending, processing, completed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())