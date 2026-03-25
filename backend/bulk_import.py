import os
import shutil
from app.core.database import SessionLocal
from app.models.models import LawDocument, User
from app.services.rag_service import rag_engine

# 配置路径
SOURCE_DIR = "import_data"
UPLOAD_DIR = "uploads"

def bulk_import():
    # 确保上传目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # 开启数据库会话
    db = SessionLocal()

    # 获取你的管理员账号 (因为你是第一个注册的，ID 肯定是 1)
    admin_user = db.query(User).filter(User.id == 1).first()
    if not admin_user:
        print("❌ 错误：未找到 ID=1 的用户，请先在前端注册一个账号！")
        db.close()
        return
    
    if not os.path.exists(SOURCE_DIR):
        print(f"❌ 错误：找不到文件夹 '{SOURCE_DIR}'。")
        db.close()
        return

    # 过滤出所有的 PDF 和 TXT 文件
    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.pdf') or f.endswith('.txt')]
    if not files:
        print(f"⚠️ 提示：'{SOURCE_DIR}' 文件夹中没有任何 PDF 或 TXT 文件。")
        db.close()
        return

    print(f"🚀 扫描到 {len(files)} 个法律文件，开始批量注入知识库...\n" + "-"*40)

    for filename in files:
        source_path = os.path.join(SOURCE_DIR, filename)
        # 为了避免文件名冲突，加上 sys_ 前缀
        dest_path = os.path.join(UPLOAD_DIR, f"sys_{filename}")
        
        # 1. 复制文件到系统的正式存放目录
        shutil.copyfile(source_path, dest_path)
        
        # 2. 在 SQLite 数据库先记一笔，状态为处理中
        new_doc = LawDocument(
            user_id=admin_user.id,
            filename=filename,
            file_path=dest_path,
            status="processing"
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        
        print(f"🔄 正在深度学习: {filename} ...")
        try:
            # 3. 呼叫大模型进行切片和向量化，存入 ChromaDB
            rag_engine.add_document(dest_path)
            
            # 4. 学习成功，更新数据库状态
            new_doc.status = "completed"
            db.commit()
            print(f"✅ 成功掌握: {filename}\n")
        except Exception as e:
            # 学习失败，记录状态
            new_doc.status = "failed"
            db.commit()
            print(f"❌ 学习失败: {filename}，报错信息: {e}\n")

    db.close()
    print("-" * 40)
    print("🎉 批量知识注入任务圆满完成！你的 AI 已经进化！")

if __name__ == "__main__":
    bulk_import()
