from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

import os
import json
from app.schemas.schemas import ChatRequest
from app.services.rag_service import rag_engine
from app.core.config import settings

router = APIRouter()

# ================= 知识库管理接口 =================
@router.post("/kb/upload", summary="上传文件至知识库")
async def upload_file(file: UploadFile = File(...)):
    """文件上传与管理 [cite: 14, 15]"""
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # 处理文件并入库
    chunk_count = rag_engine.process_and_store_file(file_path, file.filename)
    
    return {
        "status": "success", 
        "message": f"文件 {file.filename} 上传并处理成功",
        "chunks": chunk_count  # 显示文件的分块状态 [cite: 17]
    }

# ================= 对话交互接口 =================
@router.post("/chat", summary="流式问答接口")
async def chat_stream(request: ChatRequest):
    """大语言模型集成，接收提示词并接收流式回复 [cite: 40]"""
    
    # 1. 检索相似文档 [cite: 34]
    retriever = rag_engine.get_retriever()
    retrieved_docs = retriever.invoke(request.query)
    
    # 提取来源用于溯源展示 [cite: 18, 20]
    sources = [
        {"file_name": doc.metadata.get("file_name", "未知"), "content": doc.page_content[:100]}
        for doc in retrieved_docs
    ]
    
    # 2. 构建提示词模板 [cite: 38]
    context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
    prompt = ChatPromptTemplate.from_template(
        "你是专业的助手。请根据以下参考资料回答问题。\n\n"
        "参考资料：\n{context}\n\n"
        "问题：{query}\n"
        "回答要求：如果资料中没有相关信息，请明确告知。"
    )
    
    # 3. 构建 LangChain LCEL 链
    chain = prompt | rag_engine.llm | StrOutputParser()

    # 4. 生成流式响应生成器 
    async def generate_stream():
        # 首先发送检索到的来源信息（前端可以用来做角标和抽屉 [cite: 19, 20]）
        yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"
        
        # 流式返回 LLM 生成的 token
        async for chunk in chain.astream({"context": context_text, "query": request.query}):
            yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"
            
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")