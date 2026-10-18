from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

__factory = None
Base = declarative_base()

def global_init(db_name):
    global __factory
    if not db_name.strip():
        return 'Имя пустое'
    if __factory:
        return
    conn_str = f"sqlite:///db/{db_name}?check_same_thread=False"
    engine = create_engine(conn_str)
    __factory = sessionmaker(bind=engine)
    from . import __all_models
    Base.metadata.create_all(engine)


def create_session():
    global __factory
    return __factory()