from pydantic import BaseModel, EmailStr
from typing import List, Optional

# ================= Auth 相关 =================
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    avatar: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# ================= Chat 相关 =================
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[int] = None  # 改为 int，对应数据库中的 ChatSession ID

class SourceItem(BaseModel):
    file_name: str
    content: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = []