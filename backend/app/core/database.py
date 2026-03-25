import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 这里的修改：不仅导入 settings，还要把全局变量 BASE_DIR 也导入进来
from app.core.config import settings, BASE_DIR

# 这里的修改：把 settings.BASE_DIR 改成直接使用 BASE_DIR
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'lawrag.db')}"

# connect_args={"check_same_thread": False} 是 SQLite 在 FastAPI 中必须的配置
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 依赖项：用于在路由中获取数据库会话 (Dependency Injection)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()