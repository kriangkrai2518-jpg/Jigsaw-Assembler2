import streamlit as st
import os
import numpy as np
import PIL.Image, PIL.ImageDraw, PIL.ImageFont
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip

# --- FIX PILLOW 10+ ANTIALIAS ---
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# --- CONFIGURATION ---
st.set_page_config(page_title="Jigsaw Assembler Pro", layout="wide")
st.title("🎬 Jigsaw Universal Assembler (Images & Video)")

# --- UI LAYOUT ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📁 Upload Media Assets")
    # ปรับให้รับได้ทุกประเภทไฟล์ภาพและวิดีโอยอดนิยม
    uploaded_files = st.file_uploader("Add Files (MP4, JPG, PNG, etc.)", 
                                     type=["mp4", "mov", "avi", "jpg", "jpeg", "png"], 
                                     accept_multiple_files=True)
    
    custom_captions = {}
    if uploaded_files:
        st.subheader("📝 Edit Thai Captions")
        for i, file in enumerate(uploaded_files):
            custom_captions[file.name] = st.text_input(f"Subtitle for: {file.name}", f"ฉากที่ {i+1}")

    start_btn = st.button("🚀 Start Assembly")

with col2:
    st.header("📟 System Terminal")
    terminal_log = st.empty()
    log_content = ""

def write_to_terminal(text):
    global log_content
    log_content += text + "\n"
    terminal_log.code(log_content)

# --- THAI SUBTITLE ENGINE ---
def create_subtitle_image(text, width, height):
    img = PIL.Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = PIL.ImageDraw.Draw(img)
    font_path = "Kanit-Bold.ttf" 
    
    try:
        font = PIL.ImageFont.truetype(font_path, 65) if os.path.exists(font_path) else PIL.ImageFont.load_default()
    except:
        font = PIL.ImageFont.load_default()

    text_bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    
    padding = 20
    bg_x0, bg_y0 = (width-tw)//2 - padding, height - 150 - padding
    bg_x1, bg_y1 = (width+tw)//2 + padding, height - 150 + th + padding
    draw.rectangle([bg_x0, bg_y0, bg_x1, bg_y1], fill=(0, 0, 0, 180))
    draw.text(((width - tw) // 2, height - 150), text, font=font, fill=(255, 255, 255, 255))
    return np.array(img)

# --- PROCESSING ENGINE ---
if start_btn and uploaded_files:
    write_to_terminal("📌 เริ่มต้นระบบ Universal Assembly...")
    clips = []
    temp_files = []

    try:
        for uploaded_file in uploaded_files:
            file_ext = uploaded_file.name.lower().split('.')[-1]
            write_to_terminal(f"📥 กำลังประมวลผล: {uploaded_file.name} ({file_ext})")
            
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            temp_files.append(temp_path)

            # --- LOGIC: ตรวจสอบว่าเป็นภาพหรือวิดีโอ ---
            if file_ext in ['jpg', 'jpeg', 'png']:
                # ถ้าเป็นภาพ ให้สร้าง Clip ยาว 3 วินาที (ปรับเปลี่ยนเลข 3 ได้ตามใจชอบ)
                clip = ImageClip(temp_path).set_duration(3).resize(height=1080)
                write_to_terminal(f"🖼️ ตรวจพบไฟล์ภาพ: ตั้งค่าแสดงผล 3 วินาที")
            else:
                # ถ้าเป็นวิดีโอ
                clip = VideoFileClip(temp_path).resize(height=1080)
                write_to_terminal(f"📹 ตรวจพบไฟล์วิดีโอ: ความยาว {clip.duration} วินาที")

            w, h = clip.size
            thai_text = custom_captions.get(uploaded_file.name, "")
            
            # ใส่ซับไตเติ้ล
            txt_img = create_subtitle_image(thai_text, w, h)
            txt_clip = ImageClip(txt_img).set_duration(clip.duration).set_position('center')

            combined = CompositeVideoClip([clip, txt_clip])
            clips.append(combined)
            write_to_terminal(f"✅ เตรียมพร้อมฉาก: '{thai_text}'")

        if clips:
            write_to_terminal("🎬 กำลังผสมผสาน Assets ทั้งหมดเป็นคลิปเดียว...")
            final = concatenate_videoclips(clips, method="compose")
            
            output_file = "Jigsaw_Story_Result.mp4"
            final.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")

            write_to_terminal("🎊 เสร็จสมบูรณ์! พร้อมดาวน์โหลดแล้ว")
            st.success("✅ สร้างวิดีโอจากภาพและวิดีโอเรียบร้อย!")
            
            with open(output_file, 'rb') as v:
                st.video(v.read())
                st.download_button("📥 Download Final Story", data=v, file_name=output_file, mime="video/mp4")

    except Exception as e:
        write_to_terminal(f"❌ ERROR: {str(e)}")
        st.error(f"เกิดข้อผิดพลาด: {e}")

    finally:
        write_to_terminal("🧹 ทำความสะอาด Cache...")
        for c in clips:
            try: c.close()
            except: pass
        for f in temp_files:
            try:
                if os.path.exists(f): os.remove(f)
            except: pass
        write_to_terminal("✨ ระบบ Ready")

else:
    if start_btn:
        st.warning("กรุณาอัปโหลดไฟล์ก่อนนะครับคุณ Kriangkrai")
