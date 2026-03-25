import os
import re
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Callable

import numpy as np
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate

from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatZhipuAI

# ========== 基础配置 ==========
load_dotenv()
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")

# 路径配置
BASE_DIR = Path(__file__).resolve().parent
TEXT_DIR = BASE_DIR / "data" / "raw" / "national"
FAISS_DB_DIR = BASE_DIR / "faiss_db"
SPLITS_CACHE = BASE_DIR / "splits_cache.pkl"

# 检索配置
VECTOR_TOP_K = 5
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ========== 创新点1：法条级语义切分器 ==========
class LawArticleSplitter:
    """基于"第XX条"语义切分，保留法条完整性"""
    def __init__(self, chunk_overlap: int = 0):
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        # 匹配"第X条"、"第XX条"、"第XXX条"等格式
        article_pattern = r"(第[\u4e00-\u9fa50-9]+条)"
        parts = re.split(article_pattern, text)
        
        # 重组法条（将"第X条"和内容合并）
        chunks = []
        current_article = ""
        for i, part in enumerate(parts):
            if re.match(article_pattern, part):
                if current_article:
                    chunks.append(current_article.strip())
                current_article = part
            else:
                current_article += part
        
        if current_article:
            chunks.append(current_article.strip())
        
        # 对超长法条进行二次切分（保证不超限）
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > CHUNK_SIZE:
                # 超长法条按段落切分
                para_chunks = self._split_long_article(chunk)
                final_chunks.extend(para_chunks)
            else:
                final_chunks.append(chunk)
        
        logger.info(f"法条级切分完成，共生成 {len(final_chunks)} 个语义块")
        return final_chunks

    def _split_long_article(self, article: str) -> List[str]:
        """切分超长法条"""
        chunks = []
        start = 0
        while start < len(article):
            end = start + CHUNK_SIZE
            # 尽量在标点处切分，保证语义完整
            if end < len(article):
                # 查找最近的标点
                for sep in ["。", "；", "，", " "]:
                    sep_pos = article.rfind(sep, start, end)
                    if sep_pos != -1:
                        end = sep_pos + 1
                        break
            chunks.append(article[start:end].strip())
            start = end - self.chunk_overlap
        
        return chunks

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """切分文档列表"""
        split_docs = []
        for doc in documents:
            text_chunks = self.split_text(doc.page_content)
            for i, chunk in enumerate(text_chunks):
                if chunk.strip():
                    # 关键：从当前chunk中提取法条编号，并存入元数据
                    article_num = self._extract_article(chunk)
                    new_doc = Document(
                        page_content=chunk,
                        metadata={
                            **doc.metadata,
                            "chunk_id": i,
                            "article": article_num  # 确保这里被正确赋值
                        }
                    )
                    split_docs.append(new_doc)
        return split_docs

    def _extract_article(self, text: str) -> str:
        """从文本中提取法条编号"""
        match = re.search(r"(第[\u4e00-\u9fa50-9]+条)", text)
        return match.group(1) if match else ""  # 返回空字符串，避免"未知法条"

# ========== 工具函数 ==========
def load_law_documents() -> List[Document]:
    """加载法律文本文件"""
    documents = []
    if not TEXT_DIR.exists():
        logger.warning(f"文本目录不存在：{TEXT_DIR}")
        return documents

    # 遍历所有txt文件
    txt_files = list(TEXT_DIR.glob("*.txt"))
    if not txt_files:
        logger.warning(f"未找到文本文件：{TEXT_DIR}")
        return documents

    for txt_file in txt_files:
        try:
            # 读取文件（简化编码处理）
            with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # 创建文档对象
            doc = Document(
                page_content=content,
                metadata={
                    "source": str(txt_file),
                    "file_name": txt_file.name,
                    "region": "national"
                }
            )
            documents.append(doc)
            logger.info(f"加载文件：{txt_file.name}")

        except Exception as e:
            logger.error(f"加载文件失败 {txt_file.name}：{str(e)}")

    return documents

def load_or_split_documents() -> List[Document]:
    """加载或切分文档（带缓存）"""
    import pickle

    # 加载原始文档
    raw_docs = load_law_documents()
    if not raw_docs:
        return []
    
    # 尝试从缓存加载
    if SPLITS_CACHE.exists():
        try:
            with open(SPLITS_CACHE, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"加载缓存失败：{str(e)}")

    # 切分文档
    logger.info("使用法条级切分器处理文本...")
    splitter = LawArticleSplitter(chunk_overlap=CHUNK_OVERLAP)
    splits = splitter.split_documents(raw_docs)

    # 保存缓存
    try:
        with open(SPLITS_CACHE, "wb") as f:
            pickle.dump(splits, f)
        logger.info(f"文本分块缓存已保存，共 {len(splits)} 个法条chunk")
    except Exception as e:
        logger.warning(f"保存缓存失败：{str(e)}")

    return splits

# ========== 核心修复：自定义Embedding（继承Embeddings基类） ==========
class CustomZhipuEmbeddings(Embeddings):
    """兼容LangChain的智谱Embedding实现"""
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        # 直接初始化智谱客户端
        from zhipuai import ZhipuAI
        self.client = ZhipuAI(api_key=api_key)

    def embed_query(self, text: str) -> List[float]:
        """单文本嵌入"""
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """多文本嵌入"""
        try:
            response = self.client.embeddings.create(
                model="embedding-2",
                input=texts
            )
            # 提取嵌入向量
            embeddings = [item.embedding for item in response.data]
            return embeddings
        except Exception as e:
            logger.error(f"嵌入计算失败：{str(e)}")
            # 返回空向量兜底
            return [[0.0]*1024 for _ in texts]

# ========== 构建向量库 ==========
def build_vector_db() -> FAISS:
    """构建/加载FAISS向量库"""
    # 加载切分后的文档
    splits = load_or_split_documents()
    if not splits:
        raise ValueError("未加载到任何法律文档！")
    
    # 初始化自定义嵌入模型
    embeddings = CustomZhipuEmbeddings(api_key=ZHIPU_API_KEY)
    
    # 加载/重建向量库
    if FAISS_DB_DIR.exists():
        try:
            vector_db = FAISS.load_local(
                str(FAISS_DB_DIR),
                embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("成功加载现有向量库")
            return vector_db
        except Exception as e:
            logger.warning(f"加载向量库失败，重建：{str(e)}")
    
    # 重建向量库
    logger.info("开始构建新的向量库...")
    vector_db = FAISS.from_documents(splits, embeddings)
    # 保存向量库
    vector_db.save_local(str(FAISS_DB_DIR))
    logger.info("向量库构建并保存完成")
    
    return vector_db

# ========== 兼容web.py的关键函数：switch_region_db ==========
def switch_region_db(region="national"):
    """
    兼容web.py的旧接口，保证导入和调用不报错
    :param region: 地区参数（暂时忽略，默认使用全国法条）
    :return: vector_db, splits
    """
    try:
        # 直接调用无参的build_vector_db
        vector_db = build_vector_db()
        # 加载切分后的文档
        splits = load_or_split_documents()
        logger.info(f"切换地区向量库完成，当前地区：{region}，文档数量：{len(splits)}")
        return vector_db, splits
    except Exception as e:
        logger.error(f"切换地区向量库失败：{str(e)}")
        # 兜底返回空值，避免web.py崩溃
        return None, []

# ========== 构建RAG链 ==========
def build_rag_chain():
    """构建完整的RAG问答链"""
    # 1. 初始化向量库
    vector_db = build_vector_db()
    
    # 2. 创建检索器（禁用MMR，避免复杂逻辑）
    retriever = vector_db.as_retriever(
        search_type="similarity",  # 纯相似度检索（最稳定）
        search_kwargs={"k": VECTOR_TOP_K}
    )
    
    # 3. 初始化LLM
    llm = ChatZhipuAI(
        api_key=ZHIPU_API_KEY,
        model="glm-4-air",
        temperature=0.1,  # 低随机性保证回答准确
        max_tokens=2048
    )
    
    # 4. 构建提示模板
    prompt_template = """
你是专业的法律援助助手，严格按照以下要求回答：
1. 仅使用提供的法律条文回答，不编造任何信息；
2. 明确引用具体的法条编号和法律名称；
3. 回答结构清晰，分点说明；
4. 无法回答时明确说明"未找到相关法律条文"。

法律条文：
{context}

用户问题：{question}

请按以下格式回答：
### 回答内容
[你的详细回答]

### 引用法条
1. [文件名] - [法条编号]
...
"""
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    
    # 5. 定义问答函数
    def rag_answer(query: str) -> Dict:
        try:
            # 检索相关文档
            retrieved_docs = retriever.invoke(query)
            logger.info(f"检索到 {len(retrieved_docs)} 个相关文档")
            
            # 格式化上下文
            context = "\n\n".join([doc.page_content for doc in retrieved_docs])
            
            # 生成回答
            chain = prompt | llm | StrOutputParser()
            answer = chain.invoke({
                "context": context,
                "question": query
            })
            
            # 整理引用来源（去掉未知法条/None）
            sources = []
            for doc in retrieved_docs:
                sources.append({
                    "file_name": doc.metadata.get("file_name", ""),
                    "article": doc.metadata.get("article", "")
                })
            
            # 可信度评估（简化版）
            reliability = {
                "score": round(len(retrieved_docs)/VECTOR_TOP_K, 2),
                "level": "高可信度" if len(retrieved_docs)>=3 else "中等可信度" if len(retrieved_docs)>0 else "低可信度",
                "suggestion": "回答基于检索到的法律条文，可参考" if retrieved_docs else "未找到相关法条，建议咨询专业律师"
            }
            
            return {
                "answer": answer,
                "sources": sources,
                "reliability": reliability,
                "retrieved_count": len(retrieved_docs)
            }
        
        except Exception as e:
            logger.error(f"问答链执行失败：{str(e)}", exc_info=True)
            # 错误兜底返回（保证所有字段都存在）
            return {
                "answer": f"回答生成失败：{str(e)}",
                "sources": [],
                "reliability": {
                    "score": 0.0,
                    "level": "无可信度",
                    "suggestion": "系统异常，无法回答"
                },
                "retrieved_count": 0
            }
    
    return rag_answer

# ========== 主程序 ==========
def main():
    """交互测试主函数"""
    # 检查API Key
    if not ZHIPU_API_KEY:
        logger.error("未配置ZHIPU_API_KEY环境变量！")
        return
    
    try:
        # 构建RAG链
        logger.info("初始化法律援助RAG系统...")
        rag_answer = build_rag_chain()
        
        # 交互界面
        print("\n" + "="*60)
        print("🎯 公益法律援助RAG系统")
        print("💡 输入问题即可提问（输入 'exit' 退出）")
        print("="*60 + "\n")
        
        while True:
            query = input("👉 请输入你的法律问题：")
            if query.lower() == "exit":
                print("👋 退出系统，再见！")
                break
            
            if not query.strip():
                print("⚠️ 请输入有效的法律问题！")
                continue
            
            # 调用RAG回答
            result = rag_answer(query)
            
            # 输出结果（优化显示，去掉- None）
            print(f"\n📢 回答内容：\n{result['answer']}")
            print(f"\n📊 可信度评估：{result['reliability']['level']}（评分：{result['reliability']['score']}）")
            print(f"💡 评估建议：{result['reliability']['suggestion']}")
            
            # 输出引用来源（优化显示）
            if result["sources"]:
                print("\n📚 引用法条来源：")
                for i, source in enumerate(result["sources"], 1):
                    file_name = source['file_name'] or "未知文件"
                    article = source['article']
                    if article:
                        print(f"   {i}. {file_name} - {article}")
                    else:
                        print(f"   {i}. {file_name}")
            
            print("\n" + "-"*60 + "\n")
    
    except Exception as e:
        logger.error(f"系统初始化失败：{str(e)}", exc_info=True)

if __name__ == "__main__":
    main()