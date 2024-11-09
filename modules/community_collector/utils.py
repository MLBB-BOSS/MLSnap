# modules/community_collector/utils.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.community_collector.models import Base, Character
from modules.community_collector.data import HEROES
from config.settings import DATABASE_URL, logger

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    return SessionLocal()

def add_badge(user, badge_name):
    badges = user.badges.split(", ") if user.badges else []
    if badge_name not in badges:
        badges.append(badge_name)
        user.badges = ", ".join(badges)

def load_characters():
    session = get_session()
    existing_characters = session.query(Character).count()
    characters_data = []
    for role, characters in HEROES.items():
        for name in characters:
            characters_data.append({"name": name, "role": role})
    new_characters_added = False
    for char_data in characters_data:
        existing_char = session.query(Character).filter_by(name=char_data["name"]).first()
        if not existing_char:
            character = Character(name=char_data["name"], role=char_data["role"])
            session.add(character)
            new_characters_added = True
    if new_characters_added:
        session.commit()
        logger.info("Нові персонажі додані до бази даних")
    else:
        logger.info("Персонажі вже існують у базі даних")
    session.close()
