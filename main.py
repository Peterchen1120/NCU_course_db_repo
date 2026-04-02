from modules.scraper import NCUScraper
from modules.processor import CourseProcessor
from modules.database import DBManager
import dotenv,os
import pandas as pd
dotenv.load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API = os.getenv("SUPABASE_API")
ACCOUNT = os.getenv("ACCOUNT","")
PASSWORD = os.getenv("PASSWORD","")
dept_list = [
    # --- 中心、處室 ---
    #"體育室", "軍訓室", "學務處-服務學習發展中心", "通識教育中心", "語言中心", "總教學中心",
    
    # --- 文學院 ---
    "中國文學系", "英美語文學系", "法國語文學系", "文學院學士班", "師資培育中心",
    
    # --- 理學院 ---
    "理學院", "數學系", "數學系(數學科學組)", "數學系(計算與資料科學組)", "物理學系", "化學學系", "理學院學士班",
    
    # --- 工學院 ---
    "工學院", "土木工程學系", "機械工程學系", "機械工程學系(光機電工程組)", "化學工程與材料工程學系", "光電科學與工程學系", "工學院學士班",
    
    # --- 管理學院 ---
    "管理學院", "企業管理學系", "資訊管理學系", "財務金融學系", "經濟學系",
    
    # --- 資訊電機學院 ---
    "電機工程學系", "資訊工程學系", "通訊工程學系", "資訊電機學院學士班",
    
    # --- 地球科學學院 ---
    "大氣科學學系", "大氣科學學系大氣物理組", "地球科學學系", "地球科學學院學士班", "太空科學與工程學系",
    
    # --- 客家學院 ---
    "客家語文暨社會科學學系", "客家語文暨社會科學學系(客家社會及政策組)", "客家語文暨社會科學學系(客家語文及傳播組)",
    
    # --- 生醫理工學院 ---
    "生命科學系", "生醫科學與工程學系", "生醫科學與工程學系系統生物與生物資訊學士班",

    # --- 永續與綠能科技研究學院 ---
    "永續與綠能科技研究學院"
]

COLLEGE_MAP = {
    "中心、處室": ["體育室", "軍訓室", "學務處-服務學習發展中心", "通識教育中心", "語言中心", "總教學中心"],
    "文學院": ["中國文學系", "英美語文學系", "法國語文學系", "文學院學士班", "師資培育中心"],
    "理學院": ["數學系", "數學系(數學科學組)", "數學系(計算與資料科學組)", "物理學系", "化學學系", "理學院學士班"],
    "工學院": ["土木工程學系", "機械工程學系", "機械工程學系(光機電工程組)", "化學工程與材料工程學系", "工學院學士班"],
    "管理學院": ["管理學院", "企業管理學系", "資訊管理學系", "財務金融學系", "經濟學系", "管理學院學士班"],
    "資訊電機學院": ["電機工程學系", "資訊工程學系", "通訊工程學系", "資訊電機學院學士班"],
    "地球科學學院": ["大氣科學學系", "大氣科學學系大氣物理組", "地球科學學系", "地球科學學院學士班", "太空科學與工程學系"],
    "客家學院": ["客家語文暨社會科學學系", "客家語文暨社會科學學系(客家社會及政策組)", "客家語文暨社會科學學系(客家語文及傳播組)"],
    "生醫理工學院": ["生命科學系", "生醫科學與工程學系", "生醫科學與工程學系系統生物與生物資訊學士班"],
    "永續與綠能科技研究學院": ["永續與綠能科技研究學院"]
}

def lookup_college(department):
    department = str(department).strip()
    for college, departments in COLLEGE_MAP.items():
        if department in departments:
            return college
    return ""

def build_basic_info(row):
    credit = "" if pd.isna(row.get("credit")) else str(row.get("credit")).replace(".0", "")
    time_classroom = "" if pd.isna(row.get("raw_time_classroom")) else str(row.get("raw_time_classroom")).strip()
    if credit and time_classroom:
        return f"{credit}學分｜{time_classroom}"
    return credit or time_classroom

def build_dify_knowledge_base():
    df = pd.read_csv("course_catalog.csv", encoding="utf-8-sig").fillna("")
    df["serial_no"] = df["course_id"].astype(str).str[:5]
    df["clean_course_code"] = df["course_id"].astype(str).str[5:]
    df["college"] = df["dept_code"].apply(lookup_college)

    scraper = NCUScraper(ACCOUNT, PASSWORD)
    processor = CourseProcessor()
    records = []

    try:
        for idx, row in df.iterrows():
            syllabus_raw = scraper.fetch_detail_text(row.get("syallabus_url", ""), "syllabus")
            priority_raw = scraper.fetch_detail_text(row.get("priority_url", ""), "priority")

            records.append({
                "college": row["college"],
                "department": row["dept_code"],
                "course_full_id": f"{row['serial_no']}{row['clean_course_code']}",
                "course_name": " / ".join([part for part in [str(row.get("title_zh", "")).strip(), str(row.get("title_en", "")).strip()] if part]),
                "teacher": row.get("teacher", ""),
                "basic_info": build_basic_info(row),
                "syllabus_summary": processor.clean_syllabus(syllabus_raw),
                "priority_logic": processor.format_priority(priority_raw)
            })

            if (idx + 1) % 50 == 0:
                pd.DataFrame(records).to_csv("dify_knowledge_base_checkpoint.csv", index=False, encoding="utf-8-sig")

    finally:
        scraper.close()

    pd.DataFrame(records, columns=[
        "college",
        "department",
        "course_full_id",
        "course_name",
        "teacher",
        "basic_info",
        "syllabus_summary",
        "priority_logic"
    ]).to_csv("dify_knowledge_base.csv", index=False, encoding="utf-8-sig")

def main():
    # 1. 初始化
    scraper = NCUScraper(ACCOUNT,PASSWORD)
    processor = CourseProcessor()
    db = DBManager("ncu_courses.db", SUPABASE_URL, SUPABASE_API)
    raw_data = []
    # 2. 執行爬蟲 (只抓原始資料)

    for dept in dept_list:
        print(f"🚀 開始爬取{dept}課程...")
        raw_data.append(scraper.get_dept_courses(dept))

    scraper.close()

    # 3. 資料清洗與去重
    clean_catalog, clean_schedule, clean_relation = [],[],[]
    print("🧹 正在進行資料清洗與去重...")
    for course_data in raw_data:
        dept_catalog, dept_schedule, dept_relation = processor.process(course_data)
        clean_catalog.extend(dept_catalog)
        clean_schedule.extend(dept_schedule)
        clean_relation.extend(dept_relation)

    # 4. 儲存至本地備份 (CSV/SQLite)
    print("💾 儲存本地備份...")
    db.save_to_csv(clean_catalog, clean_schedule, clean_relation)
    #db.save_to_sqlite(clean_catalog, clean_schedule, clean_relation)

    # 5. 同步至雲端 Supabase (給 Dify 用)
    print("☁️  同步至 Supabase...")
    db.sync_to_supabase(clean_catalog, clean_schedule, clean_relation)

    print("✨ 全流程執行完畢！")

if __name__ == "__main__":
    build_dify_knowledge_base()
