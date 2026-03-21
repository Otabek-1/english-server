import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import ARRAY, JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set before importing database models")

engine = create_engine(
    url=DATABASE_URL,
    pool_pre_ping=True,
)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True)
    email = Column(String(100), unique=True)
    role = Column(String(10), default="user")

    password = Column(String(255), nullable=True)
    google_avatar = Column(String, nullable=True)
    premium_duration = Column(DateTime, nullable=True, default=None)

    notifications = relationship("Notification", back_populates="user")
    speaking_results = relationship("SpeakingResult", back_populates="user")
    ielts_submissions = relationship("IeltsSubmission", back_populates="user")
    password_reset_codes = relationship("PasswordResetCode", back_populates="user")


class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(128), nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True, default=None)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="password_reset_codes")


class SpeakingMock(Base):
    __tablename__ = "speaking_mocks"

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    questions = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow())

    results = relationship("SpeakingResult", back_populates="mock")


class SpeakingResult(Base):
    __tablename__ = "speaking_results"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mock_id = Column(Integer, ForeignKey("speaking_mocks.id"))
    recordings = Column(JSON)
    total_duration = Column(Integer)
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
    data = Column(JSON, nullable=False)
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
    part_1 = Column(ARRAY(String), nullable=False)
    part_2 = Column(ARRAY(String), nullable=False)
    part_3 = Column(ARRAY(String), nullable=False)
    part_4 = Column(ARRAY(String), nullable=False)
    part_5 = Column(ARRAY(String), nullable=False)
    part_6 = Column(ARRAY(String), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    mock = relationship("ListeningMock", back_populates="answers")


class Permissions(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    permissions = Column(JSON(String))


class Feedback(Base):
    __tablename__ = 'feedbacks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    rating = Column(Integer)
    text = Column(String)


class Submissions(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    section = Column(String)


class IeltsTest(Base):
    __tablename__ = "ielts_tests"

    id = Column(Integer, primary_key=True)
    title = Column(String(160), nullable=False)
    description = Column(String, nullable=True)
    exam_track = Column(String(20), nullable=False, default="academic")
    level = Column(String(20), nullable=True, default="Band 5-7")
    duration_minutes = Column(Integer, nullable=False, default=165)
    is_published = Column(Boolean, nullable=False, default=False)
    tags = Column(JSON, nullable=False, default=list)
    meta = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sections = relationship(
        "IeltsSection",
        back_populates="test",
        cascade="all, delete-orphan",
        order_by="IeltsSection.id",
    )
    submissions = relationship(
        "IeltsSubmission",
        back_populates="test",
        cascade="all, delete-orphan",
        order_by="IeltsSubmission.id.desc()",
    )


class IeltsSection(Base):
    __tablename__ = "ielts_sections"

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("ielts_tests.id", ondelete="CASCADE"), nullable=False)
    module = Column(String(20), nullable=False)
    title = Column(String(160), nullable=False)
    instructions = Column(String, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=30)
    content = Column(JSON, nullable=False, default=dict)
    answer_key = Column(JSON, nullable=False, default=list)
    order_index = Column(Integer, nullable=False, default=1)

    test = relationship("IeltsTest", back_populates="sections")


class IeltsSubmission(Base):
    __tablename__ = "ielts_submissions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(Integer, ForeignKey("ielts_tests.id", ondelete="CASCADE"), nullable=False)
    module = Column(String(20), nullable=False)
    answers = Column(JSON, nullable=False, default=list)
    score = Column(Integer, nullable=True)
    max_score = Column(Integer, nullable=True)
    band = Column(String(10), nullable=True)
    feedback = Column(JSON, nullable=False, default=dict)
    time_spent_seconds = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ielts_submissions")
    test = relationship("IeltsTest", back_populates="submissions")


class MockAttempt(Base):
    __tablename__ = "mock_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_type = Column(String(50), nullable=False, index=True)
    skill_area = Column(String(20), nullable=True, index=True)
    mock_id = Column(String(80), nullable=True)
    title = Column(String(180), nullable=True)
    route_path = Column(String(255), nullable=True)
    score = Column(Integer, nullable=True)
    max_score = Column(Integer, nullable=True)
    score_percent = Column(Integer, nullable=True)
    score_75 = Column(Integer, nullable=True)
    band = Column(String(20), nullable=True)
    status = Column(String(30), nullable=False, default="completed")
    attempt_meta = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MockProgress(Base):
    __tablename__ = "mock_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_type = Column(String(50), nullable=False, index=True)
    skill_area = Column(String(20), nullable=True, index=True)
    mock_id = Column(String(80), nullable=True)
    title = Column(String(180), nullable=True)
    route_path = Column(String(255), nullable=False)
    status = Column(String(30), nullable=False, default="active", index=True)
    remaining_seconds = Column(Integer, nullable=True)
    progress_state = Column(JSON, nullable=False, default=dict)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


AUTO_CREATE_DB = os.getenv("AUTO_CREATE_DB", "true").strip().lower() in {"1", "true", "yes", "on"}
if AUTO_CREATE_DB:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
