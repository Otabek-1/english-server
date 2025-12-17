import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, func, ForeignKey, ARRAY, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

load_dotenv()

engine = create_engine(url=os.getenv("DATABASE_URL"))
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True)
    email = Column(String(100), unique=True)
    role = Column(String(10), default="user")  # admin / user
    password = Column(String(255))
    premium_duration = Column(DateTime, nullable=True, default=None)
    notifications = relationship("Notification", back_populates="user")
    speaking_results = relationship("SpeakingResult", back_populates="user")


class SpeakingMock(Base):
    __tablename__ = "speaking_mocks"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100))  # Mock 1, Mock 2, etc.
    questions = Column(JSON)  # 8ta question: {1.1: [...], 1.2: [...], 2: [...], 3: [...]}
    created_at = Column(DateTime, default=datetime.utcnow())
    
    results = relationship("SpeakingResult", back_populates="mock")


class SpeakingResult(Base):
    __tablename__ = "speaking_results"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mock_id = Column(Integer, ForeignKey("speaking_mocks.id"))
    recordings = Column(JSON)  # {q1: url, q2: url, q3: url, ..., q8: url}
    total_duration = Column(Integer)  # total exam duration in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="speaking_results")
    mock = relationship("SpeakingMock", back_populates="results")


class ReadingMockQuestion(Base):
    __tablename__ = "reading_questions"

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    part1 = Column(JSON(String))
    part2 = Column(JSON(String))
    part3 = Column(JSON(String))
    part4 = Column(JSON(String))
    part5 = Column(JSON(String))
    created_at = Column(DateTime, default=datetime.utcnow())

    answers = relationship("ReadingMockAnswer", back_populates="question", uselist=False)


class ReadingMockAnswer(Base):
    __tablename__ = "reading_mocks"

    id = Column(Integer, primary_key=True)
    part1 = Column(ARRAY(String))
    part2 = Column(ARRAY(String))
    part3 = Column(ARRAY(String))
    part4 = Column(ARRAY(String))
    part5 = Column(ARRAY(String))
    question_id = Column(Integer, ForeignKey("reading_questions.id"))

    question = relationship("ReadingMockQuestion", back_populates="answers")


class WritingMock(Base):
    __tablename__ = "writing_mocks"

    id = Column(Integer, primary_key=True)
    images = Column(ARRAY(String), default=[])
    task1 = Column(JSON(String))
    task2 = Column(JSON(String))
    created_at = Column(DateTime, default=datetime.utcnow())


class WritingResult(Base):
    __tablename__ = "writing_results"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    mock_id = Column(Integer)
    task1 = Column(String)
    task2 = Column(String)
    result = Column(JSON(String), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")


class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    body = Column(String)
    slug = Column(String)
    reactions = Column(JSON(String))
    created_at = Column(DateTime(timezone=True), default=func.now())


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()