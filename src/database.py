from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
import uuid
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import Config

Base = declarative_base()

# Enable connection pooling/pre-ping to fix the SSL/Neon disconnect issue
engine = create_engine(
    Config.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- MODELS ---

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    name = Column(String, default="New Session") 
    
    # NEW: Store reports directly in the session so they persist
    overview_report = Column(Text, nullable=True)
    risk_report = Column(Text, nullable=True)

    contracts = relationship("Contract", back_populates="session", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    filename = Column(String)
    content = Column(Text)
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="contracts")

class ChatMessage(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String) 
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="messages")

# --- HELPER FUNCTIONS ---

def get_session_details(session_id):
    db = SessionLocal()
    session = db.query(Session).filter(Session.id == session_id).first()
    db.close()
    return session

def update_session_name(session_id, new_name):
    db = SessionLocal()
    session = db.query(Session).filter(Session.id == session_id).first()
    if session:
        session.name = new_name
        db.commit()
    db.close()

def save_session_reports(session_id, overview=None, risks=None):
    db = SessionLocal()
    session = db.query(Session).filter(Session.id == session_id).first()
    if session:
        if overview:
            session.overview_report = overview
        if risks:
            session.risk_report = risks
        db.commit()
    db.close()

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()