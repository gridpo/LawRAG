# ⚖️ LawRAG - 基于检索增强生成的公益法律援助系统

![Vue.js](https://img.shields.io/badge/Vue.js-3.X-4FC08D?logo=vuedotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.2.X-1C3C3C)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

LawRAG 是一个专为垂直法律领域打造的智能维权向导系统。本项目结合了大语言模型（LLM）的泛化生成能力与检索增强生成（RAG）的精准事实核查能力，旨在解决法律咨询场景下大模型易产生的“幻觉”问题，为用户提供精准、可溯源的法律援助建议。

## ✨ 核心特性 (Core Features)

- **🔍 语义级精准检索**：基于 ChromaDB 向量数据库，摒弃传统的固定长度切分，采用针对法律文本优化的动态语义切块（Chunking）策略，有效保持法条上下文完整性。
- **📑 法条级精准溯源**：独创“法条溯源抽屉”前端交互，用户可一键查看 AI 回答所引用的原始法律条文（PDF/TXT）及其具体出处，保障法律咨询的严肃性与可信度。
- **⚡ 流式极速响应**：后端基于 FastAPI 异步架构，前端对接 SSE (Server-Sent Events) 协议，实现“打字机”式流式输出，有效降低 TTFT（首字响应时间）至 1.2s 以内。
- **🛡️ 生产级安全防护**：全面采用 `.env` 环境变量进行敏感信息隔离；接口层集成 JWT 鉴权与防 SQL/Prompt 注入拦截机制。
- **📊 自动化测评闭环**：内置基于 `LLM-as-a-Judge` 的自动化测评框架，针对 60+ 真实维权案例进行多维指标量化评估（响应耗时、Top-K 召回率、幻觉率）。

## 🛠️ 技术栈 (Tech Stack)

### 核心 AI 链路
* **大模型引擎**: 智谱 GLM-4 
* **RAG 编排框架**: LangChain
* **向量数据库**: ChromaDB (本地持久化) / FAISS
* **文本嵌入模型 (Embedding)**: Zhipu Embedding-3

### 后端 (Backend)
* **Web 框架**: FastAPI (Python 3.10+)
* **关系型数据库**: SQLite + SQLAlchemy ORM
* **鉴权机制**: JWT (JSON Web Tokens) + bcrypt 密码哈希

### 前端 (Frontend)
* **核心框架**: Vue 3 (Composition API) + Vite
* **网络请求**: Axios (支持多环境 baseURL 切换)
* **状态管理**: Vuex / Pinia

---

## 🚀 快速开始 (Quick Start)

### 1. 环境准备
请确保您的本地已安装 [Python 3.10+](https://www.python.org/) 和 [Node.js 18+](https://nodejs.org/)。

克隆本仓库：
```bash
git clone [https://github.com/gridpo/LawRAG.git](https://github.com/你的账号/gridpo.git)
cd LawRAG