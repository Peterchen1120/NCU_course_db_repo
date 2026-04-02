import pandas as pd
import re


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
pd.DataFrame(df).to_csv("course_new_relation.csv", index=False, encoding="utf-8-sig")