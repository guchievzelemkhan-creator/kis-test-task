import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm

class Comment(SqlAlchemyBase):
    __tablename__ = 'comments'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    case_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('cases.id'))
    text = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)  # Метка времени

    # Обратная связь
    case = orm.relationship("Comment", back_populates="comments")