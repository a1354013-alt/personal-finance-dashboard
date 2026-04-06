"""
資料庫連線配置
使用 SQLAlchemy 建立 SQLite 連線與 Session 管理。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite 資料庫檔案路徑
DATABASE_URL = "sqlite:///./finance.db"

# 建立資料庫引擎
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# 建立 Session 類別
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立模型基底類別
Base = declarative_base()

# 依賴注入：取得資料庫 Session
def get_db():
    """FastAPI 依賴注入：取得資料庫 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
