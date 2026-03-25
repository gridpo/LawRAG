# ⚖️ LawRAG - 基于检索增强生成的公益法律援助系统

![Vue.js](https://img.shields.io/badge/Vue.js-3.X-4FC08D?logo=vuedotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.2.X-1C3C3C)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

LawRAG 是一款专为法律维权场景设计的智能向导系统。通过结合 **GLM-4** 大模型的生成能力与基于 **ChromaDB** 的 RAG 架构，实现了法条精准检索、自动化回答及来源溯源，有效解决了法律咨询中的“模型幻觉”问题。

## ✨ 核心亮点

- **🔍 语义级动态切分**：针对法律条文逻辑严密的特性，采用基于语义的动态切片策略，而非固定长度切分，确保法条检索的上下文完整。
- **📑 引用溯源交互**：前端通过“抽屉式”组件展示引用来源，用户可直观查看 AI 回答所依据的原始法律 PDF 及其具体出处。
- **⚡ 流式响应体验**：基于 **FastAPI 异步架构** 与 **SSE** 协议，实现毫秒级首字响应（TTFT < 1.2s）。
- **📊 闭环自动化评测**：内置 `evaluate_rag.py` 评测框架，通过 **LLM-as-a-Judge** 对 60+ 真实维权案例进行召回率与准确率量化分析。

---

## 🛠️ 技术栈

- **后端**: FastAPI, LangChain, SQLAlchemy, Pydantic
- **AI**: 智谱 GLM-4 (LLM), Zhipu Embedding-3 (向量化)
- **数据库**: ChromaDB (向量库), SQLite (业务库)
- **前端**: Vue 3, Vite, Axios, Pinia

---

## 🚀 快速开始

### 1. 获取代码
```bash
git clone [https://github.com/gridpo/LawRAG.git](https://github.com/gridpo/LawRAG.git)
cd LawRAG

2. 后端部署
Bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows 下使用 venv\Scripts\activate
pip install -r requirements.txt
配置 .env 文件（必须）：
在 backend/ 目录下创建 .env，参考如下配置：

代码段
ZHIPU_API_KEY="你的智谱AI_API_KEY"
JWT_SECRET_KEY="自定义随机字符串用于Token加密"
DATABASE_URL="sqlite:///./data/lawrag.db"
启动后端：

Bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
后端启动后，可访问 http://localhost:8000/docs 查看 Swagger 接口文档。

3. 前端部署
Bash
cd src
npm install
配置前端环境：
在 src/ 目录下创建 .env，写入：

代码段
VITE_API_BASE_URL=http://localhost:8000
启动前端：

Bash
npm run dev
📂 目录结构说明
Plaintext
LawRAG/
├── backend/
│   ├── app/
│   │   ├── api/            # 接口路由 (Auth, Chat, KB)
│   │   ├── core/           # 核心配置 (Security, Config)
│   │   └── services/       # RAG 业务核心逻辑
│   ├── data/               # 数据库及向量库存储目录 (Git 已忽略)
│   ├── evaluate_rag.py     # 自动化评测脚本
│   └── .env.example        # 环境变量模板
├── src/                    # Vue3 前端源码
│   ├── api/                # Axios 请求封装
│   └── views/              # 页面级组件 (Chat, Login)
└── README.md