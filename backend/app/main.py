from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI(title="RAG System API", version="1.0")

# 开发环境允许本地，生产环境只允许指定域名
ENVIRONMENT = os.getenv("ENV", "development")
if ENVIRONMENT == "development":
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
else:
    # 线上部署时替换为你的前端域名
    ALLOWED_ORIGINS = [
        "https://your-domain.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- 你的路由 -------------------
# app.include_router(...)
# 这里保持你原来的代码不变