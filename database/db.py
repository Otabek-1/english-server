from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, ARRAY, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

engine = create_engine(url="postgresql://postgres.nipiecblbunczdlyrbfq:Ibr0him$!@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres")
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


Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()