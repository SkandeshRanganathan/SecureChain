from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os


# PostgreSQL connection URL.
# Example:
# postgresql+psycopg2://user:password@localhost:5432/securechain
DATABASE_URL = os.getenv(
    "SECURECHAIN_DATABASE_URL",
    "postgresql+psycopg2://postgres:parvathy83@localhost:5432/securechain",
)


engine = create_engine(DATABASE_URL, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

