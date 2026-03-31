import sqlite3
from supabase import create_client


class DBManager:
    def __init__(self, db_path="ncu_courses.db", supabase_url=None, supabase_key=None):
        self.db_path = db_path
        self.supabase = create_client(supabase_url, supabase_key) if supabase_url else None

    def save_to_sqlite(self, catalog, schedule, relation):
        conn = sqlite3.connect(self.db_path)
        # 1. 建立表 (CREATE TABLE IF NOT EXISTS...)
        # 2. 寫入資料 (INSERT OR IGNORE / REPLACE)

        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_catalog(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT UNIQUE,
            dept_code TEXT,
            title_zh TEXT,
            title_en TEXT,
            note_red TEXT,
            note_blue TEXT,
            teacher TEXT,
            credit REAL,
            required_type TEXT,
            half_whole TEXT,
            capacity INTEGER,
            priority_url TEXT,
            syallabus_url TEXT,
            raw_time_classroom TEXT
            category TEXT,
            subcategory TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_schedule(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            catalog_id INTEGER,
            course_id TEXT,
            day TEXT,
            time TEXT,
            classroom TEXT,
            FOREIGN KEY (catalog_id) REFERENCES course_catalog(id)            
        )
        """)

        catalog_id_map = {}

        for row in catalog:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO course_catalog(
                        course_id, dept_code, title_zh, title_en,
                        note_red, note_blue, teacher, credit,
                        required_type, half_whole, capacity,
                        priority_url, syallabus_url, raw_time_classroom, category, subcategory
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["course_id"], row["dept_code"], row["title_zh"], row["title_en"],
                    row["note_red"], row["note_blue"], row["teacher"], row["credit"],
                    row["required_type"], row["half_whole"], row["capacity"],
                    row["priority_url"], row["syallabus_url"], row["raw_time_classroom"], row["category"], row["subcategory"]
                ))
                catalog_id_map[row["course_id"]] = cursor.lastrowid
            except Exception as e:
                print(f"DB Insert Catalog Error: {e}")

        for s_row in schedule:
            cid = s_row["course_id"]
            cat_id = catalog_id_map.get(cid)
            cursor.execute("""
                INSERT INTO course_schedule (catalog_id, course_id, day, time, classroom)
                VALUES (?, ?, ?, ?, ?)
            """, (cat_id, cid, s_row["day"], s_row["time"], s_row["classroom"]))

        conn.commit()
        conn.close()        
        print(f"📂 資料庫已更新: {self.db_path}")
        conn.close()
        print(f"✅ 本地 SQLite 更新完成")

    def sync_to_supabase(self, catalog, schedule, relation):
        if not self.supabase: 
            return
        
        self.supabase.table("course_catalog").upsert(catalog, on_conflict="course_id").execute()
        print("✅ Catalog 同步完成")

        self.supabase.table("course_schedule").insert(schedule).execute()
        print("✅ Schedule 同步完成")

        self.supabase.table("course_relation").insert(relation).execute()
        print("✅ Relation 同步完成")
        
        print(f"✅ Supabase 同步完成")

    def save_to_csv(self, catalog, schedule, relation):
        import pandas as pd
        pd.DataFrame(catalog).to_csv("course_catalog.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(schedule).to_csv("course_schedule.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(relation).to_csv("course_relation.csv", index=False, encoding="utf-8-sig")    