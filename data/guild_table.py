import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import Base


class Guild(Base):
    __tablename__ = 'guilds'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)

    cases = orm.relationship("Case", back_populates="guild", cascade="all, delete-orphan")

    def __str__(self):
        return self.name