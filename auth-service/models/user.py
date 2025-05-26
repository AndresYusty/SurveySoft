from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default='user')
    email = Column(String(120), unique=True, nullable=True)
    reset_token = Column(String(100), unique=True, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
