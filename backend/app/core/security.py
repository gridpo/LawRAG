from datetime import datetime, timedelta, timezone # 导入 timezone
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings  # 确保导入了 settings 

# 直接从配置中读取，杜绝硬编码 
SECRET_KEY = settings.JWT_SECRET_KEY 
ALGORITHM = settings.ALGORITHM
# 建议这里也使用 settings 中的过期时间配置
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """校验密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """生成密码哈希"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """生成 JWT Token"""
    to_encode = data.copy()
    
    # 修正：使用现代化的 UTC 获取方式 
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    # 使用配置好的密钥和算法 
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt