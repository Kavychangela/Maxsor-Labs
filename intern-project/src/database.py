from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./support_tickets.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

Base = declarative_base()

sessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()