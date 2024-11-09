from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, LargeBinary, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from config.settings import DATABASE_URL

# Налаштування бази даних
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Асоціативна таблиця для зв’язку багато-до-багатьох між користувачами та тегами
user_tags = Table(
    'user_tags',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.user_id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=False, nullable=False)
    badges = Column(String, default="")
    tags = relationship("Tag", secondary=user_tags, back_populates="users")
    contributions = relationship("Contribution", back_populates="user")
    screenshots = relationship("Screenshot", back_populates="user")

class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("User", secondary=user_tags, back_populates="tags")

class Character(Base):
    __tablename__ = 'characters'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, nullable=False)
    screenshots = relationship("Screenshot", back_populates="character")

class Contribution(Base):
    __tablename__ = 'contributions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    character_id = Column(Integer, ForeignKey('characters.id'))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user = relationship("User", back_populates="contributions")
    character = relationship("Character")

class Screenshot(Base):
    __tablename__ = 'screenshots'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    character_id = Column(Integer, ForeignKey('characters.id'))
    image_data = Column(LargeBinary, nullable=False)
    image_hash = Column(String, nullable=False, unique=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user = relationship("User", back_populates="screenshots")
    character = relationship("Character", back_populates="screenshots")

# Експортуємо необхідні змінні та класи
__all__ = ['Base', 'engine', 'SessionLocal', 'User', 'Tag', 'Character', 'Contribution', 'Screenshot']
