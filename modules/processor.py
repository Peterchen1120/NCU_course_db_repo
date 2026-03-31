from bs4 import BeautifulSoup
import re




class CourseProcessor:
    def __init__(self):
        self.weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        self.times = ["1", "2", "3", "4", "Z", "5", "6", "7", "8", "9", "A", "B", "C"]
        self.seen_course_ids = set()

    def process(self,all_raw_data):
        final_catalog = []
        final_schedule = []
        final_relation = []
        for raw_data in all_raw_data:
            result = self.parse_course_row(raw_data)
            if not result: 
                continue
            course_id = result["catalog"]["course_id"]
            # 確保catalog、schedule課程不重複
            if course_id not in self.seen_course_ids:
                final_catalog.append(result["catalog"])
                self.seen_course_ids.add(course_id)
                final_schedule.extend(result["schedule"])

            # Relation 不論是否重複都要加，因為多年級可能共修
            final_relation.append(result["relation"])
            # to-do
            # 完成後續程式碼
        return final_catalog,final_schedule,final_relation
        
    def parse_capacity(self,value):
        val_str = str(value).strip()
        if val_str=="無" or not val_str:
            return None
        try: return int(value)
        except: return 0
    

    def parse_course_row(self,raw_data):
        tr_html = raw_data["raw_html"]
        dept_code = raw_data["dept_code"].strip()
        grade = raw_data["grade"].strip()
        soup = BeautifulSoup(tr_html, "html.parser")
        tds = soup.find_all("td", recursive=False)
        if len(tds) < 8: return None 

        def cell(i):
            return tds[i].text.strip().replace("\n", " ") if i < len(tds) else ""

        def get_js_link(td):
            a = td.find("a")
            if a and 'onclick' in a.attrs:
                match = re.search(r"'(.*?)'", a['onclick'])
                return "https://cis.ncu.edu.tw/" + match.group(1) if match else ""
            return ""

        course_td = tds[1] 
        chinese_name = ""
        for t in course_td.find_all(string=True, recursive=False):
            text = t.strip()
            if text: chinese_name += text + " "

        eng_span = course_td.find("span", class_="engclass")
        english_name = eng_span.get_text(strip=True) if eng_span else ""
        notice_span = course_td.find("span", class_="notice")
        red_notice = notice_span.get_text(strip=True).replace("\n", " ") if notice_span else ""
        desc_span = course_td.find("span", class_="descript")
        raw_note = desc_span.get_text() if desc_span else ""
        blue_note = "".join(raw_note.split())

        course_id = tds[0].get_text().strip()
        
        # To-do 
        # 新增 raw_time_classroom 欄位
        
        catalog_element = {
            "course_id": course_id,
            "dept_code": dept_code,
            "title_zh": chinese_name.strip(),
            "title_en": english_name.strip(),
            "note_red": red_notice,
            "note_blue": blue_note,
            "teacher": cell(2),
            "credit": self.parse_capacity(cell(3)),
            "required_type": cell(5),
            "half_whole": cell(6),
            "capacity": self.parse_capacity(cell(7)),
            "priority_url": get_js_link(tds[8]),
            "syallabus_url": get_js_link(tds[9]),
            "raw_time_classroom":cell(4),
            "category": "",
            "subcategory": ""
        }

        dept_year_label = dept_code + grade
        relation = {
            "dept_year": dept_year_label,
            "course_id": course_id
        }

        current_schedule = []
        day=""
        try:
            match_text = tds[4].get_text(separator="|", strip=True)
            temp = re.match(r"(.+)\s\((.+)\)", match_text)
            if temp:
                data = temp.group(1).split("|")
                for item in data:
                    tim_classroom = item.split("/")
                    if len(tim_classroom) >= 2:
                        raw_time = tim_classroom[0].strip()
                        classroom = tim_classroom[1].strip()
                        for char in raw_time:
                            if char in self.weekdays:
                                day = char
                            elif char in self.times:
                                current_schedule.append({
                                    "course_id": course_id,
                                    "day": day,
                                    "time": char,
                                    "classroom": classroom
                                })
        except Exception as e:
            print(f"Error parse schedule for {course_id}: {e}")

        return {"catalog": catalog_element, # dict
                "schedule": current_schedule, # list[dict] 
                "relation": relation    # dict
                }

    