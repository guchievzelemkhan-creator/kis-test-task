import datetime
import sqlalchemy
from .db_session import Base
from sqlalchemy import orm

class Case(Base):
    __tablename__ = 'cases'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    guild_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('guilds.id'), nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)

    promised_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    deadline = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    status = sqlalchemy.Column(sqlalchemy.String, default='active')
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    # Связи
    guild = orm.relationship("Guild", back_populates="cases")
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