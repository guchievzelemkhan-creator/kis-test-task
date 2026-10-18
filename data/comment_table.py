import datetime
import sqlalchemy
from .db_session import Base
from sqlalchemy import orm

class Comment(Base):
    __tablename__ = 'comments'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    case_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('cases.id'), nullable=False)
    text = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    case = orm.relationship("Case", back_populates="comments")