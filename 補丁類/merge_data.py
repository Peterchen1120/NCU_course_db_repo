import pandas as pd

# 1. 載入資料
kb = pd.read_csv('dify_knowledge_base.csv')
rel = pd.read_csv('course_relation.csv')

# 2. 資料清洗：確保 Key 格式一致 (移除空格)
kb['course_id'] = kb['course_full_id'].str.strip()
rel['course_id'] = rel['course_id'].str.strip()

# 3. 執行合併 (以關係表為基礎，掛載課程細節)
# 這樣一門課如果開給多個系，會自動產生多行，每行帶有不同系所標籤
final_df = pd.merge(rel, kb, on='course_id', how='left')

# 4. 建立一個方便 Dify 檢索的綜合欄位
final_df['search_tag'] = final_df['dept_year'] + " " + final_df['course_name'] + " " + final_df['teacher'].fillna('')

# 5. 整理欄位順序並輸出
# 移除重複或不需要的臨時欄位
cols = ['dept_year', 'course_id', 'course_name', 'teacher', 'basic_info', 'syllabus_summary', 'priority_logic', 'search_tag']
final_df = final_df[cols]

final_df.to_csv('final_dify_dataset.csv', index=False, encoding='utf-8-sig')

print(f"合併完成！總計產出 {len(final_df)} 筆資料。")