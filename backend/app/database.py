from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.db_connect import create_db_engine


class Base(DeclarativeBase):
    pass


engine = create_db_engine(pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
