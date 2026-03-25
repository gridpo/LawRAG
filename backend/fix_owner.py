from app.core.database import SessionLocal
from app.models.models import LawDocument, User

def fix_ownership():
    db = SessionLocal()
    
    # 找到你刚刚注册的那个最新账号 (ID最大的那个)
    new_user = db.query(User).order_by(User.id.desc()).first()
    
    if not new_user:
        print("没有找到新用户")
        return

    # 查出数据库里所有的文件
    all_docs = db.query(LawDocument).all()
    
    # 把它们的主人全部改成这个新用户
    for doc in all_docs:
        doc.user_id = new_user.id
        
    db.commit()
    print(f"🎉 大功告成！成功将 {len(all_docs)} 个文档的所有权，转移给了你的新账号: {new_user.username}")
    db.close()

if __name__ == "__main__":
    fix_ownership()
