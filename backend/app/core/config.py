import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=dotenv_path)  

class Settings(BaseSettings):
    
    # JWT 配置：从 .env 读取，若无则报错
    JWT_SECRET_KEY: str = Field(default="", env="JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 

    # 数据库配置：统一从这里读取
    DATABASE_URL: str = Field(default="sqlite:///./data/lawrag.db")

    def model_post_init(self, __context):
        if not self.ZHIPU_API_KEY:
            raise ValueError("❌ 缺失 ZHIPU_API_KEY")
        if not self.JWT_SECRET_KEY:
            print("⚠️ 警告：JWT_SECRET_KEY 为空，请检查 .env 文件！")

# 创建全局实例
settings = Settings()

# 3. 确保文件夹存在（这里使用绝对路径，更稳健）
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)