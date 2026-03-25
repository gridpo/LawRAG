import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, LawDocument
from app.services.rag_service import rag_engine

router = APIRouter()

# 确保存放 PDF 的临时目录存在
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 这是一个后台任务：因为处理 PDF 和请求大模型非常慢，不能让前端一直转圈等待
def process_document_task(doc_id: int, file_path: str, db: Session):
    try:
        # 1. 呼叫 RAG 引擎开始学习这篇文档
        rag_engine.add_document(file_path)
        
        # 2. 学习成功，把数据库里的状态改成 completed (已完成)
        doc = db.query(LawDocument).filter(LawDocument.id == doc_id).first()
        if doc:
            doc.status = "completed"
            db.commit()
    except Exception as e:
        # 学习失败，记录状态
        doc = db.query(LawDocument).filter(LawDocument.id == doc_id).first()
        if doc:
            doc.status = "failed"
            db.commit()
        print(f"文档处理失败: {e}")

@router.post("/upload", summary="上传并向量化法律文档")
async def upload_document(
    background_tasks: BackgroundTasks, # FastAPI 神器：后台任务
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not (file.filename.endswith('.pdf') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="只支持 PDF 或 TXT 格式")

    # 1. 把前端传来的文件存到服务器硬盘上
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. 在关系型数据库(SQLite)里先记一笔，状态是 processing (处理中)
    new_doc = LawDocument(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        status="processing"
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # 3. 把耗时的“看书学习”任务丢给后台悄悄执行，立刻给前端返回成功
    background_tasks.add_task(process_document_task, new_doc.id, file_path, db)

    return {"message": "文件上传成功，AI 正在后台努力学习中...", "doc_id": new_doc.id}

@router.get("/", summary="获取已上传法律文档列表")
def get_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    docs = db.query(LawDocument).filter(LawDocument.user_id == current_user.id).order_by(LawDocument.created_at.desc()).all()
    # 格式化一下时间返回给前端
    return [{"id": d.id, "filename": d.filename, "status": d.status, "created_at": d.created_at.strftime("%Y-%m-%d %H:%M")} for d in docs]

@router.delete("/{doc_id}", summary="删除法律文档")
def delete_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(LawDocument).filter(LawDocument.id == doc_id, LawDocument.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 1. 删掉物理文件
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
        
    # 2. 删掉数据库记录
    db.delete(doc)
    db.commit()
    return {"message": "删除成功"}