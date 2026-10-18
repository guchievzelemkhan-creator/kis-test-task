import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm

class Case(SqlAlchemyBase):
    __tablename__ = 'cases'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    guild = sqlalchemy.Column(sqlalchemy.String, nullable=False)  # Кто просил (Гильдия)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)  # Суть обещания
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)  # Подробности
    promised_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)  # Когда обещано
    deadline = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)  # Когда должно быть завершено
    status = sqlalchemy.Column(sqlalchemy.String, default='active')  # active / closed
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    comments = orm.relationship("Comment", back_populates="case", cascade="all, delete-orphan")