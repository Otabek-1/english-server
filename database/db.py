import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, func, ForeignKey, ARRAY, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

load_dotenv()

# Session Model import qilish
# (Session modelni database.session_model dan import qilgin kerak)

engine = create_engine(url=os.getenv("DATABASE_URL"))
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True)
    email = Column(String(100), unique=True)
    role = Column(String(10), default="user")

    password = Column(String(255), nullable=True)   # Google userlarda NULL bo‘ladi
    google_avatar = Column(String, nullable=True)

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


class news(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    body = Column(String)
    slug = Column(String)
    reactions = Column(JSON(String))
    created_at = Column(DateTime(timezone=True), default=func.now())
    
class ListeningMock(Base):
    __tablename__ = "listening_mocks"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)

    # === SAVOLLAR DATA ===
    data = Column(JSON, nullable=False)
    # bu yerga SEN BERGAN `data` object 1:1 tushadi

    # === AUDIO URLS (HAR PART UCHUN ALOHIDA) ===
    audio_part_1 = Column(String, nullable=True)
    audio_part_2 = Column(String, nullable=True)
    audio_part_3 = Column(String, nullable=True)
    audio_part_4 = Column(String, nullable=True)
    audio_part_5 = Column(String, nullable=True)
    audio_part_6 = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    answers = relationship(
        "ListeningMockAnswer",
        back_populates="mock",
        uselist=False
    )

class ListeningMockAnswer(Base):
    __tablename__ = "listening_mock_answers"

    id = Column(Integer, primary_key=True)
    mock_id = Column(
        Integer,
        ForeignKey("listening_mocks.id", ondelete="CASCADE"),
        unique=True
    )

    # === PART 1 (1–8) ===
    part_1 = Column(ARRAY(String), nullable=False)
    # ["A", "C", "B", "A", "C", "B", "A", "C"]

    # === PART 2 (9–14) ===
    part_2 = Column(ARRAY(String), nullable=False)
    # ["Saturday", "two", "director", "three", "15", "online"]

    # === PART 3 (15–18) ===
    part_3 = Column(ARRAY(String), nullable=False)
    # ["A", "C", "F", "B"]

    # === PART 4 (19–23) ===
    part_4 = Column(ARRAY(String), nullable=False)
    # ["C", "A", "D", "B", "E"]

    # === PART 5 (24–29) ===
    part_5 = Column(ARRAY(String), nullable=False)
    # ["workman and customer", "has a change of mind", ...]

    # === PART 6 (30–35) ===
    part_6 = Column(ARRAY(String), nullable=False)
    # ["universal", "remove", "evidence", "claim", "gesture", "symbol"]

    created_at = Column(DateTime, default=datetime.utcnow)

    mock = relationship("ListeningMock", back_populates="answers")

class Permissions(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer,ForeignKey("users.id",ondelete="CASCADE"))
    
    permissions = Column(JSON(String))

# Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()