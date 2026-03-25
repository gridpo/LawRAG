import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.schemas.schemas import ChatRequest
from app.models.models import ChatSession, ChatMessage, User
from app.core.database import get_db
from app.services.rag_service import rag_engine
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/stream", summary="流式问答并保存历史")
async def chat_stream(
    request: ChatRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # 强制要求登录
):
    # 1. 处理会话逻辑
    if request.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id, 
            ChatSession.user_id == current_user.id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        # 创建新会话，取问题前10个字作标题
        session = ChatSession(title=request.query[:10], user_id=current_user.id)
        db.add(session)
        db.commit()
        db.refresh(session)

    # 2. 保存用户的提问到数据库
    user_msg = ChatMessage(session_id=session.id, role="user", content=request.query)
    db.add(user_msg)
    db.commit()

    # 3. RAG 检索
    retriever = rag_engine.get_retriever()
    retrieved_docs = retriever.invoke(request.query)
    
    sources = []
    for doc in retrieved_docs:
        # 获取原始路径，找不到就叫"未知"
        raw_path = doc.metadata.get("source") or doc.metadata.get("file_name") or "未知"
        # 通过切割斜杠，只拿最后的文件名 (比如把 /root/abc.pdf 变成 abc.pdf)
        clean_name = raw_path.split("/")[-1].split("\\")[-1]
        sources.append({"file_name": clean_name, "content": doc.page_content[:100]})
    
    # 构建上下文与提示词
    context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
    prompt = ChatPromptTemplate.from_template(
        "你是专业的法律助手，主攻劳动法和婚姻法。请严格根据以下【参考资料】回答问题。\n\n"
        "【重要指令】：\n"
        "1. 如果【参考资料】中能够解答用户的问题，请给出专业、详尽的回答。\n"
        "2. 如果用户的问题超出了【参考资料】的范围（比如问到了刑法、公司法等），**请不要自己编造答案**。你必须回答：『抱歉，我目前的知识库中暂未收录关于此问题的具体法律条文。您可以点击左侧【知识库管理】上传相关的法律文件，上传后我将立刻为您解答。』\n\n"
        "【参考资料】：\n{context}\n\n"
        "【用户问题】：{query}"
    )
    chain = prompt | rag_engine.llm | StrOutputParser()

    # 4. 生成流式响应并保存 AI 回答
    async def generate_stream():
        full_answer = ""
        # 抛出元数据（用于前端展示溯源角标和重定向 session_id）
        yield f"data: {json.dumps({'type': 'meta', 'session_id': session.id, 'sources': sources})}\n\n"
        
        # 抛出流式内容
        async for chunk in chain.astream({"context": context_text, "query": request.query}):
            full_answer += chunk
            yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"
            
        yield "data: [DONE]\n\n"
        
        # 流式传输结束后，将完整的 AI 回答存入数据库
        ai_msg = ChatMessage(session_id=session.id, role="assistant", content=full_answer)
        db.add(ai_msg)
        db.commit()

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.get("/sessions", summary="获取当前用户的会话列表")
def get_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 按 ID 倒序查询该用户的所有会话（最新的在最上面）
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.id.desc()).all()
    # 返回给前端
    return [{"id": s.id, "title": s.title, "time": "历史记录"} for s in sessions]

@router.get("/sessions/{session_id}/messages", summary="获取某个会话的历史消息")
def get_session_messages(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. 校验这个会话是不是当前用户的
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或无权限访问")
    
    # 2. 查询属于这个会话的所有消息，按先后顺序排列
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.id.asc()).all()
    return [{"role": m.role, "content": m.content} for m in messages]

@router.delete("/sessions/{session_id}", summary="删除会话")
def delete_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 级联安全删除：先删掉这个会话里的所有消息，再删掉会话本身
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"message": "删除成功"}