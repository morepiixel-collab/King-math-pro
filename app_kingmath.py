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
    .main-header { background: linear-gradient(135deg, #2c3e50, #c0392b); padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem; box-shadow: 0 10px 20px rgba(0,0,0,0.15); transition: all 0.5s ease; }
    .main-header.challenge { background: linear-gradient(135deg, #000000, #c0392b, #8e44ad); }
    .main-header h1 { margin: 0; font-size: 2.8rem; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    .main-header p { margin: 10px 0 0 0; font-size: 1.2rem; opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>👑 King Math Pro <span style="font-size: 20px; background: #f1c40f; color: #333; padding: 5px 15px; border-radius: 20px; vertical-align: middle;">Critical Thinking</span></h1>
    <p>ระบบสร้างข้อสอบวิเคราะห์คณิตศาสตร์ระดับแนวหน้า (โจทย์ปัญหา & เชาวน์ปัญญา) พร้อมเฉลยละเอียดขั้นสุด</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 1. คลังคำศัพท์และตัวช่วย (Helpers)
# ==========================================
NAMES = ["อคิณ", "นาวิน", "ภูผา", "สายฟ้า", "เจ้านาย", "ข้าวหอม", "ใบบัว", "มะลิ", "น้ำใส", "ญาญ่า", "ปลื้ม", "พายุ", "ไออุ่น", "กะทิ", "คุณครู", "นักเรียน"]
box_html = "<span style='display: inline-block; width: 24px; height: 24px; border: 2px solid #c0392b; border-radius: 4px; vertical-align: middle; position: relative; top: -2px; background-color: #fff;'></span>"

def get_vertical_fraction(num, den, color="#c0392b", is_bold=True):
    weight = "bold" if is_bold else "normal"
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
                    หัวใจสำคัญของการทำให้ผลคูณมีค่ามากที่สุด คือ <b>"การสร้างสมดุล"</b> และการนำเลขค่ามากไปไขว้คูณกับกลุ่มตัวเลขที่ใหญ่ที่สุด<br>
                    <b>ขั้นตอนที่ 1: เรียงลำดับตัวเลขจากมากไปน้อย</b><br>
                    &nbsp;&nbsp;&nbsp;👉 จะได้ลำดับ: <b>{sorted_d[0]} > {sorted_d[1]} > {sorted_d[2]} > {sorted_d[3]} > {sorted_d[4]}</b><br>
                    <b>ขั้นตอนที่ 2: วางตัวเลขหลักหน้าสุดเพื่อสร้างสมดุลเชิงสมการ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 แยกตัวเลขมากที่สุด 2 ตัว ({sorted_d[0]} และ {sorted_d[1]}) ให้อยู่คนละฝั่งการคูณ (เพื่อกระจายพลัง)<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการตัวตั้งต้น:</b> {sorted_d[1]}🔲🔲  ×  {sorted_d[0]}🔲<br>
                    <b>ขั้นตอนที่ 3: วางตำแหน่งที่เหลือด้วยหลักการคูณไขว้</b><br>
                    &nbsp;&nbsp;&nbsp;👉 เลข {sorted_d[2]} ต้องไขว้ไปคูณเลข {sorted_d[0]} ดังนั้นต้องไปอยู่ฝั่งซ้าย: {sorted_d[1]}{sorted_d[2]}🔲  ×  {sorted_d[0]}🔲<br>
                    &nbsp;&nbsp;&nbsp;👉 เลข {sorted_d[3]} ต้องไขว้ไปคูณก้อนที่ใหญ่กว่า ({sorted_d[1]}{sorted_d[2]}) ดังนั้นไปอยู่ฝั่งขวา: {sorted_d[1]}{sorted_d[2]}🔲  ×  {sorted_d[0]}{sorted_d[3]}<br>
                    <b>ขั้นตอนที่ 4: สรุปผลลัพธ์</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำ {sorted_d[4]} ใส่หลักสุดท้าย <b>สมการล่าสุด: {best_pair[0]} × {best_pair[1]}</b><br>
                    &nbsp;&nbsp;&nbsp;👉 คำนวณ: {best_pair[0]} × {best_pair[1]} = <b>{max_prod:,}</b><br>
                    <b>ตอบ: {max_prod:,}</b></span>"""
                else:
                    if is_p12:
                        digits = random.sample([1,2,3,4,5,6,7,8,9], 3)
                        max_v = int("".join(map(str, sorted(digits, reverse=True))))
                        min_v = int("".join(map(str, sorted(digits))))
                        diff = max_v - min_v
                        q = f"<b>{name}</b> มีบัตรตัวเลข 3 ใบ คือ <b>{digits[0]}, {digits[1]}, และ {digits[2]}</b> <br>ถ้านำบัตรตัวเลขทั้งหมดมาเรียงต่อกันเป็นจำนวน 3 หลัก จงหาผลต่างของจำนวนที่<b>มากที่สุด</b>และจำนวนที่<b>น้อยที่สุด</b>ที่สร้างได้?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีทำอย่างละเอียด (สร้างสมการผลต่าง):</b><br>
                        <b>ขั้นตอนที่ 1:</b> จำนวนมากที่สุด (เรียงเลขมากไปน้อย) ➔ <b>สมการค่ามาก = {max_v}</b><br>
                        <b>ขั้นตอนที่ 2:</b> จำนวนน้อยที่สุด (เรียงเลขน้อยไปมาก) ➔ <b>สมการค่าน้อย = {min_v}</b><br>
                        <b>ขั้นตอนที่ 3:</b> สร้างสมการผลต่าง: 🔲 = {max_v} - {min_v}<br>
                        &nbsp;&nbsp;&nbsp;👉 คำนวณ 🔲 = <b>{diff}</b><br>
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
                            sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์อย่างละเอียด (จัดรูปสมการตำแหน่งเลข):</b><br>
                            <b>ขั้นตอนที่ 1: ล็อกเงื่อนไข "จำนวนคู่"</b><br>
                            &nbsp;&nbsp;&nbsp;👉 ตัวแปรตำแหน่งหลักหน่วยต้องเป็นเลขคู่เท่านั้น ซึ่งคือกลุ่ม <b>{targets}</b><br>
                            <b>ขั้นตอนที่ 2: สร้างสมการ "ค่ามากที่สุด"</b><br>
                            &nbsp;&nbsp;&nbsp;👉 เราต้องผลักเลขที่น้อยที่สุดในกลุ่มเลขคู่ (คือ <b>{unit}</b>) ไปไว้ที่หลักหน่วย เพื่อสงวนเลขมากไว้ด้านหน้า<br>
                            &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: _ _ _ {unit}</b><br>
                            <b>ขั้นตอนที่ 3: แทนค่าตัวแปรที่เหลือ</b><br>
                            &nbsp;&nbsp;&nbsp;👉 นำเลขที่เหลือมาเรียงจากมากไปน้อย ➔ ได้เป็น <b>{ans_num:,}</b><br>
                            <b>ตอบ: {ans_num:,}</b></span>"""
                        else:
                            c_digits = random.sample([1,2,3,4,6,7,8,9], num_digits - 1) + [5]
                            random.shuffle(c_digits)
                            rem = sorted([d for d in c_digits if d != 5])
                            ans_num = int("".join(map(str, rem + [5])))
                            q = f"<b>{name}</b> มีบัตรตัวเลข {num_digits} ใบ คือ <b>{', '.join(map(str, c_digits))}</b> <br>จงหา<b>จำนวนที่น้อยที่สุดที่หารด้วย 5 ลงตัว</b>?"
                            sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์อย่างละเอียด (จัดรูปสมการตำแหน่งเลข):</b><br>
                            <b>ขั้นตอนที่ 1: ล็อกเงื่อนไข "หารด้วย 5 ลงตัว"</b><br>
                            &nbsp;&nbsp;&nbsp;👉 หลักหน่วยต้องเป็น 0 หรือ 5 เท่านั้น ในที่นี้เรามี <b>5</b> จึงล็อก 5 ไว้ที่หลักหน่วย<br>
                            &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: _ _ _ 5</b><br>
                            <b>ขั้นตอนที่ 2: สร้างสมการ "ค่าน้อยที่สุด"</b><br>
                            &nbsp;&nbsp;&nbsp;👉 นำเลขที่เหลือมาเรียงจากน้อยไปมาก เพื่อให้ตัวคูณหลักหน้าสุดมีค่าน้อย<br>
                            &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด (ประกอบร่าง): {ans_num:,}</b><br>
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
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (สมมติให้ 🔲 คือจำนวนปริศนา และแก้สมการด้วยคุณสมบัติการเท่ากัน):</b><br>
                    <b>ขั้นตอนที่ 1: สร้างสมการจากสิ่งที่ทำผิดพลาด</b><br>
                    &nbsp;&nbsp;&nbsp;👉 {frac_wrong_s} + {B} = {wrong_ans}<br>
                    <b>ขั้นตอนที่ 2: กำจัด +{B} เพื่อหาค่า 🔲</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำ {B} มา<b>ลบออกทั้งสองข้างของสมการ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 จะได้: {frac_wrong_s} + {B} <b>- {B}</b> = {wrong_ans} <b>- {B}</b><br>
                    &nbsp;&nbsp;&nbsp;👉 คำนวณฝั่งขวา: {wrong_ans} - {B} = {wrong_ans - B}<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด:</b> {frac_wrong_s} = {wrong_ans - B}<br>
                    <b>ขั้นตอนที่ 3: กำจัดตัวส่วน {A} (การหาร)</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำ {A} มา<b>คูณทั้งสองข้างของสมการ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 จะได้: ({frac_wrong_s}) <b>× {A}</b> = ({wrong_ans - B}) <b>× {A}</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ฝั่งซ้ายตัวส่วน {A} ตัดกันหมดไป, ฝั่งขวาคำนวณได้ {X}<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด (จำนวนปริศนา): 🔲 = {X}</b><br>
                    <b>ขั้นตอนที่ 4: คำนวณใหม่ให้ถูกต้องตามความตั้งใจแรก</b><br>
                    &nbsp;&nbsp;&nbsp;👉 โจทย์ต้องการให้นำ 🔲 ไป <b>คูณ {A}</b> แล้ว <b>ลบ {B}</b><br>
                    &nbsp;&nbsp;&nbsp;👉 แทนค่า: ({X} × {A}) - {B} = {X*A} - {B} = <b>{correct_ans:,}</b><br>
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
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (สมมติให้ 🔲 คือจำนวนตอนแรกสุด):</b><br>
                        <b>ขั้นตอนที่ 1: สร้างสมการจากสิ่งที่ทำผิดพลาด</b><br>
                        &nbsp;&nbsp;&nbsp;👉 🔲 - {x} = {wrong_ans}<br>
                        <b>ขั้นตอนที่ 2: ใช้คุณสมบัติการเท่ากันเพื่อหาค่า 🔲</b><br>
                        &nbsp;&nbsp;&nbsp;👉 ต้องการกำจัด -{x} จึง<b>นำ {x} มาบวกเพิ่มทั้งสองข้างของสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 จะได้: 🔲 - {x} <b>+ {x}</b> = {wrong_ans} <b>+ {x}</b><br>
                        &nbsp;&nbsp;&nbsp;👉 คำนวณผลลัพธ์ฝั่งขวา: {wrong_ans} + {x} = {wrong_ans + x}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด (จำนวนตอนแรก): 🔲 = {wrong_ans + x}</b><br>
                        <b>ขั้นตอนที่ 3: คำนวณผลลัพธ์ที่ถูกต้อง</b><br>
                        &nbsp;&nbsp;&nbsp;👉 ความตั้งใจแรกคือการนำไป <b>บวก {x}</b><br>
                        &nbsp;&nbsp;&nbsp;👉 นำ {wrong_ans + x} + {x} = <b>{ans_true}</b><br>
                        <b>ตอบ: {ans_true}</b></span>"""
                    else:
                        x = random.randint(3, 12); n = random.randint(11, 30); wrong_ans = n; correct_ans = n * x * x
                        frac_wrong_q = get_vertical_fraction('จำนวนหนึ่ง', x)
                        frac_wrong_s = get_vertical_fraction('🔲', x, color="#2c3e50", is_bold=False)
                        
                        q = f"<b>{name}</b> ตั้งใจจะนำจำนวนๆ หนึ่งไป <b>คูณ</b> ด้วย {x} แต่ดันไปเขียนเป็นเศษส่วนในรูป <b>{frac_wrong_q}</b> ทำให้ผลลัพธ์ผิดเพี้ยนไปเป็น <b>{wrong_ans}</b> <br>ผลลัพธ์ที่ถูกต้องตามความตั้งใจแรกคือเท่าไร?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (สมมติให้ 🔲 คือจำนวนตอนแรกสุด):</b><br>
                        <b>ขั้นตอนที่ 1: สร้างสมการจากสิ่งที่ทำผิดพลาด (การเขียนเศษส่วนคือการหาร)</b><br>
                        &nbsp;&nbsp;&nbsp;👉 {frac_wrong_s} = {wrong_ans}<br>
                        <b>ขั้นตอนที่ 2: ใช้คุณสมบัติการเท่ากันเพื่อหาค่า 🔲</b><br>
                        &nbsp;&nbsp;&nbsp;👉 ต้องการกำจัดตัวส่วน {x} จึง<b>นำ {x} มาคูณทั้งสองข้างของสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 จะได้: ({frac_wrong_s}) <b>× {x}</b> = {wrong_ans} <b>× {x}</b><br>
                        &nbsp;&nbsp;&nbsp;👉 ฝั่งซ้ายตัวส่วน {x} ตัดกันหมดไป, ฝั่งขวา {wrong_ans} × {x} = {wrong_ans * x}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด (จำนวนตอนแรก): 🔲 = {wrong_ans * x}</b><br>
                        <b>ขั้นตอนที่ 3: คำนวณผลลัพธ์ที่ถูกต้อง</b><br>
                        &nbsp;&nbsp;&nbsp;👉 ความตั้งใจแรกคือการนำไป <b>คูณด้วย {x}</b><br>
                        &nbsp;&nbsp;&nbsp;👉 นำ {wrong_ans * x} × {x} = <b>{correct_ans:,}</b><br>
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
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีทำอย่างละเอียด (ใช้สมการหักล้างตัวแปร):</b><br>
                    <b>สมการหลัก:</b> รูปที่ต้องการ = (สี่เหลี่ยมผืนผ้าทั้งหมด) - (สี่เหลี่ยมจัตุรัสทั้งหมด)<br>
                    <b>ขั้นตอนที่ 1: หาตัวแปรสี่เหลี่ยมรวมทุกชนิด (ผืนผ้า)</b><br>
                    &nbsp;&nbsp;&nbsp;👉 สมการกว้าง × ยาว: (1+2+...+{N}) × (1+2+...+{M})<br>
                    &nbsp;&nbsp;&nbsp;👉 {N*(N+1)//2} × {M*(M+1)//2} = <b>{total_rect:,} รูป</b><br>
                    <b>ขั้นตอนที่ 2: หาตัวแปรสี่เหลี่ยมจัตุรัสทั้งหมด</b><br>
                    &nbsp;&nbsp;&nbsp;👉 สมการลดทอน: ({N}×{M}) + ({N-1}×{M-1}) ... จนกว่าจะเป็น 1<br>
                    &nbsp;&nbsp;&nbsp;👉 ผลรวมคือ <b>{total_sq:,} รูป</b><br>
                    <b>ขั้นตอนที่ 3: แทนค่าในสมการหลัก</b><br>
                    &nbsp;&nbsp;&nbsp;👉 🔲 = {total_rect:,} - {total_sq:,} = <b>{ans:,} รูป</b><br>
                    <b>ตอบ: {ans:,} รูป</b></span>"""
                else:
                    grid = random.randint(2, 4) if is_p12 else random.randint(4, 6)
                    ans = sum([i*i for i in range(1, grid+1)])
                    q = f"<b>{name}</b> มีตารางกระดานขนาด <b>{grid} × {grid}</b> ช่อง จงหาว่ามี <b>'สี่เหลี่ยมจัตุรัส'</b> ซ่อนอยู่ทั้งหมดกี่รูป?"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีทำอย่างละเอียด (สร้างสมการผลรวม):</b><br>
                    <b>ขั้นตอนที่ 1:</b> นำขนาดของตาราง (n) มาสร้างสมการยกกำลังสอง<br>
                    &nbsp;&nbsp;&nbsp;👉 สมการ: 🔲 = 1² + 2² + ... + {grid}²<br>
                    <b>ขั้นตอนที่ 2:</b> คิดค่าผลบวกในสมการ<br>
                    &nbsp;&nbsp;&nbsp;👉 🔲 = 1 + 4 + ... + ({grid}×{grid}) = <b>{ans:,}</b><br>
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
                    
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (แก้สมการจากวงนอกเข้าสู่วงใน ด้วยคุณสมบัติการเท่ากัน):</b><br>
                    <b>ขั้นตอนที่ 1: กำจัดตัวคูณ {A} นอกวงเล็บ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำ {A} มา<b>หารทั้งสองข้างของสมการ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ฝั่งซ้าย {A} ตัด {A} หมดไป, ฝั่งขวา {E} ÷ {A} = {V1}<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด:</b> {frac_sol_step} − {D} = {V1}<br>
                    <b>ขั้นตอนที่ 2: กำจัดตัวลบ {D}</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำ {D} มา<b>บวกเพิ่มทั้งสองข้างของสมการ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ฝั่งซ้าย -{D} + {D} = 0, ฝั่งขวา {V1} + {D} = {V2}<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด:</b> {frac_sol_step} = {V2}<br>
                    <b>ขั้นตอนที่ 3: กำจัดตัวส่วน {C} (การหาร)</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำ {C} มา<b>คูณทั้งสองข้างของสมการ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ฝั่งซ้ายส่วน {C} ตัดกันหมดไป, ฝั่งขวา {V2} × {C} = {V3}<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด:</b> 🔲 + {B} = {V3}<br>
                    <b>ขั้นตอนที่ 4: หาค่า 🔲</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำ {B} มา<b>ลบออกทั้งสองข้างของสมการ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ฝั่งซ้ายเหลือ 🔲, ฝั่งขวา {V3} - {B} = {ans}<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 = {ans}</b><br>
                    <b>ตอบ: {ans}</b></span>"""
                else:
                    if is_p12:
                        a = random.randint(15, 50); b = random.randint(60, 150)
                        q = f"จงหาตัวเลขที่เติมลงในช่องว่าง:<br><br><span style='font-size:24px; font-weight:bold;'>{box_html} + {a} = {b}</span>"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (ใช้คุณสมบัติการเท่ากันของสมการ):</b><br>
                        <b>ขั้นตอนที่ 1:</b> จากสมการ 🔲 + {a} = {b}<br>
                        &nbsp;&nbsp;&nbsp;👉 ต้องการให้ 🔲 เหลือเพียงตัวเดียว จึงใช้คุณสมบัติการเท่ากัน โดย<b>นำ {a} มาลบออกทั้งสองข้างของสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 เขียนเป็นสมการได้ว่า: 🔲 + {a} <b>- {a}</b> = {b} <b>- {a}</b><br>
                        <b>ขั้นตอนที่ 2:</b> คำนวณผลลัพธ์แต่ละข้าง<br>
                        &nbsp;&nbsp;&nbsp;👉 ฝั่งซ้าย: {a} - {a} = 0 (เหลือ 🔲 ตัวเดียว)<br>
                        &nbsp;&nbsp;&nbsp;👉 ฝั่งขวา: {b} - {a} = {b-a}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 = {b-a}</b><br>
                        <b>ตอบ: {b-a}</b></span>"""
                    else:
                        a = random.randint(10, 50); b = random.randint(2, 9)
                        ans = random.randint(5, 40)
                        c = (ans + a) * b
                        q = f"จงหาตัวเลขที่เติมลงในช่องว่าง:<br><br><span style='font-size:24px; font-weight:bold;'>( {box_html} + {a} ) × {b} = {c}</span>"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (กำจัดตัวแปรด้วยคุณสมบัติการเท่ากัน):</b><br>
                        <b>ขั้นตอนที่ 1: กำจัดตัวนอกวงเล็บ "× {b}"</b><br>
                        &nbsp;&nbsp;&nbsp;👉 <b>นำ {b} มาหารทั้งสองข้างของสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 ฝั่งซ้าย {b} ตัด {b} หมดไป, ฝั่งขวา {c} ÷ {b} = {c//b}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด:</b> 🔲 + {a} = {c//b}<br>
                        <b>ขั้นตอนที่ 2: หาค่า 🔲</b><br>
                        &nbsp;&nbsp;&nbsp;👉 <b>นำ {a} มาลบออกทั้งสองข้างของสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 ฝั่งซ้ายเหลือ 🔲, ฝั่งขวา {c//b} - {a} = {ans}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 = {ans}</b><br>
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
                    
                    frac_sol_M1 = get_vertical_fraction(f"🔲 × {C}", f"{B} × {C}", color="#2c3e50", is_bold=False)
                    frac_sol_M2 = get_vertical_fraction(f"🔲 × {C}", B*C, color="#2c3e50", is_bold=False)
                    
                    q = f"จงหา <b>'ผลบวกของจำนวนนับทุกจำนวน'</b> ที่สามารถเติมในช่องว่างแล้วทำให้อสมการเป็นจริง:<br><br><span style='font-size:24px; font-weight:bold;'>{frac_L} &nbsp;&lt;&nbsp; {frac_M} &nbsp;&lt;&nbsp; {frac_R}</span>"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์อย่างละเอียด (แก้อสมการเศษส่วน):</b><br>
                    จากโจทย์: <b>{frac_L} &nbsp;&lt;&nbsp; {get_vertical_fraction('🔲', B, color='#2c3e50', is_bold=False)} &nbsp;&lt;&nbsp; {frac_R}</b><br>
                    <b>ขั้นตอนที่ 1: ทำให้ตัวส่วนตรงกลางเท่ากับตัวส่วนด้านข้าง ({B*C})</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำ <b>{C} มาคูณทั้งตัวเศษและตัวส่วน</b> ของพจน์ตรงกลาง<br>
                    &nbsp;&nbsp;&nbsp;👉 พจน์กลางจะเปลี่ยนเป็น: {frac_sol_M1} = {frac_sol_M2}<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>อสมการล่าสุด:</b> {frac_L} &lt; {frac_sol_M2} &lt; {frac_R}<br>
                    <b>ขั้นตอนที่ 2: กำจัดตัวส่วน {B*C} โดยใช้คุณสมบัติการคูณ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 นำ <b>{B*C} มาคูณตลอดทั้งอสมการ (คูณทุกพจน์)</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ทุกพจน์จะถูกตัดตัวส่วนทิ้งไปทั้งหมด<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>อสมการล่าสุด: {A} &lt; 🔲 × {C} &lt; {D}</b><br>
                    <b>ขั้นตอนที่ 3: หาค่า 🔲 ที่เป็นจำนวนนับ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 หาว่า 🔲 เป็นเลขอะไรได้บ้าง ที่เมื่อคูณ {C} แล้วได้ผลลัพธ์มากกว่า {A} แต่น้อยกว่า {D}<br>
                    &nbsp;&nbsp;&nbsp;👉 จากสูตรคูณแม่ {C} จะพบว่าจำนวนที่สอดคล้องคือ: <b>{', '.join(map(str, ans_list))}</b><br>
                    <b>ขั้นตอนที่ 4: หาผลบวกของทุกจำนวน</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ผลบวกสมการ = {' + '.join(map(str, ans_list))} = <b>{ans}</b><br>
                    <b>ตอบ: {ans}</b></span>"""
                else:
                    if is_p12:
                        a = random.randint(5, 15); limit_val = random.randint(20, 40)
                    else:
                        a = random.randint(10, 50); limit_val = random.randint(80, 150)
                        
                    max_val = limit_val - a - 1
                    q = f"จงหา <b>จำนวนนับที่มากที่สุด</b> ที่เติมในช่องว่าง:<br><br><span style='font-size:24px; font-weight:bold;'>{box_html} + {a} &lt; {limit_val}</span>"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (ใช้คุณสมบัติของอสมการ):</b><br>
                    <b>ขั้นตอนที่ 1:</b> จากอสมการ 🔲 + {a} &lt; {limit_val}<br>
                    &nbsp;&nbsp;&nbsp;👉 เราต้องการหาค่า 🔲 จึงต้องกำจัด +{a} โดย<b>นำ {a} มาลบออกทั้งสองข้างของอสมการ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 เขียนเป็นอสมการใหม่ได้ว่า: 🔲 + {a} <b>- {a}</b> &lt; {limit_val} <b>- {a}</b><br>
                    <b>ขั้นตอนที่ 2:</b> คำนวณผลลัพธ์ทั้งสองข้าง<br>
                    &nbsp;&nbsp;&nbsp;👉 ฝั่งซ้าย: {a} - {a} = 0 (เหลือ 🔲)<br>
                    &nbsp;&nbsp;&nbsp;👉 ฝั่งขวา: {limit_val} - {a} = {limit_val - a}<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>อสมการล่าสุดคือ: 🔲 &lt; {limit_val - a}</b><br>
                    <b>ขั้นตอนที่ 3: หาจำนวนนับที่มากที่สุด</b><br>
                    &nbsp;&nbsp;&nbsp;👉 อสมการบอกว่า 🔲 ต้อง "น้อยกว่า" {limit_val - a} (เป็น {limit_val - a} ไม่ได้)<br>
                    &nbsp;&nbsp;&nbsp;👉 ดังนั้น จำนวนนับที่มากที่สุดที่เป็นไปได้คือ {limit_val - a} - 1 = <b>{max_val}</b><br>
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
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (วิเคราะห์การลบทีละหลักและเขียนเป็นสมการ):</b><br>
                    <b>ขั้นตอนที่ 1: วิเคราะห์หลักหน่วย</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ตัวตั้ง {Z} ลบ {C} ซึ่ง {Z} < {C} ลบไม่ได้ จึงยืมหลักสิบมา 10<br>
                    &nbsp;&nbsp;&nbsp;👉 หลักหน่วยกลายเป็น {Z} + 10 = {10+Z}<br>
                    &nbsp;&nbsp;&nbsp;👉 สร้างสมการ: {10+Z} - {C} = 🔲 (กล่องล่างสุด)<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 ล่างสุด = {10+Z-C}</b><br>
                    <b>ขั้นตอนที่ 2: วิเคราะห์หลักสิบ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ตัวตั้ง {Y} ถูกยืมไป 1 เหลือ {Y-1} แต่ต้องลบ 🔲 ให้ได้ {str_Res[1]}<br>
                    &nbsp;&nbsp;&nbsp;👉 {Y-1} น้อยกว่า {str_Res[1]} จึงยืมหลักร้อยมา 10 กลายเป็น {10+Y-1}<br>
                    &nbsp;&nbsp;&nbsp;👉 สร้างสมการ: {10+Y-1} - 🔲 = {str_Res[1]}<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>นำ 🔲 บวกทั้งสองข้าง และนำ {str_Res[1]} ลบทั้งสองข้าง</b><br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 ตรงกลาง = {10+Y-1} - {str_Res[1]} = {B}</b><br>
                    <b>ขั้นตอนที่ 3: วิเคราะห์หลักร้อย</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ตัวตั้ง 🔲 (บนสุด) ถูกหลักสิบยืมไป 1 จึงเหลือ (🔲 - 1)<br>
                    &nbsp;&nbsp;&nbsp;👉 สร้างสมการ: (🔲 - 1) - {A} = {str_Res[0]}<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>นำ {A} และ 1 บวกเพิ่มทั้งสองข้างของสมการ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 บนสุด = {str_Res[0]} + {A} + 1 = {X}</b><br>
                    <b>ตอบ: บนคือ {X}, กลางคือ {B}, ล่างคือ {10+Z-C}</b></span>"""
                else:
                    if is_p12:
                        a1, a2 = random.randint(1, 8), random.randint(1, 8)
                        b1, b2 = random.randint(1, 9 - a1), random.randint(1, 9 - a2)
                        str_a, str_b, str_ans = str(a1*10+a2).zfill(2), str(b1*10+b2).zfill(2), str((a1+b1)*10+(a2+b2)).zfill(2)
                        top_row, bot_row, res_row = [str_a[0], box_html], [box_html, str_b[1]], list(str_ans)
                        math_table = get_vertical_math(top_row, bot_row, res_row, operator="+")
                        q = f"จงเติมตัวเลขลงใน 🔲 ให้ถูกต้องสมบูรณ์<br>{math_table}"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (วิเคราะห์เป็นสมการทีละหลัก):</b><br>
                        <b>ขั้นตอนที่ 1: วิเคราะห์หลักหน่วย</b><br>
                        &nbsp;&nbsp;&nbsp;👉 สร้างสมการ: 🔲 (บน) + {str_b[1]} = {str_ans[1]}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>นำ {str_b[1]} มาลบออกทั้งสองข้างของสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 จะได้: 🔲 (บน) + {str_b[1]} <b>- {str_b[1]}</b> = {str_ans[1]} <b>- {str_b[1]}</b><br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 (บน) = {str_a[1]}</b><br>
                        <b>ขั้นตอนที่ 2: วิเคราะห์หลักสิบ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 สร้างสมการ: {str_a[0]} + 🔲 (ล่าง) = {str_ans[0]}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>นำ {str_a[0]} มาลบออกทั้งสองข้างของสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 จะได้: {str_a[0]} <b>- {str_a[0]}</b> + 🔲 (ล่าง) = {str_ans[0]} <b>- {str_a[0]}</b><br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 (ล่าง) = {str_b[0]}</b><br>
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
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (เขียนรูปประโยคเป็นสมการ):</b><br>
                        <b>ขั้นตอนที่ 1: สร้างสมการหลักจากการคูณ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 ให้ตัวเลข 2 หลักด้านบนคือ "จำนวนปริศนา"<br>
                        &nbsp;&nbsp;&nbsp;👉 สมการคือ: จำนวนปริศนา × {n2} = {ans_val}<br>
                        <b>ขั้นตอนที่ 2: หาจำนวนปริศนาด้วยคุณสมบัติการเท่ากัน</b><br>
                        &nbsp;&nbsp;&nbsp;👉 ต้องการกำจัด × {n2} จึง<b>นำ {n2} มาหารทั้งสองข้างของสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 จะได้: (จำนวนปริศนา × {n2}) <b>÷ {n2}</b> = {ans_val} <b>÷ {n2}</b><br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: จำนวนปริศนา = {n1}</b><br>
                        <b>ขั้นตอนที่ 3: หาตัวเลขที่หายไปในช่องว่าง</b><br>
                        &nbsp;&nbsp;&nbsp;👉 เนื่องจากจำนวนด้านบนคือ {n1} และโจทย์ให้หลักสิบมาคือ {str_n1[0]}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 หลักหน่วย = {str_n1[1]}</b><br>
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
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์ (สมการความยาวที่ถูกซ่อน):</b><br>
                    เมื่อวางซ้อนทับกัน รูปทรงใหม่จะกลายเป็นสี่เหลี่ยมผืนผ้ายาวๆ 1 รูป<br>
                    <b>ขั้นตอนที่ 1: สร้างสมการความยาว (แนวนอน) ของรูปใหม่</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ถ้านำแผ่นมาต่อกันเฉยๆ จะยาว {N} × {S} = {N*S} ซม.<br>
                    &nbsp;&nbsp;&nbsp;👉 แต่มีรอยซ้อนทับ {N-1} รอย รอยละ {O} ซม. ➔ หดหายไป {N-1} × {O} = {(N-1)*O} ซม.<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: ความยาว = {N*S} - {(N-1)*O} = {width} ซม.</b><br>
                    <b>ขั้นตอนที่ 2: ระบุความกว้าง (แนวตั้ง)</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ความกว้างยังคงเท่าเดิมคือด้านของจัตุรัส ➔ <b>สมการล่าสุด: ความกว้าง = {S} ซม.</b><br>
                    <b>ขั้นตอนที่ 3: แทนค่าในสมการหาความยาวรอบรูป</b><br>
                    &nbsp;&nbsp;&nbsp;👉 สมการรอบรูป = 2 × (กว้าง + ยาว)<br>
                    &nbsp;&nbsp;&nbsp;👉 แทนค่า: 2 × ({width} + {S}) = <b>{ans} ซม.</b><br>
                    <b>ตอบ: {ans} ซม.</b></span>"""
                else:
                    if is_p12: 
                        L = random.randint(4, 20) * 4
                        q = f"<b>{name}</b> มีลวดความยาว <b>{L} ซม.</b> นำไปดัดเป็นรูปสี่เหลี่ยมจัตุรัส จะมีความยาวด้านละกี่เซนติเมตร?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (ตั้งเป็นสมการ):</b><br>
                        <b>ขั้นตอนที่ 1: สร้างสมการจากคุณสมบัติของสี่เหลี่ยมจัตุรัส</b><br>
                        &nbsp;&nbsp;&nbsp;👉 จัตุรัสมี 4 ด้านเท่ากัน สมมติให้ด้านยาว = 🔲<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการ: 4 × 🔲 = {L}</b><br>
                        <b>ขั้นตอนที่ 2: ใช้คุณสมบัติการเท่ากันหาค่า 🔲</b><br>
                        &nbsp;&nbsp;&nbsp;👉 <b>นำ 4 มาหารทั้งสองข้างของสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 (4 × 🔲) ÷ 4 = {L} ÷ 4<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 = {L//4} ซม.</b><br>
                        <b>ตอบ: {L//4} ซม.</b></span>"""
                    else:
                        side = random.randint(5, 25)
                        leftover = random.randint(5, 20)
                        L = (side * 4) + leftover
                        q = f"<b>{name}</b> นำเส้นลวดที่มีความยาว <b>{L} ซม.</b> ไปสร้างรูปสี่เหลี่ยมจัตุรัสแล้ว <b>เหลือเศษลวด {leftover} ซม.</b><br>ความยาวของแต่ละด้านของรูปสี่เหลี่ยมจัตุรัสนี้เป็นกี่เซนติเมตร?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (ตั้งสมการและคุณสมบัติการเท่ากัน):</b><br>
                        <b>ขั้นตอนที่ 1: สร้างสมการจากโจทย์</b><br>
                        &nbsp;&nbsp;&nbsp;👉 สมมติให้ความยาวด้านของจัตุรัส = 🔲<br>
                        &nbsp;&nbsp;&nbsp;👉 ลวดทั้งหมด = ลวดที่ใช้ทำ 4 ด้าน + ลวดที่เหลือ<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการ: (4 × 🔲) + {leftover} = {L}</b><br>
                        <b>ขั้นตอนที่ 2: ใช้คุณสมบัติการเท่ากันกำจัดเศษลวด</b><br>
                        &nbsp;&nbsp;&nbsp;👉 <b>นำ {leftover} มาลบออกทั้งสองข้างของสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 (4 × 🔲) + {leftover} - {leftover} = {L} - {leftover}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 4 × 🔲 = {L - leftover}</b><br>
                        <b>ขั้นตอนที่ 3: ใช้คุณสมบัติการเท่ากันหาความยาวด้าน</b><br>
                        &nbsp;&nbsp;&nbsp;👉 <b>นำ 4 มาหารทั้งสองข้างของสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 (4 × 🔲) ÷ 4 = {L - leftover} ÷ 4<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 = {side}</b><br>
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
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดย้อนกลับและตั้งสมการทีละขั้น (Olympiad Level):</b><br>
                    <b>วันที่ 3:</b> อ่าน {f1_2_s} แล้วอ่านอีก {Y} หน้าจนจบ<br>
                    &nbsp;&nbsp;&nbsp;👉 ตั้งสมการ: 🔲/2 = {Y} (เพราะครึ่งหลังคือที่เหลือ)<br>
                    &nbsp;&nbsp;&nbsp;👉 นำ 2 คูณทั้งสองข้าง ➔ <b>สมการล่าสุด: หน้าก่อนอ่านวันที่ 3 = {R2}</b><br>
                    <b>วันที่ 2:</b> อ่าน {f1_3_s} + {X} หน้า ทำให้เหลือ {R2} หน้า<br>
                    &nbsp;&nbsp;&nbsp;👉 ตั้งสมการ: ส่วนที่เหลือ = {f2_3_s} ของวันนั้น<br>
                    &nbsp;&nbsp;&nbsp;👉 {f2_3_s} × 🔲 = {R2} + {X} = {R2+X}<br>
                    &nbsp;&nbsp;&nbsp;👉 นำ 3/2 คูณทั้งสองข้าง ➔ <b>สมการล่าสุด: หน้าก่อนอ่านวันที่ 2 = {R1}</b><br>
                    <b>วันที่ 1:</b> อ่าน {f1_4_s} ทำให้เหลือ {R1} หน้า<br>
                    &nbsp;&nbsp;&nbsp;👉 ตั้งสมการ: ส่วนที่เหลือ = {f3_4_s} ของทั้งเล่ม<br>
                    &nbsp;&nbsp;&nbsp;👉 {f3_4_s} × 🔲(ทั้งหมด) = {R1}<br>
                    &nbsp;&nbsp;&nbsp;👉 นำ 4/3 คูณทั้งสองข้าง ➔ <b>สมการล่าสุด: หน้าทั้งหมด = {Total}</b><br>
                    <b>ตอบ: {Total} หน้า</b></span>"""
                else:
                    if is_p12: 
                        baskets = random.randint(4, 9)
                        breads_per_b = random.randint(3, 10)
                        total_breads = baskets * breads_per_b
                        ask_b = random.randint(2, baskets-1)
                        q = f"<b>{name}</b> แบ่งขนมปัง <b>{total_breads} ชิ้น</b> ใส่ตะกร้า <b>{baskets} ใบ</b> ใบละเท่าๆ กัน<br>จงหาว่าขนมปังที่อยู่ในตะกร้า <b>{ask_b} ใบ</b> มีทั้งหมดกี่ชิ้น?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิด (สมการแบ่งกลุ่ม):</b><br>
                        <b>ขั้นตอนที่ 1: ตั้งสมการหาจำนวนต่อตะกร้า</b><br>
                        &nbsp;&nbsp;&nbsp;👉 สมการ: 🔲 (ชิ้นต่อตะกร้า) × {baskets} = {total_breads}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>นำ {baskets} หารทั้งสองข้างของสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 = {breads_per_b} ชิ้น</b><br>
                        <b>ขั้นตอนที่ 2: ตั้งสมการหาผลรวมที่ต้องการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 สมการ: 🔲 (รวม) = {breads_per_b} × {ask_b}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: 🔲 (รวม) = {breads_per_b * ask_b} ชิ้น</b><br>
                        <b>ตอบ: {breads_per_b * ask_b} ชิ้น</b></span>"""
                    else:
                        den = random.choice([4, 5, 6, 8, 10])
                        num = random.randint(1, den-2)
                        total_money = random.randint(10, 50) * den
                        ans_rem = total_money - int((total_money/den)*num)
                        
                        frac_html = get_vertical_fraction(num, den)
                        
                        q = f"<b>{name}</b> มีเงิน <b>{total_money} บาท</b> ซื้อเครื่องเขียนไป <b>{frac_html}</b> ของเงินทั้งหมด จะเหลือเงินกี่บาท?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (วิเคราะห์เป็นสมการ):</b><br>
                        <b>ขั้นตอนที่ 1: หาจำนวนเงินที่ใช้ไปเป็นสมการ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 สมการ: เงินที่ใช้ = ({num} ÷ {den}) × {total_money}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: เงินที่ใช้ = {int((total_money/den)*num)} บาท</b><br>
                        <b>ขั้นตอนที่ 2: คำนวณเงินที่เหลือ</b><br>
                        &nbsp;&nbsp;&nbsp;👉 สมการ: เงินที่เหลือ = เงินตอนแรก - เงินที่ใช้ไป<br>
                        &nbsp;&nbsp;&nbsp;👉 แทนค่า: เงินที่เหลือ = {total_money} - {int((total_money/den)*num)}<br>
                        &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: เงินที่เหลือ = {ans_rem} บาท</b><br>
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
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์ (สมการความคลาดเคลื่อนสะสม):</b><br>
                    <b>ขั้นตอนที่ 1: สมการหาจำนวนวัน</b><br>
                    &nbsp;&nbsp;&nbsp;👉 สมการ: วันทั้งหมด = วัน{end_day} - วันจันทร์ ➔ <b>สมการล่าสุด: วันทั้งหมด = {days} วัน</b><br>
                    <b>ขั้นตอนที่ 2: สมการหาเวลาเพี้ยนรวม</b><br>
                    &nbsp;&nbsp;&nbsp;👉 สมการ: เวลาที่เดินเร็ว = {gain_m} × {days} ➔ <b>สมการล่าสุด: เวลาที่เดินเร็ว = {total_gain} นาที</b><br>
                    <b>ขั้นตอนที่ 3: สมการคำนวณเวลาบนหน้าปัด</b><br>
                    &nbsp;&nbsp;&nbsp;👉 สมการ: เวลาหน้าปัด = เวลาจริง + เวลาที่เดินเร็ว<br>
                    &nbsp;&nbsp;&nbsp;👉 แปลง {total_gain} นาที = <b>{carry_h} ชั่วโมง {final_m} นาที</b><br>
                    &nbsp;&nbsp;&nbsp;👉 แทนค่า: 08:00 น. + {carry_h} ชั่วโมง {final_m} นาที = <b>{final_h:02d}:{final_m:02d} น.</b><br>
                    <b>ตอบ: เวลา {final_h:02d}:{final_m:02d} น.</b></span>"""
                else:
                    if is_p12: 
                        h1 = random.randint(1, 4); m1 = random.randint(10, 20)
                        h2 = random.randint(1, 3); m2 = random.randint(10, 30)
                        q = f"<b>{name}</b> ใช้เวลาเดินทางช่วงแรก <b>{h1} ชั่วโมง {m1} นาที</b> และช่วงที่สองอีก <b>{h2} ชั่วโมง {m2} นาที</b> รวมใช้เวลาเท่าไร?"
                        sol = f"<span style='color: #2c3e50;'><b>สร้างสมการเวลารวม:</b><br>👉 สมการชั่วโมง = {h1} + {h2} = <b>{h1+h2} ชั่วโมง</b><br>👉 สมการนาที = {m1} + {m2} = <b>{m1+m2} นาที</b><br><b>ตอบ: {h1+h2} ชั่วโมง {m1+m2} นาที</b></span>"
                    elif is_p34:
                        km1 = random.randint(2, 6); m1 = random.randint(400, 800)
                        m2 = random.randint(1200, 2500)
                        total_m = (km1 * 1000) + m1 + m2
                        ans_km = total_m // 1000
                        ans_m = total_m % 1000
                        q = f"<b>{name}</b> จงหาผลบวกของระยะทาง:<br><b>{km1} กิโลเมตร {m1} เมตร  +  {m2} เมตร</b>  =  🔲 กิโลเมตร 🔲 เมตร"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิด (สมการระยะทาง):</b><br>
                        แปลงเป็นหน่วยเดียว: ({km1} × 1000) + {m1} = {km1 * 1000 + m1} เมตร<br>
                        สมการผลบวก: 🔲 = {km1 * 1000 + m1} + {m2}<br>
                        <b>สมการล่าสุด: 🔲 = {total_m} เมตร</b><br>
                        แปลงกลับ: {total_m} เมตร = <b>{ans_km} กม. {ans_m} ม.</b><br>
                        <b>ตอบ: {ans_km} กิโลเมตร {ans_m} เมตร</b></span>"""
                    else:
                        h1 = random.randint(2, 6); m1 = random.randint(40, 55)
                        h2 = random.randint(1, 4); m2 = random.randint(30, 55)
                        total_m = m1 + m2
                        carry_h = total_m // 60
                        left_m = total_m % 60
                        ans_h = h1 + h2 + carry_h
                        q = f"<b>{name}</b> เดินทางด้วยรถยนต์ <b>{h1} ชม. {m1} นาที</b> และต่อเรืออีก <b>{h2} ชม. {m2} นาที</b> รวมใช้เวลาทั้งหมดเท่าไร?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดอย่างละเอียด (สมการเวลา):</b><br>
                        <b>ขั้นตอนที่ 1: สมการนาที</b><br>
                        &nbsp;&nbsp;&nbsp;👉 🔲 = {m1} + {m2} ➔ <b>สมการล่าสุด: 🔲 = {total_m} นาที</b><br>
                        &nbsp;&nbsp;&nbsp;👉 ปัด {total_m} นาที = <b>{carry_h} ชม. {left_m} นาที</b><br>
                        <b>ขั้นตอนที่ 2: สมการชั่วโมง</b><br>
                        &nbsp;&nbsp;&nbsp;👉 🔲 = {h1} + {h2} + {carry_h} ➔ <b>สมการล่าสุด: 🔲 = {ans_h} ชั่วโมง</b><br>
                        <b>ตอบ: {ans_h} ชั่วโมง {left_m} นาที</b></span>"""

            # ---------------------------------------------------------
            # 10. โจทย์ปัญหาเปรียบเทียบกลุ่ม 
            # ---------------------------------------------------------
            elif actual_sub_t == "โจทย์ปัญหาเปรียบเทียบกลุ่ม":
                if is_challenge:
                    C = random.randint(5, 15)
                    P = random.randint(5, 15)
                    H = P + 3 * C
                    L = 4 * P + 6 * C
                    
                    q = f"ในฟาร์มของ<b>{name}</b>มี หมู ไก่ และเป็ด รวมกันทั้งหมด <b>{H} ตัว (นับหัว)</b> และนับขารวมกันได้ <b>{L} ขา</b><br>ถ้าเจ้าของฟาร์มบอกว่า <b>'มีจำนวนเป็ดเป็น 2 เท่าของจำนวนไก่'</b><br>จงหาว่าในฟาร์มแห่งนี้มีหมูทั้งหมดกี่ตัว?"
                    sol = f"""<span style='color: #2c3e50;'><b>วิธีคิดวิเคราะห์ (สมการนับหัว-นับขา แบบ Step by Step):</b><br>
                    <b>ขั้นตอนที่ 1: กำหนดตัวแปรและสร้างกลุ่มสัตว์ปีก</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ให้ หมู = M, ไก่ = C, เป็ด = D<br>
                    &nbsp;&nbsp;&nbsp;👉 จากโจทย์ "เป็ดเป็น 2 เท่าของไก่" (D = 2C) ดังนั้นจัดกลุ่ม (ไก่ 1 + เป็ด 2) เป็น 1 เซ็ต<br>
                    &nbsp;&nbsp;&nbsp;👉 1 เซ็ต มี 3 ตัว และมีขา = 2(ไก่) + 2×2(เป็ด) = 6 ขา<br>
                    &nbsp;&nbsp;&nbsp;👉 ค่าเฉลี่ยของสัตว์ปีก 1 ตัวในกลุ่มนี้ คือ 6 ÷ 3 = <b>2 ขาต่อตัว</b><br>
                    <b>ขั้นตอนที่ 2: ตั้งสมมติฐานและสร้างสมการ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 สมมติให้สัตว์ทั้ง {H} ตัวเป็นสัตว์ปีก (มี 2 ขา) ขารวมสมมติคือ: {H} × 2 = <b>{H*2} ขา</b><br>
                    &nbsp;&nbsp;&nbsp;👉 ขาของจริงคือ {L} ขา แสดงว่ามีส่วนต่างขาที่เกินมา: {L} - {H*2} = <b>{L - H*2} ขา</b><br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: ขาของหมูที่เกินจาก 2 ขา = {L - H*2} ขา</b><br>
                    <b>ขั้นตอนที่ 3: คำนวณหาจำนวนหมู (M) ด้วยคุณสมบัติการเท่ากัน</b><br>
                    &nbsp;&nbsp;&nbsp;👉 หมูแต่ละตัวมี 4 ขา ซึ่งมากกว่าสัตว์ปีกอยู่ 2 ขา (4 - 2 = 2)<br>
                    &nbsp;&nbsp;&nbsp;👉 สมการจำนวนหมู: M × 2 = {L - H*2}<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>นำ 2 มาหารทั้งสองข้างของสมการ</b><br>
                    &nbsp;&nbsp;&nbsp;👉 (M × 2) ÷ 2 = {L - H*2} ÷ 2<br>
                    &nbsp;&nbsp;&nbsp;👉 <b>สมการล่าสุด: M = {P}</b><br>
                    <b>ตอบ: มีหมู {P} ตัว</b></span>"""
                else:
                    if is_p12: 
                        dozens = random.randint(2, 6)
                        students = random.choice([2, 3, 4, 6])
                        total_items = dozens * 12
                        ans = total_items // students
                        q = f"คุณครู<b>{name}</b>มีดินสอ <b>{dozens} โหล</b> นำมาแบ่งให้นักเรียน <b>{students} คน</b> คนละเท่าๆ กัน<br>นักเรียนจะได้รับดินสอคนละกี่แท่ง?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิด (สมการแบ่งของ):</b><br>
                        <b>ขั้นตอนที่ 1: สมการหาของทั้งหมด</b><br>
                        &nbsp;&nbsp;&nbsp;👉 🔲 = {dozens} × 12 ➔ <b>สมการล่าสุด: 🔲 = {total_items} แท่ง</b><br>
                        <b>ขั้นตอนที่ 2: สมการแบ่งให้เด็ก</b><br>
                        &nbsp;&nbsp;&nbsp;👉 🔲 = {total_items} ÷ {students} ➔ <b>สมการล่าสุด: 🔲 = {ans} แท่ง</b><br>
                        <b>ตอบ: {ans} แท่ง</b></span>"""
                    else:
                        g1_std, g1_items = random.randint(10, 15), random.randint(5, 9)
                        g2_std, g2_items = random.randint(16, 22), random.randint(3, 5)
                        t1 = g1_std * g1_items
                        t2 = g2_std * g2_items
                        diff = abs(t1 - t2)
                        more_g = "กลุ่มแรก" if t1 > t2 else "กลุ่มที่สอง"
                        q = f"คุณครู<b>{name}</b>แจกสมุดให้เด็กกลุ่มแรก <b>{g1_std} คน คนละ {g1_items} เล่ม</b> และกลุ่มที่สอง <b>{g2_std} คน คนละ {g2_items} เล่ม</b><br>กลุ่มใดได้รับสมุดรวมมากกว่ากัน และมากกว่ากันกี่เล่ม?"
                        sol = f"""<span style='color: #2c3e50;'><b>วิธีคิด (สมการเปรียบเทียบ):</b><br>
                        <b>ขั้นตอนที่ 1: สมการกลุ่มแรก</b> ➔ 🔲 = {g1_std} × {g1_items} ➔ <b>สมการล่าสุด: 🔲 = {t1} เล่ม</b><br>
                        <b>ขั้นตอนที่ 2: สมการกลุ่มที่สอง</b> ➔ 🔲 = {g2_std} × {g2_items} ➔ <b>สมการล่าสุด: 🔲 = {t2} เล่ม</b><br>
                        <b>ขั้นตอนที่ 3: สมการผลต่าง</b><br>
                        &nbsp;&nbsp;&nbsp;👉 🔲 = {max(t1,t2)} - {min(t1,t2)} ➔ <b>สมการล่าสุด: 🔲 = {diff} เล่ม</b><br>
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
st.sidebar.markdown("### 🎨 ตั้งค่าแบรนด์")
brand_name = st.sidebar.text_input("🏷️ ชื่อแบรนด์ / ผู้สอน:", value="บ้านทีเด็ด")

if st.sidebar.button(f"{'🚀 สั่งสร้างข้อสอบระดับ Ultimate Challenge!' if is_challenge else '🚀 สั่งสร้างข้อสอบ King Math'}", type="primary", use_container_width=True):
    with st.spinner("กำลังตรวจสอบตรรกะระดับ Deep Scan และวาดภาพเศษส่วนแนวตั้ง..."):
        
        qs = generate_questions_logic(selected_level, selected_sub, num_input, is_challenge)
        
        html_w = create_page(selected_level, selected_sub, qs, is_key=False, q_margin=q_margin, ws_height=ws_height, brand_name=brand_name, is_challenge=is_challenge)
        html_k = create_page(selected_level, selected_sub, qs, is_key=True, q_margin=q_margin, ws_height=ws_height, brand_name=brand_name, is_challenge=is_challenge)
        
        st.session_state['worksheet_html'] = html_w
        st.session_state['answerkey_html'] = html_k
        
        ebook_body = f'\n<div class="a4-wrapper">{extract_body(html_w)}</div>\n<div class="a4-wrapper">{extract_body(html_k)}</div>\n'
        
        bg_color = "#2c3e50" if is_challenge else "#525659"
        
        full_ebook_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap" rel="stylesheet"><style>@page {{ size: A4; margin: 15mm; }} @media screen {{ body {{ font-family: 'Sarabun', sans-serif; background-color: {bg_color}; display: flex; flex-direction: column; align-items: center; padding: 40px 0; margin: 0; }} .a4-wrapper {{ width: 210mm; min-height: 297mm; background: white; margin-bottom: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.3); padding: 15mm; box-sizing: border-box; }} }} @media print {{ body {{ font-family: 'Sarabun', sans-serif; background: transparent; padding: 0; display: block; margin: 0; }} .a4-wrapper {{ width: 100%; min-height: auto; margin: 0; padding: 0; box-shadow: none; page-break-after: always; }} }} .header {{ text-align: center; border-bottom: 2px solid #333; margin-bottom: 10px; padding-bottom: 10px; }} .header h2 {{ color: {'#c0392b' if is_challenge else '#333'}; }} .q-box {{ margin-bottom: {q_margin}; padding: 10px 15px; page-break-inside: avoid; font-size: 20px; line-height: 1.8; }} .workspace {{ height: {ws_height}; border: 2px dashed #bdc3c7; border-radius: 8px; margin: 15px 0; padding: 10px; color: #95a5a6; font-size: 16px; background-color: #fafbfc; }} .ans-line {{ margin-top: 10px; border-bottom: 1px dotted #999; width: 80%; height: 30px; font-weight: bold; font-size: 20px; display: flex; align-items: flex-end; padding-bottom: 5px; }} .sol-text {{ color: #333; font-size: 18px; display: block; margin-top: 15px; padding: 15px; background-color: #fdf2e9; border-left: 4px solid #d35400; border-radius: 4px; line-height: 1.8; }} .page-footer {{ text-align: right; font-size: 14px; color: #95a5a6; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }} </style></head><body>{ebook_body}</body></html>"""

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
    st.success(f"✅ โค้ดอัปเดตเรียบร้อยครับ! เปลี่ยนการอธิบายเป็นรูปแบบ Step by Step เชิงสมการ โดยระบุคุณสมบัติการเท่ากัน (นำ...มาบวก/ลบ/คูณ/หาร ทั้งสองข้าง) พร้อมสรุป 'สมการล่าสุด' ทุกบรรทัดครับ")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📄 โหลดเฉพาะโจทย์", data=st.session_state['worksheet_html'], file_name=f"{st.session_state['filename_base']}_Worksheet.html", mime="text/html", use_container_width=True)
        st.download_button("🔑 โหลดเฉพาะเฉลย", data=st.session_state['answerkey_html'], file_name=f"{st.session_state['filename_base']}_AnswerKey.html", mime="text/html", use_container_width=True)
    with c2:
        st.download_button("📚 โหลดรวมเล่ม E-Book", data=st.session_state['ebook_html'], file_name=f"{st.session_state['filename_base']}_Full_EBook.html", mime="text/html", use_container_width=True)
        st.download_button("🗂️ โหลดแพ็กเกจ (.zip)", data=st.session_state['zip_data'], file_name=f"{st.session_state['filename_base']}.zip", mime="application/zip", use_container_width=True)
    st.markdown("---")
    components.html(st.session_state['ebook_html'], height=800, scrolling=True)
