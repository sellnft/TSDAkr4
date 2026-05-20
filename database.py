from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from config import settings

DATABASE_URL = settings.get_db_url()

# Создаем синхронный движок для работы с базой данных
engine = create_engine(url=DATABASE_URL)
# Создаем фабрику сессий для взаимодействия с базой данных
SessionLocal = sessionmaker(engine, expire_on_commit=False)

# Базовый класс для всех моделей
class Base(DeclarativeBase):
    __abstract__ = True  # Класс абстрактный, чтобы не создавать отдельную таблицу для него