import os
from pathlib import Path
from pypdf import PdfReader

# 配置路径
PDF_DIR = Path("/root/LawRAG/LawRAG/data/pdf")
TXT_DIR = Path("/root/LawRAG/LawRAG/data/raw")
TXT_DIR.mkdir(parents=True, exist_ok=True)  # 确保目录存在

def extract_pdf_to_txt(pdf_path: Path, txt_path: Path):
    """提取单个PDF的文本并保存为TXT"""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            # 清理无效字符，优化格式
            clean_text = page_text.replace("\n", " ").replace("  ", " ").strip()
            text += clean_text + "\n\n"
        
        # 保存文本
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✅ 成功提取：{pdf_path.name} -> {txt_path.name}")
    except Exception as e:
        print(f"❌ 提取失败 {pdf_path.name}：{e}")

if __name__ == "__main__":
    # 遍历所有PDF文件
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print("⚠️ 未在data/pdf目录下找到任何PDF文件")
        exit()
    
    print(f"📄 共发现 {len(pdf_files)} 个PDF文件，开始提取...")
    for pdf_file in pdf_files:
        # 生成对应的TXT文件名（保留原名称，替换后缀）
        txt_filename = pdf_file.stem + ".txt"
        txt_path = TXT_DIR / txt_filename
        extract_pdf_to_txt(pdf_file, txt_path)
    
    print("\n🎉 批量提取完成！文本文件已保存至：/root/LawRAG/LawRAG/data/raw")