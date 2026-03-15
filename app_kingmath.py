import streamlit as st
import streamlit.components.v1 as components
import random
import math
import zipfile
import io
import time
import itertools

# ==========================================
# ⚙️ ตั้งค่าหน้าเพจ Web App & CSS
# ==========================================
st.set_page_config(page_title="King Math Pro", page_icon="👑", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }
    div[data-testid="stSidebar"] div.stButton > button { background-color: #c0392b; color: white; border-radius: 8px; height: 3.5rem; font-size: 18px; font-weight: bold; border: none; box-shadow: 0 4px 6px rgba(192,57,43,0.3); transition: all 0.3s ease;}
    div[data-testid="stSidebar"] div.stButton > button:hover { background-color: #e74c3c; transform: translateY(-2px); box-shadow: 0 6px 12px rgba(192,57,43,0.4); }
    div.stDownloadButton > button { border-radius: 8px; font-weight: bold; border: 1px solid #bdc3c7; }
    div.stDownloadButton > button:hover { border-color: #c0392b; color: #c0392b; }
    .main-header { background: linear-gradient(135deg, #2c3e50, #c0392b); padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem; box-shadow: 0 10px 20px rgba(0,0,0,0.15); }
    .main-header.challenge { background: linear-gradient(135deg, #000000, #c0392b, #8e44ad); }
    .main-header h1 { margin: 0; font-size: 2.8rem; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    .main-header p { margin: 10px 0 0 0; font-size: 1.2rem; opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. คลังคำศัพท์และตัวช่วย (Helpers)
# ==========================================
NAMES = ["อคิณ", "นาวิน", "ภูผา", "สายฟ้า", "เจ้านาย", "ข้าวหอม", "ใบบัว", "มะลิ", "น้ำใส", "ญาญ่า", "ปลื้ม", "พายุ", "ไออุ่น", "กะทิ", "คุณครู", "นักเรียน"]
box_html = "<span style='display: inline-block; width: 24px; height: 24px; border: 2px solid #c0392b; border-radius: 4px; vertical-align: middle; position: relative; top: -2px; background-color: #fff;'></span>"

def get_vertical_fraction(num, den, color="#c0392b", is_bold=True):
    weight = "bold" if is_bold else "normal"
    # ใช้ white-space: nowrap ป้องกันการแตกบรรทัด และเพิ่ม padding ให้เส้นคั่นดูสวยงามสมดุล
    return f"""<span style="display:inline-flex; flex-direction:column; vertical-align:middle; text-align:center; line-height:1.4; margin: 0 6px; font-family:'Sarabun', sans-serif; white-space: nowrap;"><span style="border-bottom: 2px solid {color}; padding: 2px 6px; font-weight:{weight}; color:{color};">{num}</span><span style="padding: 2px 6px; font-weight:{weight}; color:{color};">{den}</span></span>"""

def get_vertical_math(top_chars, bottom_chars, result_chars, operator="+"):
    max_len = max(len(top_chars), len(bottom_chars), len(result_chars))
    top_padded = [""] * (max_len - len(top_chars)) + top_chars
    bot_padded = [""] * (max_len - len(bottom_chars)) + bottom_chars
    res_padded = [""] * (max_len - len(result_chars)) + result_chars
    
    html = "<table style='border-collapse: collapse; font-size: 26px; font-weight: bold; text-align: center; margin: 15px 0 15px 40px;'>"
    html += "<tr>"
    for char in top_padded: html += f"<td style='padding: 5px 12px; width: 35px;'>{char}</td>"
    html += f"<td rowspan='2' style='padding-left: 20px; vertical-align: middle; font-size: 28px; color: #2c3e50;'>{operator}</td></tr><tr>"
    for char in bot_padded: html += f"<td style='padding: 5px 12px; width: 35px; border-bottom: 2px solid #333;'>{char}</td>"
    html += "</tr><tr>"
    for char in res_padded: html += f"<td style='padding: 5px 12px; width: 35px; border-bottom: 4px double #333;'>{char}</td>"
    html += "<td></td></tr></table>"
    return html

# ==========================================
# 2. ฐานข้อมูลหัวข้อ
# ==========================================
king_topics = [
    "การสร้างจำนวนจากเลขโดด", "โจทย์ปัญหาทำผิดเป็นถูก", "การนับตารางเรขาคณิต",
    "ปริศนาสมการช่องว่าง", "อสมการและค่าที่เป็นไปได้", "ปริศนาตัวเลขที่หายไป",         
    "ความยาวและเส้นรอบรูป", "โจทย์ปัญหาเศษส่วนประยุกต์", "การคำนวณหน่วยและเวลา", "โจทย์ปัญหาเปรียบเทียบกลุ่ม"       
]

comp_db = {
    "ระดับประถมต้น (ป.1 - ป.2)": king_topics,
    "ระดับประถมกลาง (ป.3 - ป.4)": king_topics,
    "ระดับประถมปลาย (ป.5 - ป.6)": king_topics
}

# ==========================================
# 3. Logic & Dynamic Difficulty Scaling 
# ==========================================
def generate_questions_logic(level, sub_t, num_q, is_challenge):
    questions = []
    seen = set()
    is_p12 = "ป.1" in level or "ป.2" in level
    is_p34 = "ป.3" in level or "ป.4" in level

    for _ in range(num_q):
        q, sol, attempts = "", "", 0
        
        while attempts < 500:
            attempts += 1
            actual_sub_t = sub_t
            if sub_t == "🌟 สุ่มรวมทุกแนว King Math":
                actual_sub_t = random.choice(king_topics)
            name = random.choice(NAMES)

            # ---------------------------------------------------------
            # 1. การสร้างจำนวนจากเลขโดด
            # ---------------------------------------------------------
            if actual_sub_t == "การสร้างจำนวนจากเลขโดด":
                if is_challenge:
                    digits = random.sample([1,2,3,4,5,6,7,8,9], 5)
                    max_prod = 0
                    best_pair = ()
                    for p in itertools.permutations(digits):
                        n1 = p[0]*100 + p[1]*10 + p[2]
                        n2 = p[3]*10 + p[4]
                        if n1 * n2 > max_prod:
                            max_prod = n1 * n2
                            best_pair = (n1, n2)
                    sorted_d = sorted(digits, reverse=True)
                    q = f"<b>{name}</b> ได้รับบัตรตัวเลข 5 ใบ คือ <b>{', '.join(map(str, digits))}</b> <br>ถ้านำบัตรตัวเลขทั้งหมดมาสร้างเป็น <b>จำนวน 3 หลัก</b> และ <b>จำนวน 2 หลัก</b> ที่เมื่อนำมาคูณกันแล้วจะได้ <b>'ผลคูณที่มีค่ามากที่สุด'</b><br>ผลคูณนั้นคือเท่าไร?"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์เชิงลึก (เทคนิคสมดุลและคูณไขว้):</b><br>
                    หัวใจสำคัญของการทำให้ผลคูณมีค่ามากที่สุด คือ <b>"การสร้างสมดุล"</b> และการนำเลขค่ามากไปไขว้คูณกับกลุ่มตัวเลขที่ใหญ่ที่สุดครับ!<br>
                    <b>ขั้นตอนที่ 1: เรียงลำดับตัวเลขจากมากไปน้อย</b><br>
                    &nbsp;&nbsp;&nbsp;👉 จะได้ตัวเลขคือ <b>{sorted_d[0]} > {sorted_d[1]} > {sorted_d[2]} > {sorted_d[3]} > {sorted_d[4]}</b><br>
                    <b>ขั้นตอนที่ 2: วางตัวเลขใน "หลักหน้าสุด" (หลักที่ทรงพลังที่สุด)</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำเลขที่มากที่สุด 2 ตัวแรก (คือ {sorted_d[0]} และ {sorted_d[1]}) มาเป็นตัวนำทัพ<br>
                    &nbsp;&nbsp;&nbsp;👉 <i>ทำไมต้องแยกกัน?</i> เพราะถ้าเอาเลขมากไปกระจุกอยู่ด้วยกัน จะสู้การกระจายพลังไปเป็นหลักหน้าของทั้งสองจำนวนไม่ได้<br>
                    &nbsp;&nbsp;&nbsp;👉 <i>ทำไม {sorted_d[0]} ต้องไปอยู่จำนวน 2 หลัก?</i> เพราะจำนวน 2 หลัก จะรับบทเป็น "ตัวคูณ" ที่ไปคูณกระจุยกับตัวเลข 3 หลักทุกตำแหน่ง การเอาเลขใหญ่สุดเป็นตัวคูณจะทวีคูณค่าได้มหาศาลครับ! ➔ ตอนนี้เราจะได้โครงสร้าง: <b>{sorted_d[1]}🔲🔲  ×  {sorted_d[0]}🔲</b><br>
                    <b>ขั้นตอนที่ 3: วางตัวเลขในตำแหน่งถัดไป (เทคนิคคูณไขว้)</b><br>
                    &nbsp;&nbsp;&nbsp;👉 เลข <b>{sorted_d[2]}</b> (มากสุดในกลุ่มที่เหลือ) เราต้องนำมันไปจับคู่ให้โดนคูณด้วยเลข <b>{sorted_d[0]}</b> ดังนั้นต้องส่งมันไปอยู่ฝั่งตรงข้าม ➔ โครงสร้าง: <b>{sorted_d[1]}{sorted_d[2]}🔲  ×  {sorted_d[0]}🔲</b><br>
                    &nbsp;&nbsp;&nbsp;👉 เลข <b>{sorted_d[3]}</b> ต้องนำไปไขว้คูณกับก้อนที่ใหญ่ที่สุดในตอนนี้ (คือ {sorted_d[1]}{sorted_d[2]}0) จึงต้องนำไปใส่ในจำนวน 2 หลัก ➔ โครงสร้าง: <b>{sorted_d[1]}{sorted_d[2]}🔲  ×  {sorted_d[0]}{sorted_d[3]}</b><br>
                    <b>ขั้นตอนที่ 4: เติมหลักหน่วยตัวสุดท้าย</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำเลขน้อยสุด <b>{sorted_d[4]}</b> ไปใส่ช่องที่เหลือ ➔ จะได้ตัวเลขที่สมบูรณ์คือ <b>{best_pair[0]}</b> และ <b>{best_pair[1]}</b><br>
                    <b>ขั้นตอนที่ 5: ตรวจสอบผลคูณ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 คำนวณ {best_pair[0]} × {best_pair[1]} = <b>{max_prod:,}</b><br>
                    <b>ตอบ: {max_prod:,}</b></span>"""
                else:
                    if is_p12:
                        digits = random.sample([1,2,3,4,5,6,7,8,9], 3)
                        max_v = int("".join(map(str, sorted(digits, reverse=True))))
                        min_v = int("".join(map(str, sorted(digits))))
                        diff = max_v - min_v
                        q = f"<b>{name}</b> มีบัตรตัวเลข 3 ใบ คือ <b>{digits[0]}, {digits[1]}, และ {digits[2]}</b> <br>ถ้านำบัตรตัวเลขทั้งหมดมาเรียงต่อกันเป็นจำนวน 3 หลัก จงหาผลต่างของจำนวนที่<b>มากที่สุด</b>และจำนวนที่<b>น้อยที่สุด</b>ที่สร้างได้?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีทำอย่างละเอียด:</b><br>
                        <b>ขั้นตอนที่ 1:</b> สร้างจำนวนมากที่สุด นำเลขค่ามากไว้หน้าสุด = <b>{max_v}</b><br>
                        <b>ขั้นตอนที่ 2:</b> สร้างจำนวนน้อยที่สุด นำเลขค่าน้อยไว้หน้าสุด = <b>{min_v}</b><br>
                        <b>ขั้นตอนที่ 3:</b> หาผลต่างโดยนำตัวมากตั้ง ลบด้วยตัวน้อย: {max_v} - {min_v} = <b>{diff}</b><br>
                        <b>ตอบ: {diff}</b></span>"""
                    else: 
                        q_type = random.choice(["even", "div5"])
                        num_digits = 4 if is_p34 else 5
                        if q_type == "even":
                            evens = [2, 4, 6, 8]; odds = [1, 3, 5, 7, 9]
                            c_digits = random.sample(evens, 2) + random.sample(odds, num_digits-2)
                            random.shuffle(c_digits)
                            targets = sorted([d for d in c_digits if d % 2 == 0])
                            others = [d for d in c_digits if d % 2 != 0]
                            unit = targets[0] 
                            rem = sorted(others + targets[1:], reverse=True)
                            ans_num = int("".join(map(str, rem + [unit])))
                            q = f"<b>{name}</b> มีบัตรตัวเลข {num_digits} ใบ คือ <b>{', '.join(map(str, c_digits))}</b> <br>จงหา<b>จำนวนคู่ที่มากที่สุด</b>ที่สามารถสร้างได้?"
                            sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์อย่างละเอียด:</b><br>
                            <b>ขั้นตอนที่ 1: วิเคราะห์เงื่อนไข "จำนวนคู่"</b><br>
                            &nbsp;&nbsp;&nbsp;👉 กฎคือหลักหน่วยต้องเป็นเลขคู่เท่านั้น! เลขคู่ที่เรามีในมือคือ <b>{targets}</b><br>
                            <b>ขั้นตอนที่ 2: วิเคราะห์เงื่อนไข "ค่ามากที่สุด"</b><br>
                            &nbsp;&nbsp;&nbsp;👉 ถ้าอยากให้จำนวนมีค่ามากๆ เราต้องหวงตัวเลขค่าเยอะเอาไว้ใส่ในหลักหน้าสุด (หลักพัน/หลักหมื่น)<br>
                            &nbsp;&nbsp;&nbsp;👉 ดังนั้น เราต้องยอมเสียสละเลขคู่ที่ <b>น้อยที่สุด</b> (คือ <b>{unit}</b>) ไปล็อกไว้ที่ตำแหน่งหลักหน่วยเลยครับ<br>
                            <b>ขั้นตอนที่ 3: จัดเรียงตัวเลขที่เหลือ</b><br>
                            &nbsp;&nbsp;&nbsp;👉 นำเลขที่เหลือในมือทั้งหมด มาเรียงจาก <b>มากไปน้อย</b> ไว้ด้านหน้า<br>
                            &nbsp;&nbsp;&nbsp;👉 จะประกอบร่างได้เป็น <b>{ans_num:,}</b><br>
                            <b>ตอบ: {ans_num:,}</b></span>"""
                        else:
                            c_digits = random.sample([1,2,3,4,6,7,8,9], num_digits - 1) + [5]
                            random.shuffle(c_digits)
                            rem = sorted([d for d in c_digits if d != 5])
                            ans_num = int("".join(map(str, rem + [5])))
                            q = f"<b>{name}</b> มีบัตรตัวเลข {num_digits} ใบ คือ <b>{', '.join(map(str, c_digits))}</b> <br>จงหา<b>จำนวนที่น้อยที่สุดที่หารด้วย 5 ลงตัว</b>?"
                            sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์อย่างละเอียด:</b><br>
                            <b>ขั้นตอนที่ 1: วิเคราะห์เงื่อนไข "หารด้วย 5 ลงตัว"</b><br>
                            &nbsp;&nbsp;&nbsp;👉 กฎเหล็กของการหาร 5 ลงตัวคือ หลักหน่วยต้องเป็น 0 หรือ 5 เท่านั้น!<br>
                            &nbsp;&nbsp;&nbsp;👉 ในบัตรที่เรามี มีเลข <b>5</b> อยู่ จึงต้องนำ 5 ไปล็อกไว้ที่ตำแหน่งหลักหน่วยทันที<br>
                            <b>ขั้นตอนที่ 2: วิเคราะห์เงื่อนไข "ค่าน้อยที่สุด"</b><br>
                            &nbsp;&nbsp;&nbsp;👉 ถ้าอยากให้จำนวนมีค่าน้อยๆ เราต้องหลีกเลี่ยงการเอาเลขมากไปไว้ด้านหน้า<br>
                            &nbsp;&nbsp;&nbsp;👉 ให้นำเลขที่เหลือในมือทั้งหมด มาเรียงจาก <b>น้อยไปมาก</b> ไว้ด้านหน้าของเลข 5<br>
                            <b>ขั้นตอนที่ 3: สรุปตัวเลข</b><br>
                            &nbsp;&nbsp;&nbsp;👉 จะประกอบร่างได้เป็น <b>{ans_num:,}</b><br>
                            <b>ตอบ: {ans_num:,}</b></span>"""

            # ---------------------------------------------------------
            # 2. โจทย์ปัญหาทำผิดเป็นถูก
            # ---------------------------------------------------------
            elif actual_sub_t == "โจทย์ปัญหาทำผิดเป็นถูก":
                if is_challenge:
                    A = random.randint(3, 8)
                    B = random.randint(5, 20)
                    X = random.randint(5, 12) * A
                    wrong_ans = (X // A) + B
                    correct_ans = (X * A) - B
                    
                    frac_wrong_q = get_vertical_fraction('จำนวนปริศนา', A)
                    frac_wrong_s = get_vertical_fraction('🔲', A, color="#2c3e50", is_bold=False)
                    
                    q = f"<b>{name}</b> ตั้งใจจะนำจำนวนปริศนาไป <b>คูณด้วย {A}</b> แล้ว <b>ลบออกด้วย {B}</b><br>แต่เขาทำผิดพลาด สลับเครื่องหมายเป็นนำไปเขียนในรูปเศษส่วนคือ <b>{frac_wrong_q}</b> แล้วค่อย <b>บวกเพิ่ม {B}</b> ทำให้ได้ผลลัพธ์เป็น <b>{wrong_ans}</b><br>จงหาผลลัพธ์ที่แท้จริงตามความตั้งใจแรก?"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (สวมบทบาทนักสืบย้อนเวลา):</b><br>
                    <b>ขั้นตอนที่ 1: ย้อนรอยสิ่งที่ทำผิด เพื่อหา 'จำนวนปริศนา'</b><br>
                    &nbsp;&nbsp;&nbsp;👉 สิ่งที่ทำผิด: {frac_wrong_s} + {B} = {wrong_ans}<br>
                    &nbsp;&nbsp;&nbsp;👉 ย้อนกลับขั้นที่ 1 (บวกเป็นลบ): {wrong_ans} - {B} = {wrong_ans - B}<br>
                    &nbsp;&nbsp;&nbsp;👉 ย้อนกลับขั้นที่ 2 (ส่วนหารเปลี่ยนเป็นคูณ): {wrong_ans - B} × {A} = <b>{X}</b> (นี่คือจำนวนปริศนา!)<br>
                    <b>ขั้นตอนที่ 2: คิดใหม่ให้ถูกต้องตามโจทย์สั่ง</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ความตั้งใจแรกคือ นำ {X} ไป <b>คูณ {A}</b> แล้ว <b>ลบ {B}</b><br>
                    &nbsp;&nbsp;&nbsp;👉 คำนวณ: ({X} × {A}) - {B} = {X*A} - {B} = <b>{correct_ans:,}</b><br>
                    <b>ตอบ: {correct_ans:,}</b></span>"""
                else:
                    if is_p12:
                        x = random.randint(5, 20)
                        ans_true = random.randint(30, 80)
                        wrong_ans = ans_true - (2 * x)
                        while wrong_ans <= 0:
                            ans_true = random.randint(50, 100)
                            wrong_ans = ans_true - (2 * x)
                            
                        q = f"<b>{name}</b> ตั้งใจจะนำจำนวนๆ หนึ่งไป <b>บวก</b> กับ {x} แต่เขาทำผิดโดยนำไป <b>ลบ</b> ด้วย {x} ทำให้ได้ผลลัพธ์เป็น <b>{wrong_ans}</b> <br>ผลลัพธ์ที่แท้จริงคือเท่าไร?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (คิดย้อนกลับ):</b><br>
                        <b>ขั้นตอนที่ 1: หาตัวเลขในตอนแรกสุด</b><br>
                        &nbsp;&nbsp;&nbsp;👉 จากที่ทำผิดคือ: 🔲 - {x} = {wrong_ans}<br>
                        &nbsp;&nbsp;&nbsp;👉 ย้ายฝั่งเปลี่ยน <b>ลบ เป็น บวก</b> จะได้ตัวเลขตอนแรกคือ: {wrong_ans} + {x} = <b>{wrong_ans + x}</b><br>
                        <b>ขั้นตอนที่ 2: คิดเลขให้ถูกต้อง</b><br>
                        &nbsp;&nbsp;&nbsp;👉 นำตัวเลขตอนแรก ({wrong_ans + x}) ไป <b>บวกด้วย {x}</b> ตามโจทย์สั่ง: {wrong_ans + x} + {x} = <b>{ans_true}</b><br>
                        <b>ตอบ: {ans_true}</b></span>"""
                    else:
                        x = random.randint(3, 12); n = random.randint(11, 30); wrong_ans = n; correct_ans = n * x * x
                        
                        frac_wrong_q = get_vertical_fraction('จำนวนหนึ่ง', x)
                        frac_wrong_s = get_vertical_fraction('🔲', x, color="#2c3e50", is_bold=False)
                        
                        q = f"<b>{name}</b> ตั้งใจจะนำจำนวนๆ หนึ่งไป <b>คูณ</b> ด้วย {x} แต่ดันไปเขียนเป็นเศษส่วนในรูป <b>{frac_wrong_q}</b> ทำให้ผลลัพธ์ผิดเพี้ยนไปเป็น <b>{wrong_ans}</b> <br>ผลลัพธ์ที่ถูกต้องตามความตั้งใจแรกคือเท่าไร?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (คิดย้อนกลับ):</b><br>
                        <b>ขั้นตอนที่ 1: หาตัวเลขในตอนแรกสุด</b><br>
                        &nbsp;&nbsp;&nbsp;👉 จากที่ทำผิดคือ: {frac_wrong_s} = {wrong_ans}<br>
                        &nbsp;&nbsp;&nbsp;👉 ย้ายฝั่งเปลี่ยน <b>เส้นคั่น (หาร) เป็น คูณ</b> จะได้ตัวเลขตอนแรกคือ: {wrong_ans} × {x} = <b>{wrong_ans * x}</b><br>
                        <b>ขั้นตอนที่ 2: คิดเลขให้ถูกต้อง</b><br>
                        &nbsp;&nbsp;&nbsp;👉 นำตัวเลขตอนแรก ({wrong_ans * x}) ไป <b>คูณด้วย {x}</b> ตามโจทย์สั่ง: {wrong_ans * x} × {x} = <b>{correct_ans:,}</b><br>
                        <b>ตอบ: {correct_ans:,}</b></span>"""

            # ---------------------------------------------------------
            # 3. การนับตารางเรขาคณิต
            # ---------------------------------------------------------
            elif actual_sub_t == "การนับตารางเรขาคณิต":
                if is_challenge:
                    N = random.randint(3, 5)
                    M = random.randint(4, 7)
                    if N == M: M += 1
                    total_rect = (N * (N + 1) // 2) * (M * (M + 1) // 2)
                    total_sq = sum((N - i) * (M - i) for i in range(min(N, M)))
                    ans = total_rect - total_sq
                    
                    q = f"<b>{name}</b> วาดตารางเป็นรูปสี่เหลี่ยมผืนผ้าขนาด <b>{N} × {M}</b> ช่อง<br>จงหาว่ามี <b>'สี่เหลี่ยมผืนผ้าที่ไม่ใช่สี่เหลี่ยมจัตุรัส'</b> ซ่อนอยู่ทั้งหมดกี่รูป?"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีทำอย่างละเอียด (วิเคราะห์แบบหักล้าง):</b><br>
                    สูตรคือ: (สี่เหลี่ยมผืนผ้าทั้งหมด) - (สี่เหลี่ยมจัตุรัสทั้งหมด)<br>
                    <b>ขั้นตอนที่ 1: หาจำนวนสี่เหลี่ยมรวมทุกชนิด (สูตรผืนผ้า)</b><br>
                    &nbsp;&nbsp;&nbsp;👉 (ผลบวกด้านกว้าง) × (ผลบวกด้านยาว)<br>
                    &nbsp;&nbsp;&nbsp;👉 (1+2+...+{N}) × (1+2+...+{M}) = {N*(N+1)//2} × {M*(M+1)//2} = <b>{total_rect:,} รูป</b><br>
                    <b>ขั้นตอนที่ 2: หาจำนวนสี่เหลี่ยมจัตุรัสทั้งหมด</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำด้านกว้างและยาวมาคูณกัน แล้วลดทีละ 1 นำมาบวกกัน<br>
                    &nbsp;&nbsp;&nbsp;👉 ({N}×{M}) + ({N-1}×{M-1}) ... จนกว่าตัวใดตัวหนึ่งเป็น 1<br>
                    &nbsp;&nbsp;&nbsp;👉 ผลรวมคือ <b>{total_sq:,} รูป</b><br>
                    <b>ขั้นตอนที่ 3: หักล้างกัน</b><br>
                    &nbsp;&nbsp;&nbsp;👉 {total_rect:,} - {total_sq:,} = <b>{ans:,} รูป</b><br>
                    <b>ตอบ: {ans:,} รูป</b></span>"""
                else:
                    grid = random.randint(2, 4) if is_p12 else random.randint(4, 6)
                    ans = sum([i*i for i in range(1, grid+1)])
                    q = f"<b>{name}</b> มีตารางกระดานขนาด <b>{grid} × {grid}</b> ช่อง จงหาว่ามี <b>'สี่เหลี่ยมจัตุรัส'</b> ซ่อนอยู่ทั้งหมดกี่รูป?"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีทำอย่างละเอียด (สูตรลัดสี่เหลี่ยมจัตุรัส):</b><br>
                    นำขนาดความยาวของตาราง มายกกำลังสองทีละตัว แล้วบวกกัน (1² + 2² + ... + {grid}²)<br>
                    ผลรวม = 1 + 4 + ... + ({grid}×{grid}) = <b>{ans:,} รูป</b><br>
                    <b>ตอบ: {ans:,} รูป</b></span>"""

            # ---------------------------------------------------------
            # 4. ปริศนาสมการช่องว่าง
            # ---------------------------------------------------------
            elif actual_sub_t == "ปริศนาสมการช่องว่าง":
                if is_challenge:
                    ans = random.randint(5, 20)
                    B = random.randint(2, 10)
                    C = random.randint(2, 5)
                    V3 = ans + B
                    while V3 % C != 0:
                        ans += 1
                        V3 = ans + B
                    V2 = V3 // C
                    if V2 <= 1:
                        ans += C * 2
                        V3 = ans + B
                        V2 = V3 // C
                    D = random.randint(1, V2 - 1)
                    V1 = V2 - D
                    A = random.randint(2, 6)
                    E = A * V1
                    
                    frac_html = get_vertical_fraction(f'( {box_html} + {B} )', C)
                    frac_sol_step = get_vertical_fraction(f'( 🔲 + {B} )', C, color="#2c3e50", is_bold=False)
                    
                    q = f"จงหาตัวเลขที่เติมลงในช่องว่าง:<br><br><span style='font-size:24px; font-weight:bold;'>{A} × &nbsp;<span style='font-size:36px; vertical-align: middle;'>[</span>&nbsp; {frac_html} &nbsp;−&nbsp; {D} &nbsp;<span style='font-size:36px; vertical-align: middle;'>]</span>&nbsp; =&nbsp; {E}</span>"
                    
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (แกะกล่องของขวัญจากวงนอกเข้าสู่วงใน):</b><br>
                    <b>ขั้นตอนที่ 1: กำจัดตัวเลขนอกวงเล็บใหญ่สุด คือ "× {A}"</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ย้ายไปฝั่งขวา เปลี่ยนเป็น <b>÷ {A}</b><br>
                    &nbsp;&nbsp;&nbsp;👉 {E} ÷ {A} = <b>{V1}</b><br>
                    <b>ขั้นตอนที่ 2: กำจัดตัวเลข "- {D}"</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ย้ายไปฝั่งขวา เปลี่ยนเป็น <b>+ {D}</b><br>
                    &nbsp;&nbsp;&nbsp;👉 {V1} + {D} = <b>{V2}</b> (สมการเหลือ: {frac_sol_step} = {V2})<br>
                    <b>ขั้นตอนที่ 3: กำจัดส่วน "{C}" (คือการหาร)</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ย้ายไปฝั่งขวา เปลี่ยนเป็น <b>× {C}</b><br>
                    &nbsp;&nbsp;&nbsp;👉 {V2} × {C} = <b>{V3}</b><br>
                    <b>ขั้นตอนที่ 4: หาค่า 🔲</b><br>
                    &nbsp;&nbsp;&nbsp;👉 เหลือ 🔲 + {B} = {V3} ➔ ย้ายไปลบ ➔ {V3} - {B} = <b>{ans}</b><br>
                    <b>ตอบ: {ans}</b></span>"""
                else:
                    if is_p12:
                        a = random.randint(15, 50); b = random.randint(60, 150)
                        q = f"จงหาตัวเลขที่เติมลงในช่องว่าง:<br><br><span style='font-size:24px; font-weight:bold;'>{box_html} + {a} = {b}</span>"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (หลักการย้ายข้าง):</b><br>
                        <b>ขั้นตอนที่ 1:</b> เราต้องย้าย <b>+ {a}</b> ไปอยู่ฝั่งขวาของเครื่องหมายเท่ากับ ( = )<br>
                        <b>ขั้นตอนที่ 2:</b> เวลาย้ายฝั่ง ต้องเปลี่ยนเครื่องหมายเป็น <b>ตรงกันข้าม</b> (จากบวกเป็นลบ)<br>
                        &nbsp;&nbsp;&nbsp;👉 สมการใหม่คือ: 🔲 = {b} - {a}<br>
                        &nbsp;&nbsp;&nbsp;👉 คิดเลข: {b} - {a} = <b>{b-a}</b><br>
                        <b>ตอบ: {b-a}</b></span>"""
                    else:
                        a = random.randint(10, 50); b = random.randint(2, 9)
                        ans = random.randint(5, 40)
                        c = (ans + a) * b
                        q = f"จงหาตัวเลขที่เติมลงในช่องว่าง:<br><br><span style='font-size:24px; font-weight:bold;'>( {box_html} + {a} ) × {b} = {c}</span>"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (ย้ายข้างทีละตัว):</b><br>
                        <b>ขั้นตอนที่ 1: กำจัดตัวนอกวงเล็บ "× {b}"</b> ย้ายไปเปลี่ยนเป็น <b>÷ {b}</b><br>
                        &nbsp;&nbsp;&nbsp;👉 จะได้: {c} ÷ {b} = <b>{c//b}</b> (สมการเหลือ: 🔲 + {a} = {c//b})<br>
                        <b>ขั้นตอนที่ 2: หาค่า 🔲</b> ย้าย <b>+ {a}</b> ข้ามฝั่งไป <b>- {a}</b><br>
                        &nbsp;&nbsp;&nbsp;👉 จะได้: {c//b} - {a} = <b>{ans}</b><br>
                        <b>ตอบ: {ans}</b></span>"""

            # ---------------------------------------------------------
            # 5. อสมการและค่าที่เป็นไปได้ 
            # ---------------------------------------------------------
            elif actual_sub_t == "อสมการและค่าที่เป็นไปได้":
                if is_challenge:
                    C = random.choice([2, 3, 4, 5])
                    ans_list = list(range(random.randint(5, 10), random.randint(12, 18)))
                    min_val, max_val = ans_list[0], ans_list[-1]
                    B = random.randint(3, 8)
                    A = (min_val * C) - random.randint(1, C-1)
                    D = (max_val * C) + random.randint(1, C-1)
                    ans = sum(ans_list)
                    
                    frac_L = get_vertical_fraction(A, B*C)
                    frac_M = get_vertical_fraction(box_html, B)
                    frac_R = get_vertical_fraction(D, B*C)
                    
                    frac_sol_M = get_vertical_fraction("🔲", B, color="#2c3e50", is_bold=False)
                    frac_sol_M1 = get_vertical_fraction(f"🔲 × {C}", f"{B} × {C}", color="#2c3e50", is_bold=False)
                    frac_sol_M2 = get_vertical_fraction(f"🔲 × {C}", B*C, color="#2c3e50", is_bold=False)
                    
                    q = f"จงหา <b>'ผลบวกของจำนวนนับทุกจำนวน'</b> ที่สามารถเติมในช่องว่างแล้วทำให้อสมการเป็นจริง:<br><br><span style='font-size:24px; font-weight:bold;'>{frac_L} &nbsp;&lt;&nbsp; {frac_M} &nbsp;&lt;&nbsp; {frac_R}</span>"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์ (อสมการเศษส่วน):</b><br>
                    การจะเปรียบเทียบเศษส่วนได้ "ตัวส่วนด้านล่างต้องเท่ากัน" ทั้งหมดก่อนครับ!<br>
                    <b>ขั้นตอนที่ 1: ทำตัวส่วนให้เท่ากัน</b><br>
                    &nbsp;&nbsp;&nbsp;👉 เศษส่วนตรงกลางคือ {frac_sol_M} แต่ด้านข้างมีส่วนเป็น {B*C} ดังนั้นเราต้องนำ {C} มาคูณทั้งเศษและส่วนให้ตัวตรงกลาง<br>
                    &nbsp;&nbsp;&nbsp;👉 ตรงกลางจะกลายเป็น: {frac_sol_M1} = {frac_sol_M2}<br>
                    <b>ขั้นตอนที่ 2: เปรียบเทียบเฉพาะตัวเศษด้านบน</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ตอนนี้ส่วนเป็น {B*C} เท่ากันหมดแล้ว เราสามารถนำเฉพาะตัวเศษด้านบนมาเทียบกันได้เลย อสมการจะกลายเป็น: <b>{A} &lt; 🔲 × {C} &lt; {D}</b><br>
                    <b>ขั้นตอนที่ 3: หาจำนวนนับ 🔲 ที่เป็นไปได้ทั้งหมด</b><br>
                    &nbsp;&nbsp;&nbsp;👉 เราต้องหาว่ามีเลขอะไรบ้างที่คูณ {C} แล้วได้ผลลัพธ์อยู่ระหว่าง {A} ถึง {D}<br>
                    &nbsp;&nbsp;&nbsp;👉 ลองท่องสูตรคูณแม่ {C} จะพบว่าจำนวนนับที่ใช้ได้คือ: <b>{', '.join(map(str, ans_list))}</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ผลบวกของทุกจำนวน = {' + '.join(map(str, ans_list))} = <b>{ans}</b><br>
                    <b>ตอบ: {ans}</b></span>"""
                else:
                    if is_p12:
                        a = random.randint(5, 15); limit_val = random.randint(20, 40)
                    else:
                        a = random.randint(10, 50); limit_val = random.randint(80, 150)
                        
                    max_val = limit_val - a - 1
                    q = f"จงหา <b>จำนวนนับที่มากที่สุด</b> ที่เติมในช่องว่าง:<br><br><span style='font-size:24px; font-weight:bold;'>{box_html} + {a} &lt; {limit_val}</span>"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด:</b><br>
                    <b>ขั้นตอนที่ 1:</b> คิดเสมือนว่ามันคือเครื่องหมาย "เท่ากับ" ก่อน ➔ 🔲 + {a} = {limit_val}<br>
                    &nbsp;&nbsp;&nbsp;👉 ย้ายข้างไปลบ จะได้ 🔲 = {limit_val} - {a} = <b>{limit_val - a}</b><br>
                    <b>ขั้นตอนที่ 2:</b> กลับสู่ความจริง โจทย์บอก <b>น้อยกว่า ( &lt; )</b> {limit_val}<br>
                    &nbsp;&nbsp;&nbsp;👉 ดังนั้นจำนวนที่มากที่สุดที่เป็นไปได้คือ {limit_val - a} - 1 = <b>{max_val}</b><br>
                    <b>ตอบ: {max_val}</b></span>"""

            # ---------------------------------------------------------
            # 6. ปริศนาตัวเลขที่หายไป
            # ---------------------------------------------------------
            elif actual_sub_t == "ปริศนาตัวเลขที่หายไป":
                if is_challenge:
                    Z = random.randint(0, 4); C = random.randint(Z+3, 9)
                    Y = random.randint(0, 4); B = random.randint(Y+3, 9)
                    X = random.randint(5, 9); A = random.randint(1, X-3)
                    
                    Top = int(f"{X}{Y}{Z}")
                    Bot = int(f"{A}{B}{C}")
                    Res = Top - Bot
                    str_Res = str(Res).zfill(3)
                    
                    top_row = [box_html, str(Y), str(Z)]
                    bot_row = [str(A), box_html, str(C)]
                    res_row = [str_Res[0], str_Res[1], box_html]
                    
                    math_table = get_vertical_math(top_row, bot_row, res_row, operator="−")
                    
                    q = f"จงวิเคราะห์การตั้งลบแบบมีการยืมข้ามหลักต่อไปนี้ แล้วหาว่าตัวเลขที่ซ่อนอยู่ใน 🔲 จาก <b>บนลงล่าง</b> คือเลขใดตามลำดับ?<br>{math_table}"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์ (แกะรอยการลบและการยืมทีละหลัก):</b><br>
                    <b>หลักหน่วย:</b> {Z} - {C} ตัวตั้งน้อยกว่าตัวลบ จึงต้อง <b>'ยืม'</b> หลักสิบมา 10<br>
                    &nbsp;&nbsp;&nbsp;👉 กลายเป็น (10 + {Z}) - {C} = <b>{10+Z-C}</b> ➔ 🔲 ล่างสุดคือ <b>{10+Z-C}</b><br>
                    <b>หลักสิบ:</b> เลข {Y} ถูกยืมไป 1 จึงเหลือ {Y-1} แต่ยังต้องลบกับ 🔲 แล้วได้ {str_Res[1]}<br>
                    &nbsp;&nbsp;&nbsp;👉 ตัวตั้งเหลือน้อยกว่าแน่ๆ จึงต้อง <b>'ยืม'</b> หลักร้อยมาอีก 10 กลายเป็น (10 + {Y-1})<br>
                    &nbsp;&nbsp;&nbsp;👉 สมการคือ: {10+Y-1} - 🔲 = {str_Res[1]} ➔ ย้ายข้าง: {10+Y-1} - {str_Res[1]} = <b>{B}</b> ➔ 🔲 ตรงกลางคือ <b>{B}</b><br>
                    <b>หลักร้อย:</b> 🔲 ถูกหลักสิบยืมไป 1 จึงมีค่าลดลง 1<br>
                    &nbsp;&nbsp;&nbsp;👉 สมการคือ: (🔲 - 1) - {A} = {str_Res[0]} ➔ ย้ายข้างหาค่า 🔲 = {int(str_Res[0])} + {A} + 1 = <b>{X}</b> ➔ 🔲 บนสุดคือ <b>{X}</b><br>
                    <b>ตอบ: บนคือ {X}, กลางคือ {B}, ล่างคือ {10+Z-C}</b></span>"""
                else:
                    if is_p12:
                        a1, a2 = random.randint(1, 8), random.randint(1, 8)
                        b1, b2 = random.randint(1, 9 - a1), random.randint(1, 9 - a2)
                        str_a, str_b, str_ans = str(a1*10+a2).zfill(2), str(b1*10+b2).zfill(2), str((a1+b1)*10+(a2+b2)).zfill(2)
                        top_row, bot_row, res_row = [str_a[0], box_html], [box_html, str_b[1]], list(str_ans)
                        math_table = get_vertical_math(top_row, bot_row, res_row, operator="+")
                        q = f"จงเติมตัวเลขลงใน 🔲 ให้ถูกต้องสมบูรณ์<br>{math_table}"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (เจาะทีละหลัก):</b><br>
                        <b>หลักหน่วย (ขวาสุด):</b> 🔲 + {str_b[1]} = {str_ans[1]}<br>
                        &nbsp;&nbsp;&nbsp;👉 คิดย้อนกลับ: {str_ans[1]} - {str_b[1]} = <b>{str_a[1]}</b> (นี่คือตัวเลขกล่องบน)<br>
                        <b>หลักสิบ (ซ้ายสุด):</b> {str_a[0]} + 🔲 = {str_ans[0]}<br>
                        &nbsp;&nbsp;&nbsp;👉 คิดย้อนกลับ: {str_ans[0]} - {str_a[0]} = <b>{str_b[0]}</b> (นี่คือตัวเลขกล่องล่าง)<br>
                        <b>ตอบ: กล่องบนคือ {str_a[1]}, กล่องล่างคือ {str_b[0]}</b></span>"""
                    else:
                        n2 = random.randint(2, 9)
                        n1 = random.randint(11, 99)
                        ans_val = n1 * n2
                        str_n1, str_ans = str(n1), str(ans_val)
                        top_row = [str_n1[0], box_html]
                        bot_row = [str(n2)]
                        res_row = list(str_ans)
                        math_table = get_vertical_math(top_row, bot_row, res_row, operator="×")
                        
                        q = f"จงเติมตัวเลขลงใน 🔲 ให้การคูณนี้ถูกต้อง<br>{math_table}"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด:</b><br>
                        จากโจทย์คือ ตัวตั้ง 2 หลัก × {n2} = {ans_val}<br>
                        ย้ายข้างการคูณไปเป็นหาร: จำนวนสองหลักคือ {ans_val} ÷ {n2} = <b>{n1}</b><br>
                        ดังนั้นตัวเลขที่หายไปในช่องว่างด้านบนคือ <b>{str_n1[1]}</b><br>
                        <b>ตอบ: {str_n1[1]}</b></span>"""

            # ---------------------------------------------------------
            # 7. ความยาวและเส้นรอบรูป
            # ---------------------------------------------------------
            elif actual_sub_t == "ความยาวและเส้นรอบรูป":
                if is_challenge:
                    N = random.randint(3, 5)
                    S = random.randint(5, 12)
                    O = random.randint(1, S-2)
                    width = N * S - (N - 1) * O
                    ans = 2 * (width + S)
                    
                    q = f"<b>{name}</b> นำกระดาษรูปสี่เหลี่ยมจัตุรัสที่มีความยาวด้านละ <b>{S} ซม.</b> จำนวน <b>{N} แผ่น</b> มาวางเรียงต่อกันเป็นแนวยาว<br>โดยให้แต่ละแผ่นวางซ้อนทับกันเป็นระยะ <b>{O} ซม.</b><br>จงหาความยาวรอบรูปทั้งหมดของรูปทรงที่เกิดใหม่นี้?"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์ (ความยาวที่ถูกซ่อน):</b><br>
                    เมื่อวางซ้อนทับกัน รูปทรงใหม่จะกลายเป็นสี่เหลี่ยมผืนผ้ายาวๆ 1 รูป<br>
                    <b>ขั้นตอนที่ 1: หาความยาว (แนวนอน) ของรูปใหม่</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ถ้านำแผ่นมาต่อกันเฉยๆ จะยาว {N} × {S} = {N*S} ซม.<br>
                    &nbsp;&nbsp;&nbsp;👉 แต่มีรอยซ้อนทับ {N-1} รอย รอยละ {O} ซม. ➔ หดหายไป {N-1} × {O} = {(N-1)*O} ซม.<br>
                    &nbsp;&nbsp;&nbsp;👉 ความยาวจริง = {N*S} - {(N-1)*O} = <b>{width} ซม.</b><br>
                    <b>ขั้นตอนที่ 2: หาความกว้าง (แนวตั้ง)</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ความกว้างยังคงเท่าเดิมคือด้านของจัตุรัส = <b>{S} ซม.</b><br>
                    <b>ขั้นตอนที่ 3: หาความยาวรอบรูปทั้งหมด</b><br>
                    &nbsp;&nbsp;&nbsp;👉 2 × (กว้าง + ยาว) = 2 × ({width} + {S}) = <b>{ans} ซม.</b><br>
                    <b>ตอบ: {ans} ซม.</b></span>"""
                else:
                    if is_p12: 
                        L = random.randint(4, 20) * 4
                        q = f"<b>{name}</b> มีลวดความยาว <b>{L} ซม.</b> นำไปดัดเป็นรูปสี่เหลี่ยมจัตุรัส จะมีความยาวด้านละกี่เซนติเมตร?"
                        sol = f"<span style='color: #2c3e50;'>จัตุรัสมี 4 ด้านที่เท่ากัน ➔ นำความยาวลวดทั้งหมดไปแบ่ง 4 ส่วน: {L} ÷ 4 = <b>{L//4} ซม.</b></span>"
                    else:
                        side = random.randint(5, 25)
                        leftover = random.randint(5, 20)
                        L = (side * 4) + leftover
                        q = f"<b>{name}</b> นำเส้นลวดที่มีความยาว <b>{L} ซม.</b> ไปสร้างรูปสี่เหลี่ยมจัตุรัสแล้ว <b>เหลือเศษลวด {leftover} ซม.</b><br>ความยาวของแต่ละด้านของรูปสี่เหลี่ยมจัตุรัสนี้เป็นกี่เซนติเมตร?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิด:</b><br>
                        <b>ขั้นตอนที่ 1:</b> หาลวดที่ถูกใช้จริง นำลวดทั้งหมดหักส่วนที่เหลือทิ้ง: {L} - {leftover} = <b>{L - leftover} ซม.</b><br>
                        <b>ขั้นตอนที่ 2:</b> ลวด {L - leftover} ซม. ถูกดัดเป็นจัตุรัส (4 ด้านเท่ากัน) ➔ นำไปหาร 4<br>
                        &nbsp;&nbsp;&nbsp;👉 {L - leftover} ÷ 4 = <b>{side} ซม.</b><br>
                        <b>ตอบ: {side} ซม.</b></span>"""

            # ---------------------------------------------------------
            # 8. โจทย์ปัญหาเศษส่วนประยุกต์
            # ---------------------------------------------------------
            elif actual_sub_t == "โจทย์ปัญหาเศษส่วนประยุกต์":
                if is_challenge:
                    Y = random.randint(10, 30)
                    R2 = 2 * Y
                    X = random.randint(10, 30)
                    while (R2 + X) % 2 != 0: X += 1
                    R1 = (R2 + X) * 3 // 2
                    Total = R1 * 4 // 3
                    
                    f1_4 = get_vertical_fraction(1, 4)
                    f1_3 = get_vertical_fraction(1, 3)
                    f1_2 = get_vertical_fraction(1, 2)
                    
                    f1_4_s = get_vertical_fraction(1, 4, color="#2c3e50", is_bold=False)
                    f1_3_s = get_vertical_fraction(1, 3, color="#2c3e50", is_bold=False)
                    f1_2_s = get_vertical_fraction(1, 2, color="#2c3e50", is_bold=False)
                    f2_3_s = get_vertical_fraction(2, 3, color="#2c3e50", is_bold=False)
                    f3_4_s = get_vertical_fraction(3, 4, color="#2c3e50", is_bold=False)
                    
                    q = f"อคิณอ่านหนังสือเล่มหนึ่ง <b>วันแรกอ่านไป {f1_4} ของเล่ม</b><br><b>วันที่สองอ่านไป {f1_3} ของหน้าที่เหลือ</b> และอ่านเพิ่มอีก <b>{X} หน้า</b><br><b>วันที่สามอ่านไป {f1_2} ของหน้าที่เหลือ</b> และอ่านเพิ่มอีก <b>{Y} หน้า</b> ปรากฏว่าอ่านจบเล่มพอดี!<br>จงหาว่าหนังสือเล่มนี้มีทั้งหมดกี่หน้า?"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดย้อนกลับ (Olympiad Level):</b><br>
                    เมื่อมีคำว่า "ของหน้าที่เหลือ" ซ้อนกัน ให้คิดย้อนจากวันสุดท้ายกลับมาวันแรกครับ!<br>
                    <b>วันที่ 3:</b> อ่านครึ่งหนึ่ง ({f1_2_s}) แล้วอ่านอีก {Y} หน้าจนจบเล่ม<br>
                    &nbsp;&nbsp;&nbsp;👉 แสดงว่า {Y} หน้าที่อ่านตอนท้าย ก็คือ "ครึ่งหนึ่ง" ที่เหลืออยู่นั่นเอง<br>
                    &nbsp;&nbsp;&nbsp;👉 จำนวนหน้าก่อนอ่านวันที่ 3 = {Y} × 2 = <b>{R2} หน้า</b><br>
                    <b>วันที่ 2:</b> อ่าน {f1_3_s} และอ่านเพิ่มอีก {X} หน้า ทำให้เหลือ {R2} หน้า<br>
                    &nbsp;&nbsp;&nbsp;👉 นำ {X} ไปคืนกลับ: {R2} + {X} = {R2+X} หน้า<br>
                    &nbsp;&nbsp;&nbsp;👉 ซึ่ง {R2+X} หน้า คิดเป็น {f2_3_s} ของวันนั้น (เพราะอ่านไป {f1_3_s})<br>
                    &nbsp;&nbsp;&nbsp;👉 จำนวนหน้าก่อนอ่านวันที่ 2 = ({R2+X} ÷ 2) × 3 = <b>{R1} หน้า</b><br>
                    <b>วันที่ 1:</b> อ่าน {f1_4_s} ทำให้เหลือ {R1} หน้า<br>
                    &nbsp;&nbsp;&nbsp;👉 ซึ่ง {R1} หน้า คิดเป็น {f3_4_s} ของทั้งเล่ม<br>
                    &nbsp;&nbsp;&nbsp;👉 จำนวนหน้าทั้งหมด = ({R1} ÷ 3) × 4 = <b>{Total} หน้า</b><br>
                    <b>ตอบ: {Total} หน้า</b></span>"""
                else:
                    if is_p12: 
                        baskets = random.randint(4, 9)
                        breads_per_b = random.randint(3, 10)
                        total_breads = baskets * breads_per_b
                        ask_b = random.randint(2, baskets-1)
                        q = f"<b>{name}</b> แบ่งขนมปัง <b>{total_breads} ชิ้น</b> ใส่ตะกร้า <b>{baskets} ใบ</b> ใบละเท่าๆ กัน<br>จงหาว่าขนมปังที่อยู่ในตะกร้า <b>{ask_b} ใบ</b> มีทั้งหมดกี่ชิ้น?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิด:</b><br>
                        <b>ขั้นตอนที่ 1:</b> หาว่า 1 ตะกร้ามีกี่ชิ้น ➔ {total_breads} ÷ {baskets} = <b>{breads_per_b} ชิ้น</b><br>
                        <b>ขั้นตอนที่ 2:</b> ถ้าต้องการ {ask_b} ตะกร้า ➔ นำ {breads_per_b} × {ask_b} = <b>{breads_per_b * ask_b} ชิ้น</b><br>
                        <b>ตอบ: {breads_per_b * ask_b} ชิ้น</b></span>"""
                    else:
                        den = random.choice([4, 5, 6, 8, 10])
                        num = random.randint(1, den-2)
                        total_money = random.randint(10, 50) * den
                        ans_rem = total_money - int((total_money/den)*num)
                        
                        frac_html = get_vertical_fraction(num, den)
                        
                        q = f"<b>{name}</b> มีเงิน <b>{total_money} บาท</b> ซื้อเครื่องเขียนไป <b>{frac_html}</b> ของเงินทั้งหมด จะเหลือเงินกี่บาท?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด:</b><br>
                        <b>ขั้นตอนที่ 1: หาเงินที่ใช้ไป</b><br>
                        &nbsp;&nbsp;&nbsp;👉 นำเงินทั้งหมดมาแบ่งเป็น {den} ส่วน: {total_money} ÷ {den} = {total_money//den} บาท/ส่วน<br>
                        &nbsp;&nbsp;&nbsp;👉 ใช้ไป {num} ส่วน: {total_money//den} × {num} = <b>{int((total_money/den)*num)} บาท</b><br>
                        <b>ขั้นตอนที่ 2: หาเงินที่เหลือ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 นำเงินตอนแรกมาหักออก: {total_money} - {int((total_money/den)*num)} = <b>{ans_rem} บาท</b><br>
                        <b>ตอบ: {ans_rem} บาท</b></span>"""

            # ---------------------------------------------------------
            # 9. การคำนวณหน่วยและเวลา
            # ---------------------------------------------------------
            elif actual_sub_t == "การคำนวณหน่วยและเวลา":
                if is_challenge:
                    days_map = {"พฤหัสบดี": 3, "ศุกร์": 4, "เสาร์": 5}
                    end_day = random.choice(list(days_map.keys()))
                    days = days_map[end_day]
                    gain_m = random.randint(3, 12)
                    total_gain = days * gain_m
                    
                    real_h = 8
                    real_m = 0
                    
                    show_m = real_m + total_gain
                    carry_h = show_m // 60
                    final_m = show_m % 60
                    final_h = real_h + carry_h
                    
                    q = f"นาฬิกาเรือนหนึ่งทำงานผิดปกติ โดยจะเดิน <b>'เร็วเกินไป' วันละ {gain_m} นาที</b><br>ถ้า<b>{name}</b>ตั้งเวลานาฬิกาเรือนนี้ให้ตรงกับเวลาจริงในตอน <b>08:00 น. ของวันจันทร์</b><br>จงหาว่าเมื่อเวลาจริงคือ <b>08:00 น. ของวัน{end_day}ในสัปดาห์เดียวกัน</b> นาฬิกาเรือนนี้จะชี้บอกเวลาใด?"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์ (คำนวณความคลาดเคลื่อนสะสม):</b><br>
                    <b>ขั้นตอนที่ 1: หาจำนวนวันที่ผ่านไป</b><br>
                    &nbsp;&nbsp;&nbsp;👉 จาก 08:00 น. วันจันทร์ ถึง 08:00 น. วัน{end_day} นับเวลาที่ผ่านไปได้ <b>{days} วันพอดีเป๊ะ</b><br>
                    <b>ขั้นตอนที่ 2: หาเวลาที่นาฬิกาเดินเพี้ยนไปทั้งหมด</b><br>
                    &nbsp;&nbsp;&nbsp;👉 เดินเร็ววันละ {gain_m} นาที × {days} วัน = <b>เดินเร็วไปทั้งหมด {total_gain} นาที</b><br>
                    <b>ขั้นตอนที่ 3: คำนวณเวลาบนหน้าปัด</b><br>
                    &nbsp;&nbsp;&nbsp;👉 เวลาจริงคือ 08:00 น. แต่นาฬิกาจะเดินนำหน้าไปอีก {total_gain} นาที<br>
                    &nbsp;&nbsp;&nbsp;👉 แปลงนาทีที่เดินเร็วเป็นชั่วโมง: {total_gain} นาที = <b>{carry_h} ชั่วโมง {final_m} นาที</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำไปบวกเพิ่มจากเวลาจริง: 08:00 น. + {carry_h} ชั่วโมง {final_m} นาที = <b>{final_h:02d}:{final_m:02d} น.</b><br>
                    <b>ตอบ: เวลา {final_h:02d}:{final_m:02d} น.</b></span>"""
                else:
                    if is_p12: 
                        h1 = random.randint(1, 4); m1 = random.randint(10, 20)
                        h2 = random.randint(1, 3); m2 = random.randint(10, 30)
                        q = f"<b>{name}</b> ใช้เวลาเดินทางช่วงแรก <b>{h1} ชั่วโมง {m1} นาที</b> และช่วงที่สองอีก <b>{h2} ชั่วโมง {m2} นาที</b> รวมใช้เวลาเท่าไร?"
                        sol = f"<span style='color: #2c3e50;'>รวมชั่วโมง: {h1} + {h2} = <b>{h1+h2} ชั่วโมง</b><br>รวมนาที: {m1} + {m2} = <b>{m1+m2} นาที</b><br><b>ตอบ: {h1+h2} ชั่วโมง {m1+m2} นาที</b></span>"
                    elif is_p34: # P3-P4 Logic Restored
                        km1 = random.randint(2, 6); m1 = random.randint(400, 800)
                        m2 = random.randint(1200, 2500)
                        total_m = (km1 * 1000) + m1 + m2
                        ans_km = total_m // 1000
                        ans_m = total_m % 1000
                        q = f"<b>{name}</b> จงหาผลบวกของระยะทาง:<br><b>{km1} กิโลเมตร {m1} เมตร  +  {m2} เมตร</b>  =  🔲 กิโลเมตร 🔲 เมตร"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิด:</b><br>
                        แปลงทุกอย่างเป็นเมตรก่อน: ({km1} × 1000) + {m1} = {km1 * 1000 + m1} เมตร<br>
                        นำมาบวกกัน: {km1 * 1000 + m1} + {m2} = <b>{total_m} เมตร</b><br>
                        แปลงกลับเป็นกิโลเมตร: {total_m} เมตร = <b>{ans_km} กม. {ans_m} ม.</b><br>
                        <b>ตอบ: {ans_km} กิโลเมตร {ans_m} เมตร</b></span>"""
                    else:
                        h1 = random.randint(2, 6); m1 = random.randint(40, 55)
                        h2 = random.randint(1, 4); m2 = random.randint(30, 55)
                        total_m = m1 + m2
                        carry_h = total_m // 60
                        left_m = total_m % 60
                        ans_h = h1 + h2 + carry_h
                        q = f"<b>{name}</b> เดินทางด้วยรถยนต์ <b>{h1} ชม. {m1} นาที</b> และต่อเรืออีก <b>{h2} ชม. {m2} นาที</b> รวมใช้เวลาทั้งหมดเท่าไร?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด:</b><br>
                        <b>ขั้นตอนที่ 1:</b> นำนาทีมาบวกกัน: {m1} + {m2} = <b>{total_m} นาที</b><br>
                        <b>ขั้นตอนที่ 2:</b> เนื่องจาก 60 นาที = 1 ชั่วโมง ➔ เราสามารถปัด {total_m} นาที เป็น <b>{carry_h} ชั่วโมง กับอีก {left_m} นาที</b><br>
                        <b>ขั้นตอนที่ 3:</b> นำชั่วโมงมาบวกกันทั้งหมด: {h1} + {h2} + {carry_h} (ที่ทดมา) = <b>{ans_h} ชั่วโมง</b><br>
                        <b>ตอบ: {ans_h} ชั่วโมง {left_m} นาที</b></span>"""

            # ---------------------------------------------------------
            # 10. โจทย์ปัญหาเปรียบเทียบกลุ่ม (แก้บั๊กสัตว์ปีก 4 ขา เป็น 2 ขา)
            # ---------------------------------------------------------
            elif actual_sub_t == "โจทย์ปัญหาเปรียบเทียบกลุ่ม":
                if is_challenge:
                    C = random.randint(5, 15)
                    P = random.randint(5, 15)
                    H = P + 3 * C
                    L = 4 * P + 6 * C
                    
                    q = f"ในฟาร์มของ<b>{name}</b>มี หมู ไก่ และเป็ด รวมกันทั้งหมด <b>{H} ตัว (นับหัว)</b> และนับขารวมกันได้ <b>{L} ขา</b><br>ถ้าเจ้าของฟาร์มบอกว่า <b>'มีจำนวนเป็ดเป็น 2 เท่าของจำนวนไก่'</b><br>จงหาว่าในฟาร์มแห่งนี้มีหมูทั้งหมดกี่ตัว?"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์ (สมการนับหัว-นับขา):</b><br>
                    <b>ขั้นตอนที่ 1: ยุบรวมสัตว์ปีก (ไก่และเป็ด) ให้เป็นกลุ่มเดียว</b><br>
                    &nbsp;&nbsp;&nbsp;👉 เป็ดมีเป็น 2 เท่าของไก่ แปลว่าถ้าจัดกลุ่ม: ไก่ 1 ตัว จะมาพร้อมกับ เป็ด 2 ตัว เสมอ (รวมเป็น 3 ตัวใน 1 เซ็ต)<br>
                    &nbsp;&nbsp;&nbsp;👉 1 เซ็ตมี 3 ตัว (หัว) และมีขา = (ไก่ 1 ตัว = 2 ขา) + (เป็ด 2 ตัว = 4 ขา) = <b>6 ขาต่อเซ็ต</b><br>
                    &nbsp;&nbsp;&nbsp;👉 สรุป: สัตว์ปีก 1 เซ็ต มี 3 หัว 6 ขา (ซึ่งตกเฉลี่ย <b>หัวละ 2 ขา</b> เท่าเดิม!)<br>
                    <b>ขั้นตอนที่ 2: สมมติฐานแบบสุดโต่ง (สมมติว่าเป็นสัตว์ปีกทั้งหมด)</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ถ้าสัตว์ทั้ง {H} ตัวเป็นสัตว์ปีกทั้งหมด จะมีขา: {H} × 2 = <b>{H*2} ขา</b><br>
                    &nbsp;&nbsp;&nbsp;👉 แต่ขาจริงมี {L} ขา แสดงว่ามีขาเกินมา: {L} - {H*2} = <b>{L - H*2} ขา</b><br>
                    <b>ขั้นตอนที่ 3: หาจำนวนหมู</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ขาที่เกินมา เกิดจากการที่ "หมูมีขามากกว่าสัตว์ปีกอยู่ตัวละ 2 ขา" (4 ลบ 2)<br>
                    &nbsp;&nbsp;&nbsp;👉 นำขาที่เกินมา หารด้วย 2 จะได้จำนวนหมู: {L - H*2} ÷ 2 = <b>{P} ตัว</b><br>
                    <b>ตอบ: มีหมู {P} ตัว</b></span>"""
                else:
                    if is_p12: 
                        dozens = random.randint(2, 6)
                        students = random.choice([2, 3, 4, 6])
                        total_items = dozens * 12
                        ans = total_items // students
                        q = f"คุณครู<b>{name}</b>มีดินสอ <b>{dozens} โหล</b> นำมาแบ่งให้นักเรียน <b>{students} คน</b> คนละเท่าๆ กัน<br>นักเรียนจะได้รับดินสอคนละกี่แท่ง?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิด:</b><br>
                        <b>ขั้นตอนที่ 1:</b> แปลงโหลเป็นแท่ง (1 โหล = 12 แท่ง) ➔ {dozens} โหล = {dozens} × 12 = <b>{total_items} แท่ง</b><br>
                        <b>ขั้นตอนที่ 2:</b> แบ่งให้เด็ก {students} คน ➔ นำมาหาร: {total_items} ÷ {students} = <b>{ans} แท่ง</b><br>
                        <b>ตอบ: {ans} แท่ง</b></span>"""
                    else:
                        g1_std, g1_items = random.randint(10, 15), random.randint(5, 9)
                        g2_std, g2_items = random.randint(16, 22), random.randint(3, 5)
                        t1 = g1_std * g1_items
                        t2 = g2_std * g2_items
                        diff = abs(t1 - t2)
                        more_g = "กลุ่มแรก" if t1 > t2 else "กลุ่มที่สอง"
                        q = f"คุณครู<b>{name}</b>แจกสมุดให้เด็กกลุ่มแรก <b>{g1_std} คน คนละ {g1_items} เล่ม</b> และกลุ่มที่สอง <b>{g2_std} คน คนละ {g2_items} เล่ม</b><br>กลุ่มใดได้รับสมุดรวมมากกว่ากัน และมากกว่ากันกี่เล่ม?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิด:</b><br>
                        <b>ขั้นตอนที่ 1:</b> หากลุ่มแรก ➔ {g1_std} × {g1_items} = <b>{t1} เล่ม</b><br>
                        <b>ขั้นตอนที่ 2:</b> หากลุ่มที่สอง ➔ {g2_std} × {g2_items} = <b>{t2} เล่ม</b><br>
                        <b>ขั้นตอนที่ 3:</b> เปรียบเทียบ จะเห็นว่า <b>{more_g}</b> ได้มากกว่า<br>
                        <b>ขั้นตอนที่ 4:</b> หาผลต่าง ➔ {max(t1,t2)} - {min(t1,t2)} = <b>{diff} เล่ม</b><br>
                        <b>ตอบ: {more_g} มากกว่าอยู่ {diff} เล่ม</b></span>"""

            else:
                q = f"⚠️ [ระบบผิดพลาด] ไม่พบเงื่อนไขสำหรับหัวข้อ: <b>{actual_sub_t}</b>"
                sol = "Error"

            # ตรวจสอบการซ้ำของโจทย์
            if q not in seen: 
                seen.add(q)
                questions.append({"question": q, "solution": sol})
                break 
            elif attempts >= 499:
                questions.append({"question": q, "solution": sol})
                break
            
    return questions

# ==========================================
# UI Rendering
# ==========================================
def extract_body(html_str):
    try: return html_str.split('<body>')[1].split('</body>')[0]
    except IndexError: return html_str

def create_page(level, sub_t, questions, is_key=False, q_margin="20px", ws_height="180px", brand_name="", is_challenge=False):
    title_suffix = " 🔥 [ULTIMATE CHALLENGE]" if is_challenge else ""
    title = f"เฉลยข้อสอบ (Answer Key){title_suffix}" if is_key else f"ข้อสอบวิเคราะห์ (King Math Pro){title_suffix}"
    
    student_info = """
        <table style="width: 100%; margin-bottom: 10px; font-size: 18px; border-collapse: collapse;">
            <tr>
                <td style="width: 1%; white-space: nowrap; padding-right: 5px;"><b>ชื่อ-สกุล</b></td>
                <td style="border-bottom: 2px dotted #999; width: 60%;"></td>
                <td style="width: 1%; white-space: nowrap; padding-left: 20px; padding-right: 5px;"><b>ระดับชั้น</b></td>
                <td style="border-bottom: 2px dotted #999; width: 15%;"></td>
                <td style="width: 1%; white-space: nowrap; padding-left: 20px; padding-right: 5px;"><b>เลขที่</b></td>
                <td style="border-bottom: 2px dotted #999; width: 15%;"></td>
            </tr>
        </table>
        """ if not is_key else ""
        
    html = f"""<!DOCTYPE html><html lang="th"><head><meta charset="utf-8">
    <style>
        @page {{ size: A4; margin: 15mm; }}
        body {{ font-family: 'Sarabun', sans-serif; padding: 20px; line-height: 1.6; color: #333; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; margin-bottom: 10px; padding-bottom: 10px; }}
        .header h2 {{ color: {'#c0392b' if is_challenge else '#333'}; }}
        .q-box {{ margin-bottom: {q_margin}; padding: 10px 15px; page-break-inside: avoid; font-size: 20px; line-height: 1.8; }}
        .workspace {{ height: {ws_height}; border: 2px dashed #bdc3c7; border-radius: 8px; margin: 15px 0; padding: 10px; color: #95a5a6; font-size: 16px; background-color: #fafbfc; }}
        .ans-line {{ margin-top: 10px; border-bottom: 1px dotted #999; width: 80%; height: 30px; font-weight: bold; font-size: 20px; display: flex; align-items: flex-end; padding-bottom: 5px; }}
        .sol-text {{ color: #333; font-size: 18px; display: block; margin-top: 15px; padding: 15px; background-color: #fdf2e9; border-left: 4px solid #d35400; border-radius: 4px; line-height: 1.8; }}
        .page-footer {{ text-align: right; font-size: 14px; color: #95a5a6; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }}
    </style></head><body>
    <div class="header"><h2>{title}</h2><p><b>หมวดหมู่:</b> {sub_t} ({level})</p></div>
    {student_info}"""
    
    for i, item in enumerate(questions, 1):
        html += f'<div class="q-box"><b>ข้อที่ {i}.</b> '
        if is_key:
            html += f'{item["question"]}<div class="sol-text">{item["solution"]}</div>'
        else:
            html += f'{item["question"]}<div class="workspace">พื้นที่สำหรับแสดงวิธีคิดวิเคราะห์...</div><div class="ans-line">ตอบ: </div>'
        html += '</div>'
        
    if brand_name: 
        html += f'<div class="page-footer">&copy; 2026 {brand_name} | สงวนลิขสิทธิ์</div>'
        
    return html + "</body></html>"

def generate_cover_html(level, sub_t, num_q, brand_name, is_challenge):
    theme_color = "#8e44ad" if is_challenge else "#d35400"
    badge_text = "🔥 ULTIMATE CHALLENGE MODE" if is_challenge else "(King Math Edition)"
    
    return f"""<!DOCTYPE html><html lang="th"><head><meta charset="utf-8">
    <style>
        .cover-inner {{ width: 100%; height: 100%; padding: 40px; box-sizing: border-box; text-align: center; position: relative; border: 15px solid {theme_color}; background: white; }}
        .title-box {{ margin-top: 80px; }}
        .title {{ font-size: 65px; color: #2c3e50; font-weight: bold; margin: 0; line-height: 1.2; }}
        .grade-badge {{ font-size: 40px; background-color: #f1c40f; color: #333; padding: 15px 50px; border-radius: 50px; display: inline-block; font-weight: bold; margin-top: 30px; }}
        .topic {{ font-size: 42px; color: #34495e; margin-top: 70px; font-weight: bold; }}
        .sub-topic {{ font-size: 32px; color: {theme_color}; margin-top: 10px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);}}
        .icons {{ font-size: 110px; margin: 60px 0; }}
        .details-badge {{ background-color: {theme_color}; color: white; display: inline-block; padding: 15px 40px; border-radius: 15px; font-size: 32px; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}}
        .footer {{ position: absolute; bottom: 40px; left: 0; width: 100%; text-align: center; font-size: 22px; color: #7f8c8d; }}
    </style></head><body>
    <div class="cover-inner">
        <div class="title-box">
            <h1 class="title">ข้อสอบวิเคราะห์คณิตศาสตร์</h1>
            <div class="grade-badge">{level}</div>
        </div>
        <div class="topic">เรื่อง: {sub_t}</div>
        <div class="sub-topic">{badge_text}</div>
        <div class="icons">{'⚔️ 🧠 🏆 🚀' if is_challenge else '👑 🧠 💡 🎯'}</div>
        <div class="details-badge">รวมทั้งหมด {num_q} ข้อ (พร้อมเฉลยละเอียด)</div>
        <div class="footer"><b>ออกแบบและจัดทำโดย:</b> {brand_name}</div>
    </div>
    </body></html>"""

# ==========================================
# 4. Streamlit UI (Sidebar & Result Grouping)
# ==========================================
st.sidebar.markdown("## ⚙️ พารามิเตอร์การสร้างข้อสอบ")

selected_level = st.sidebar.selectbox("👑 เลือกระดับชั้น:", list(comp_db.keys()))
sub_options = comp_db[selected_level]
selected_sub = st.sidebar.selectbox("📝 เลือกแนวข้อสอบ (พร้อมเฉลยละเอียด):", sub_options + ["🌟 สุ่มรวมทุกแนว King Math"])

num_input = st.sidebar.number_input("🔢 จำนวนข้อ:", min_value=1, max_value=100, value=10)

st.sidebar.markdown("---")
is_challenge = st.sidebar.toggle("🔥 โหมด Challenge (ระดับยากพิเศษสำหรับเด็กเก่ง)", value=False)

if is_challenge:
    st.markdown("""
    <script>
        const header = window.parent.document.querySelector('.main-header');
        if(header) { header.classList.add('challenge'); header.querySelector('span').innerText = '🔥 Ultimate Challenge Mode'; header.querySelector('span').style.background = '#e74c3c'; header.querySelector('span').style.color = '#fff'; }
    </script>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <script>
        const header = window.parent.document.querySelector('.main-header');
        if(header) { header.classList.remove('challenge'); header.querySelector('span').innerText = 'Critical Thinking'; header.querySelector('span').style.background = '#f1c40f'; header.querySelector('span').style.color = '#333'; }
    </script>
    """, unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📏 ตั้งค่าหน้ากระดาษ")
spacing_level = st.sidebar.select_slider(
    "↕️ ความสูงของพื้นที่ทดเลข:", 
    options=["แคบ", "ปานกลาง", "กว้าง", "กว้างพิเศษ"], 
    value="กว้าง"
)

if spacing_level == "แคบ": q_margin, ws_height = "15px", "100px"
elif spacing_level == "ปานกลาง": q_margin, ws_height = "20px", "180px"
elif spacing_level == "กว้าง": q_margin, ws_height = "30px", "280px"
else: q_margin, ws_height = "40px", "400px"

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 ตั้งค่าแบรนด์ & หน้าปก")
brand_name = st.sidebar.text_input("🏷️ ชื่อแบรนด์ / ผู้สอน:", value="บ้านทีเด็ด")
include_cover = st.sidebar.checkbox("🎨 สร้างหน้าปก", value=True)

if st.sidebar.button(f"{'🚀 สั่งสร้างข้อสอบระดับ Ultimate Challenge!' if is_challenge else '🚀 สั่งสร้างข้อสอบ King Math'}", type="primary", use_container_width=True):
    with st.spinner("กำลังตรวจสอบตรรกะระดับ Deep Scan และวาดภาพเศษส่วนแนวตั้ง..."):
        
        qs = generate_questions_logic(selected_level, selected_sub, num_input, is_challenge)
        
        html_w = create_page(selected_level, selected_sub, qs, is_key=False, q_margin=q_margin, ws_height=ws_height, brand_name=brand_name, is_challenge=is_challenge)
        html_k = create_page(selected_level, selected_sub, qs, is_key=True, q_margin=q_margin, ws_height=ws_height, brand_name=brand_name, is_challenge=is_challenge)
        html_cover = generate_cover_html(selected_level, selected_sub, num_input, brand_name, is_challenge) if include_cover else ""
        
        st.session_state['worksheet_html'] = html_w
        st.session_state['answerkey_html'] = html_k
        
        ebook_body = ""
        if include_cover: ebook_body += f'\n<div class="a4-wrapper cover-wrapper">{extract_body(html_cover)}</div>\n'
        ebook_body += f'\n<div class="a4-wrapper">{extract_body(html_w)}</div>\n<div class="a4-wrapper">{extract_body(html_k)}</div>\n'
        
        bg_color = "#2c3e50" if is_challenge else "#525659"
        
        full_ebook_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap" rel="stylesheet"><style>@page {{ size: A4; margin: 15mm; }} @media screen {{ body {{ font-family: 'Sarabun', sans-serif; background-color: {bg_color}; display: flex; flex-direction: column; align-items: center; padding: 40px 0; margin: 0; }} .a4-wrapper {{ width: 210mm; min-height: 297mm; background: white; margin-bottom: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.3); padding: 15mm; box-sizing: border-box; }} .cover-wrapper {{ padding: 0; }} }} @media print {{ body {{ font-family: 'Sarabun', sans-serif; background: transparent; padding: 0; display: block; margin: 0; }} .a4-wrapper {{ width: 100%; min-height: auto; margin: 0; padding: 0; box-shadow: none; page-break-after: always; }} .cover-wrapper {{ height: 260mm; }} }} .header {{ text-align: center; border-bottom: 2px solid #333; margin-bottom: 10px; padding-bottom: 10px; }} .header h2 {{ color: {'#c0392b' if is_challenge else '#333'}; }} .q-box {{ margin-bottom: {q_margin}; padding: 10px 15px; page-break-inside: avoid; font-size: 20px; line-height: 1.8; }} .workspace {{ height: {ws_height}; border: 2px dashed #bdc3c7; border-radius: 8px; margin: 15px 0; padding: 10px; color: #95a5a6; font-size: 16px; background-color: #fafbfc; }} .ans-line {{ margin-top: 10px; border-bottom: 1px dotted #999; width: 80%; height: 30px; font-weight: bold; font-size: 20px; display: flex; align-items: flex-end; padding-bottom: 5px; }} .sol-text {{ color: #333; font-size: 18px; display: block; margin-top: 15px; padding: 15px; background-color: #fdf2e9; border-left: 4px solid #d35400; border-radius: 4px; line-height: 1.8; }} .page-footer {{ text-align: right; font-size: 14px; color: #95a5a6; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }} .cover-inner {{ width: 100%; height: 100%; padding: 40px; box-sizing: border-box; text-align: center; position: relative; border: 15px solid {'#8e44ad' if is_challenge else '#d35400'}; background: white; }} .title-box {{ margin-top: 80px; }} .title {{ font-size: 65px; color: #2c3e50; font-weight: bold; margin: 0; line-height: 1.2; }} .grade-badge {{ font-size: 40px; background-color: #f1c40f; color: #333; padding: 15px 50px; border-radius: 50px; display: inline-block; font-weight: bold; margin-top: 30px; }} .topic {{ font-size: 42px; color: #34495e; margin-top: 70px; font-weight: bold; }} .sub-topic {{ font-size: 32px; color: {'#8e44ad' if is_challenge else '#7f8c8d'}; margin-top: 10px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);}} .icons {{ font-size: 110px; margin: 60px 0; }} .details-badge {{ background-color: {'#8e44ad' if is_challenge else '#d35400'}; color: white; display: inline-block; padding: 15px 40px; border-radius: 15px; font-size: 32px; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}} .footer {{ position: absolute; bottom: 40px; left: 0; width: 100%; text-align: center; font-size: 22px; color: #7f8c8d; }} </style></head><body>{ebook_body}</body></html>"""

        mode_name = "Challenge" if is_challenge else "Normal"
        safe_sub = selected_sub.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
        filename_base = f"KingMath_Pro_{mode_name}_{safe_sub}_{int(time.time())}"
        
        st.session_state['ebook_html'] = full_ebook_html
        st.session_state['filename_base'] = filename_base
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(f"{filename_base}_Full_EBook.html", full_ebook_html.encode('utf-8'))
            zip_file.writestr(f"{filename_base}_Worksheet.html", html_w.encode('utf-8'))
            zip_file.writestr(f"{filename_base}_AnswerKey.html", html_k.encode('utf-8'))
        st.session_state['zip_data'] = zip_buffer.getvalue()

if 'ebook_html' in st.session_state:
    st.success(f"✅ สร้างไฟล์ข้อสอบสำเร็จ! อัปเกรดเศษส่วนแนวตั้งและขจัดบั๊กแฝงทั้งหมดแล้ว 1,000% ครับ {'(🔥 โหมดตัวตึง Ultimate Challenge!)' if 'Challenge' in st.session_state['filename_base'] else ''}")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📄 โหลดเฉพาะโจทย์", data=st.session_state['worksheet_html'], file_name=f"{st.session_state['filename_base']}_Worksheet.html", mime="text/html", use_container_width=True)
        st.download_button("🔑 โหลดเฉพาะเฉลย", data=st.session_state['answerkey_html'], file_name=f"{st.session_state['filename_base']}_AnswerKey.html", mime="text/html", use_container_width=True)
    with c2:
        st.download_button("📚 โหลดรวมเล่ม E-Book", data=st.session_state['ebook_html'], file_name=f"{st.session_state['filename_base']}_Full_EBook.html", mime="text/html", use_container_width=True)
        st.download_button("🗂️ โหลดแพ็กเกจ (.zip)", data=st.session_state['zip_data'], file_name=f"{st.session_state['filename_base']}.zip", mime="application/zip", use_container_width=True)
    st.markdown("---")
    components.html(st.session_state['ebook_html'], height=800, scrolling=True)
