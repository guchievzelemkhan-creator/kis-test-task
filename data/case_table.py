import datetime
import sqlalchemy
from .db_session import Base
from sqlalchemy import orm

class Case(Base):
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
    
    
    @property
    def is_overdue(self):
        if self.status == 'active' and self.deadline:
            return self.deadline < datetime.datetime.now()
        return False

    @property
    def is_burning(self):
        if self.status == 'active' and self.deadline and not self.is_overdue:
            days_left = (self.deadline - datetime.datetime.now()).days
            return 0 <= days_left <= 3
        return False