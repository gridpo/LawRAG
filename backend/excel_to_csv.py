import pandas as pd

# 这里写你最初始、最真实的那个 Excel 文件名
# 如果名字不对，请自行修改成你上传到服务器的实际文件名
input_excel = "法律维权场景咨询提问库.xlsx" 
output_csv = "clean_questions.csv"

print(f"⏳ 正在读取 Excel: {input_excel}...")

try:
    # 读取 Excel 文件（默认读取第一个 Sheet）
    df = pd.read_excel(input_excel)
    
    # 将其无损转换为纯正的 UTF-8 CSV 文件
    # index=False 代表不保存行号，encoding='utf-8-sig' 确保绝不乱码
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    
    print(f"🎉 转换成功！已生成干净的 CSV 文件: {output_csv}")
    
except Exception as e:
    print(f"❌ 转换失败: {e}")
