import pandas as pd
import re,os,dotenv
from supabase import create_client
dotenv.load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_API")

supabase = create_client(url, key)

def split_dept_year(text):
    # 使用正則表達式尋找最後出現的「年級」或「不分類」作為切割點
    # 範例：資訊管理學系一年級A班 -> (資訊管理學系, 一年級A班)
    match = re.search(r'(一年級|二年級|三年級|四年級|五年級|碩士班|博士班|不分類)', text)
    if match:
        start = match.start()
        dept = text[:start]
        year = text[start:]
        return dept, year
    return text, "未知"

# 1. 讀取本地 CSV
df = pd.read_csv('course_relation.csv')

# 2. 執行拆分
df[['new_dept', 'new_year']] = df['dept_year'].apply(lambda x: pd.Series(split_dept_year(x)))

print("預覽拆分結果：")
print(df[['dept_year', 'new_dept', 'new_year']].head())

# 3. 同步到 Supabase (假設以 course_id 作為更新依據)
# 注意：為了效率，建議分批更新 (Batch Update)
for index, row in df.iterrows():
    try:
        supabase.table("course_relation").update({
            "dept_name": row['new_dept'],
            "year_level": row['new_year']
        }).eq("course_id", row['course_id']).execute()
        
        if index % 100 == 0:
            print(f"已處理 {index} 筆資料...")
    except Exception as e:
        print(f"更新第 {index} 筆時出錯: {e}")

print("補丁執行完畢！")