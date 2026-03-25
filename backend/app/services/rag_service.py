import os
from typing import List
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from zhipuai import ZhipuAI

from app.core.config import settings

# 兼容 LangChain 的智谱 Embedding (修复64条限流问题)
class CustomZhipuEmbeddings(Embeddings):
    def __init__(self, api_key: str):
        self.client = ZhipuAI(api_key=api_key)
        self.BATCH_SIZE = 64

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        all_embeddings = []
        # 按BATCH_SIZE分批处理
        for i in range(0, len(texts), self.BATCH_SIZE):
            # 截取当前批次的文本（最多64条）
            batch_texts = texts[i:i + self.BATCH_SIZE]
            # 调用智谱AI嵌入接口
            response = self.client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=batch_texts
            )
            # 提取当前批次的嵌入向量并合并
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        return all_embeddings

class RAGEngine:
    def __init__(self):
        self.embeddings = CustomZhipuEmbeddings(api_key=settings.ZHIPU_API_KEY)
        self.llm = ChatZhipuAI(
            api_key=settings.ZHIPU_API_KEY,
            model=settings.LLM_MODEL,
            temperature=0.1,
            streaming=True  # 开启流式输出
        )
        # 初始化 Chroma 向量库 
        self.vector_store = Chroma(
            persist_directory=settings.CHROMA_DB_DIR,
            embedding_function=self.embeddings
        )

    def process_and_store_file(self, file_path: str, file_name: str):
        """文档加载、分块与向量化 [cite: 23, 26, 29]"""
        # 1. 格式解析 [cite: 24]
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding='utf-8')
        docs = loader.load()

        # 2. 文本分块与元数据提取 
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        splits = text_splitter.split_documents(docs)
        
        # 注入元数据
        for split in splits:
            split.metadata["file_name"] = file_name
            
        # 3. 向量化与存储 [cite: 31]
        self.vector_store.add_documents(splits)
        return len(splits)

    def get_retriever(self):
        """获取检索器 [cite: 32]"""
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": settings.TOP_K} # 检索Top-K [cite: 34]
        )
    
    def add_document(self, file_path: str):
        """读取文件、切片并存入 Chroma 向量数据库"""
        # 1. 判断文件类型并加载文字
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.txt'):
            loader = TextLoader(file_path, encoding='utf-8')
        else:
            raise ValueError("不支持的文件格式")
        
        docs = loader.load()
        
        # 2. 文本切片 (把长文切成500字一段，前后重叠50字防断句)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        splits = text_splitter.split_documents(docs)
        
        # 3. 把切好的文本段落向量化，并存入 Chroma 数据库
        self.vector_store.add_documents(splits)
        print(f"成功将 {len(splits)} 个文本块存入向量数据库！")

rag_engine = RAGEngine()