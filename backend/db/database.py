"""
資料庫連線設定 - 使用 SQLite + SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base  # 點 10: 從 sqlalchemy.orm 匯入

DATABASE_URL = "sqlite:///./finance.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI 依賴注入：取得資料庫 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
