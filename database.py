"""Database models and setup for TDS Project 1."""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class Task(Base):
    """Table for tasks sent to students."""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    email = Column(String(255), nullable=False)
    task = Column(String(255), nullable=False)
    round = Column(Integer, nullable=False)
    nonce = Column(String(255), nullable=False, unique=True)
    brief = Column(Text, nullable=False)
    attachments = Column(JSON)
    checks = Column(JSON)
    evaluation_url = Column(String(512), nullable=False)
    endpoint = Column(String(512), nullable=False)
    statuscode = Column(Integer)
    secret = Column(String(255), nullable=False)


class Repo(Base):
    """Table for repos submitted by students."""
    __tablename__ = 'repos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    email = Column(String(255), nullable=False)
    task = Column(String(255), nullable=False)
    round = Column(Integer, nullable=False)
    nonce = Column(String(255), nullable=False)
    repo_url = Column(String(512), nullable=False)
    commit_sha = Column(String(255), nullable=False)
    pages_url = Column(String(512), nullable=False)


class Result(Base):
    """Table for evaluation results."""
    __tablename__ = 'results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    email = Column(String(255), nullable=False)
    task = Column(String(255), nullable=False)
    round = Column(Integer, nullable=False)
    repo_url = Column(String(512), nullable=False)
    commit_sha = Column(String(255), nullable=False)
    pages_url = Column(String(512), nullable=False)
    check = Column(Text, nullable=False)
    score = Column(Integer, nullable=False)
    reason = Column(Text)
    logs = Column(Text)


def get_engine():
    """Get database engine."""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///tds_project.db')
    return create_engine(database_url)


def get_session():
    """Get database session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """Initialize the database tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Database initialized successfully!")


if __name__ == '__main__':
    init_db()
