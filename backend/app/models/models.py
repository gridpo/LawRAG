from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    avatar = Column(String, default="default_avatar.png")  # 对应文档: 用户头像
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系：一个用户可以有多个对话会话
    sessions = relationship("ChatSession", back_populates="owner", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="新对话")              # 对应文档: 对话重命名
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="sessions")
    # 关系：一个会话包含多条消息
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)                                  # "user" 或 "assistant"，对应文档: 区分提问和回答
    content = Column(Text)                                 # 消息内容
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")

class LawDocument(Base):
    __tablename__ = "law_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # 关联用户，保证数据隔离
    filename = Column(String, index=True)             # 文件原始名称 (如: 劳动法.pdf)
    file_path = Column(String)                        # 文件在服务器上的物理存储路径
    status = Column(String, default="processing")     # 向量化状态: processing(处理中), completed(已完成), failed(失败)
    created_at = Column(DateTime, default=datetime.utcnow) # 上传时间

    # 建立与 User 表的关系 (可选，方便连表查询)
    user = relationship("User", backref="documents")