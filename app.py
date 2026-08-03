import streamlit as st
import requests
import pandas as pd
import os
import urllib.parse
from datetime import datetime
from collections import Counter
import json

# --- הגדרות ה-API החדש מ-RapidAPI ---
API_KEY = "f12e948562msh6f3e335a467b3d5p121373jsn707b22eb9ba6"
API_HOST = "free-api-live-football-data.p.rapidapi.com"
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

CSV_FILE = "my_games.csv"
THEME_FILE = "theme.txt"
UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="Football Tracker", layout="wide", page_icon="⚽", initial_sidebar_state="collapsed")

# --- פונקציות עיצוב ---
def load_theme():
    if os.path.exists(THEME_FILE):
        with open(THEME_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "כהה 🌙"

def save_theme(theme_choice):
    with open(THEME_FILE, "w", encoding="utf-8") as f:
        f.write(theme_choice)

def change_theme():
    save_theme(st.session_state.theme_radio)
    st.session_state.theme = st.session_state.theme_radio

if 'theme' not in st.session_state: st.session_state.theme = load_theme()
if 'saved_matches' not in st.session_state: st.session_state.saved_matches = []
if 'search_results' not in st.session_state: st.session_state.search_results = []

# --- CSS ---
is_light = (st.session_state.theme == "בהיר ☀️")
bg_color = "#f8f9fa" if is_light else "#0e1117"
text_color = "#2b2b2b" if is_light else "#ffffff"
card_bg = "#ffffff" if is_light else "linear-gradient(145deg, #1a1c23, #252730)"
card_border = "1px solid #e9ecef" if is_light else "1px solid rgba(255,255,255,0.05)"
radio_bg = "#e9ecef" if is_light else "rgba(255, 255, 255, 0.05)"
radio_hover = "#dee2e6" if is_light else "rgba(255, 255, 255, 0.1)"
shadow_base = "0 4px 6px rgba(0,0,0,0.05)" if is_light else "0 4px 15px rgba(0,0,0,0.3)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700;900&display=swap');
html, body, [data-testid="stAppViewContainer"] {{ overflow-x: hidden !important; max-width: 100vw !important; }}
html, body, div, p, label, h1, h2, h3, h4, h5, h6, li, button, input, span {{ font-family: 'Heebo', sans-serif; }}
#MainMenu {{visibility: hidden;}} header {{visibility: hidden;}} footer {{visibility: hidden;}}
[data-testid="stAppViewContainer"] {{ background-color: {bg_color} !important; }}
.stMarkdown, .stText, p, label, h1, h2, h3, h4, h5, h6, li {{ color: {text_color} !important; }}
.app-logo-wrapper {{ display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 35px; margin-top: 10px; direction: rtl; flex-wrap: wrap; }}
.app-icon-box {{ width: 65px; height: 65px; background: linear-gradient(135deg, #007bff, #00d2ff); border-radius: 18px; display: flex; align-items: center; justify-content: center; font-size: 2.5em; box-shadow: 0 8px 20px rgba(0,123,255,0.4); transform: rotate(-10deg); }}
.app-text-box {{ display: flex; flex-direction: column; text-align: right; }}
.app-text-main {{ font-size: 2.5em; font-weight: 900; color: {text_color} !important; line-height: 1; letter-spacing: -1px; }}
.app-text-sub {{ font-size: 1.1em; font-weight: 700; color: #007bff; letter-spacing: 2px; text-transform: uppercase; margin-top: 4px; }}
div.row-widget.stRadio > div {{ flex-direction: row; justify-content: center; background-color: {radio_bg}; padding: 6px; border-radius: 30px; gap: 5px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); flex-wrap: wrap; }}
div.row-widget.stRadio > div > label {{ background-color: transparent !important; padding: 8px 18px !important; border-radius: 22px !important; cursor: pointer; font-weight: 700; font-size: 0.95em; transition: all 0.3s ease; }}
div.row-widget.stRadio > div > label[data-checked="true"] {{ background-color: {'#ffffff' if is_light else '#3a3f50'} !important; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
div.row-widget.stRadio > div > label:hover {{ background-color: {radio_hover} !important; }}
.stat-card, .match-card {{ background: {card_bg}; border-radius: 16px; color: {text_color} !important; box-shadow: {shadow_base}; border: {card_border}; padding: 15px; margin-bottom: 12px; width: 100%; box-sizing: border-box; }}
.stat-card {{ text-align: center; padding: 20px 15px; }}
.stat-value {{ font-size: 2.2em; font-weight: 900; margin: 8px 0; color: #007bff !important; }}
.stat-title {{ font-size: 1em; color: {'#7f8c8d' if is_light else '#adb5bd'} !important; font-weight: 700; text-transform: uppercase; }}
.stButton > button {{ border-radius: 12px !important; font-weight: bold !important; width: 100% !important; }}
</style>
""", unsafe_allow_html=True)

# --- ניהול קובץ היומן ---
def load_saved_matches():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE).fillna('')
        if not df.empty and 'תאריך' in df.columns:
            df = df.sort_values(by='תאריך', ascending=False)
        return df.to_dict('records')
    return []

if not st.session_state.saved_matches:
    st.session_state.saved_matches = load_saved_matches()

def save_match_to_file(match_data):
    current_data = load_saved_matches()
    if 'הייתי_במשחק' not in match_data:
        match_data['הייתי_במשחק'] = False
    current_data.insert(0, match_data)
    df = pd.DataFrame(current_data)
    if not df.empty and 'תאריך' in df.columns:
        df = df.sort_values(by='תאריך', ascending=False)
    df.to_csv(CSV_FILE, index=False)
    st.session_state.saved_matches = df.to_dict('records')

def delete_match_from_file(match_id):
    current_data = load_saved_matches()
    current_data = [m for m in current_data if str(m.get('ID_משחק')) != str(match_id)]
    df = pd.DataFrame(current_data)
    if df.empty:
        df = pd.DataFrame(columns=["ID_משחק", "תאריך", "תחרות", "מארחת", "תוצאה", "אורחת", "אצטדיון", "הייתי_במשחק"])
    else:
        df = df.sort_values(by='תאריך', ascending=False)
    df.to_csv(CSV_FILE, index=False)
    st.session_state.saved_matches = df.to_dict('records')
    img_path = os.path.join(UPLOAD_DIR, f"{match_id}.png")
    if os.path.exists(img_path): os.remove(img_path)

def update_attendance_in_file(match_id, attended_status):
    current_data = load_saved_matches()
    for m in current_data:
        if str(m.get('ID_משחק')) == str(match_id):
            m['הייתי_במשחק'] = attended_status
            break
    df = pd.DataFrame(current_data)
    if not df.empty and 'תאריך' in df.columns:
        df = df.sort_values(by='תאריך', ascending=False)
    df.to_csv(CSV_FILE, index=False)
    st.session_state.saved_matches = df.to_dict('records')

@st.dialog("אישור מחיקה")
def delete_confirmation_dialog(match_id, match_desc):
    st.write(f"האם למחוק את המשחק **{match_desc}**?")
    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("למחוק אצלי", use_container_width=True, type="primary"):
            delete_match_from_file(match_id)
            st.rerun()
    with col2:
        if st.button("ביטול", use_container_width=True):
            st.rerun()

# --- פונקציית חיפוש ב-API החדש של RapidAPI ---
@st.cache_data(show_spinner=False)
def search_matches_api(query):
    url = f"https://{API_HOST}/football-search" # דוגמה לחיפוש כללי בשרת
    querystring = {"search": query}
    try:
        response = requests.get(url, headers=HEADERS, params=querystring)
        return response.json()
    except:
        return {}

def match_card_html(date, competition, stadium, home_team, away_team, score, theme_name, attended=False):
    is_lht = (theme_name == "בהיר ☀️")
    tc_inline = "#333333 !important" if is_lht else "white !important"
    att_tag = "<br><span style='background: linear-gradient(45deg, #28a745, #20c997); color: white !important; padding: 2px 8px; border-radius: 15px; font-size: 0.75em; font-weight: 900; display: inline-block; margin-top: 4px;'>🎟️ באצטדיון</span>" if attended else ""
    
    return f"""
    <div class='match-card'>
        <div style='text-align: center; color: #888 !important; font-size: 0.85em; font-weight: bold; margin-bottom: 10px;'>
            📅 <span style='color: {tc_inline};'>{date}</span> &nbsp;|&nbsp; 🏆 {competition} &nbsp;|&nbsp; 🏟️ {stadium} {att_tag}
        </div>
        <div style='text-align: center; font-size: 1.2em; display: flex; align-items: center; justify-content: center; color: {tc_inline}; font-weight: 900; flex-wrap: wrap; gap: 5px;'>
            <span>{home_team}</span> 
            <span style='background: linear-gradient(135deg, #007bff, #0056b3); color: white !important; padding: 4px 15px; border-radius: 20px; font-weight: 900; margin: 0 10px; font-size: 0.9em; letter-spacing: 1px;'>{score}</span> 
            <span>{away_team}</span>
        </div>
    </div>
    """

# --- פריסת תפריט עיצוב ---
col_empty, col_theme = st.columns([9, 1])
with col_theme:
    st.radio("עיצוב:", ["כהה 🌙", "בהיר ☀️"], index=0 if st.session_state.theme == "כהה 🌙" else 1, horizontal=True, label_visibility="collapsed", key="theme_radio", on_change=change_theme)

# --- לוגו ---
st.markdown("""
<div class="app-logo-wrapper">
    <div class="app-icon-box">⚽</div>
    <div class="app-text-box">
        <div class="app-text-main">יומן המשחקים</div>
        <div class="app-text-sub">הכדורגל שלי</div>
    </div>
</div>
""", unsafe_allow_html=True)

nav_choice = st.radio("ניווט", ["📋 יומן המשחקים", "🔍 חיפוש ב-API", "➕ הוספה ידנית", "📊 סטטיסטיקות אישיות"], index=0, horizontal=True, label_visibility="collapsed")
st.write("---")

# ==========================================
# מסך 1: יומן המשחקים
# ==========================================
if nav_choice == "📋 יומן המשחקים":
    if len(st.session_state.saved_matches) > 0:
        with st.container():
            col_search, col_filter = st.columns(2)
            with col_search:
                search_query = st.text_input("חיפוש קבוצה או אצטדיון...", "")
            with col_filter:
                all_comps = list(set([m.get('תחרות', '') for m in st.session_state.saved_matches if m.get('תחרות', '')]))
                selected_comp = st.selectbox("סנן לפי תחרות:", ["כל התחרויות"] + all_comps)
        
        st.write("---")
        filtered_matches = [m for m in st.session_state.saved_matches if search_query.lower() in f"{m.get('מארחת', '')} {m.get('אורחת', '')} {m.get('אצטדיון', '')}".lower() and (selected_comp == "כל התחרויות" or m.get('תחרות', '') == selected_comp)]
        
        st.markdown(f"<p style='color: gray !important; font-size: 0.9em; font-weight: bold;'>מציג {len(filtered_matches)} מתוך {len(st.session_state.saved_matches)} משחקים שמורים</p>", unsafe_allow_html=True)
        
        for match in filtered_matches:
            date, competition, stadium = match.get('תאריך', ''), match.get('תחרות', ''), match.get('אצטדיון', '')
            home_team, away_team, score = match.get('מארחת', ''), match.get('אורחת', ''), match.get('תוצאה', '')
            match_id, attended = match.get('ID_משחק'), match.get('הייתי_במשחק', False)
            
            col_match, col_attend, col_del = st.columns([10, 3, 1])
            with col_del:
                st.write(""); st.write("")
                if st.button("🗑️", key=f"del_out_{match_id}"): delete_confirmation_dialog(match_id, f"{home_team} נגד {away_team}")
            with col_attend:
                st.write(""); st.write(""); st.write("")
                new_attended = st.checkbox("הייתי באצטדיון 🏟️", value=attended, key=f"att_{match_id}")
                if new_attended != attended:
                    update_attendance_in_file(match_id, new_attended)
                    if new_attended: st.balloons()
                    st.rerun()
            with col_match:
                st.markdown(match_card_html(date, competition, stadium, home_team, away_team, score, st.session_state.theme, attended), unsafe_allow_html=True)
                with st.expander("📸 זיכרון מהיציע ותמונות"):
                    img_path = os.path.join(UPLOAD_DIR, f"{match_id}.png")
                    if os.path.exists(img_path):
                        c1, c2, c3 = st.columns([1, 2, 1])
                        with c2:
                            st.image(img_path, use_container_width=True, clamp=True)
                            if st.button("🗑️ מחק תמונה", key=f"del_img_{match_id}"):
                                os.remove(img_path); st.rerun()
                    else:
                        up_file = st.file_uploader("העלה תמונה מהמשחק", type=["png", "jpg", "jpeg"], key=f"up_{match_id}")
                        if up_file:
                            with open(img_path, "wb") as f: f.write(up_file.getbuffer())
                            st.rerun()
            st.write("")
    else:
        st.info("היומן שלך ריק.")

# ==========================================
# מסך 2: חיפוש ב-API החדש
# ==========================================
elif nav_choice == "🔍 חיפוש ב-API":
    st.markdown("<h3 style='text-align: center; margin-bottom: 20px; font-weight: 900; font-size: 1.5em;'>חיפוש משחקים דרך ה-API החדש 🔍</h3>", unsafe_allow_html=True)
    
    query = st.text_input("הקלד שם קבוצה או מילת חיפוש באנגלית:")
    if st.button("חפש בשרת", type="primary", use_container_width=True):
        if query.strip():
            with st.spinner("מחפש נתונים מול RapidAPI..."):
                res = search_matches_api(query.strip())
                st.write("תוצאות מהשרת החדש:")
                st.json(res) # מציג את מבנה הנתונים כדי שנוכל להתאים בדיוק לפי מה שהשרת מחזיר
        else:
            st.warning("נא להקליד מילת חיפוש.")

# ==========================================
# מסך 3: הוספה ידנית (גיבוי אמין תמיד)
# ==========================================
elif nav_choice == "➕ הוספה ידנית":
    st.markdown("<h3 style='text-align: center; margin-bottom: 20px; font-weight: 900; font-size: 1.5em;'>הוספת משחק ידנית 📝</h3>", unsafe_allow_html=True)
    with st.form("manual_form"):
        c1, c2 = st.columns(2)
        with c1: h_team = st.text_input("קבוצת בית")
        with c2: a_team = st.text_input("קבוצת חוץ")
        c3, c4 = st.columns(2)
        with c3: s_home = st.number_input("שערים - בית", min_value=0, value=0)
        with c4: s_away = st.number_input("שערים - חוץ", min_value=0, value=0)
        c5, c6 = st.columns(2)
        with c5: m_date = st.date_input("תאריך", value=datetime.now())
        with c6: comp = st.text_input("מסגרת / תחרות")
        stadium = st.text_input("אצטדיון")
        attended = st.checkbox("הייתי באצטדיון 🏟️")
        
        if st.form_submit_button("שמור משחק ליומן 💾", use_container_width=True):
            if h_team and a_team and comp:
                match_data = {
                    "ID_משחק": str(int(datetime.now().timestamp() * 1000)),
                    "תאריך": str(m_date), "תחרות": comp, "מארחת": h_team,
                    "תוצאה": f"{s_home} - {s_away}", "אורחת": a_team,
                    "אצטדיון": stadium or "לא ידוע", "הייתי_במשחק": attended
                }
                save_match_to_file(match_data)
                if attended: st.balloons()
                st.success("המשחק נוסף בהצלחה!")
            else:
                st.warning("נא למלא שדות חובה.")

# ==========================================
# מסך 4: סטטיסטיקות
# ==========================================
elif nav_choice == "📊 סטטיסטיקות אישיות":
    st.markdown("<h3 style='text-align: center; margin-bottom: 25px; font-weight: 900; font-size: 1.5em;'>הסטטיסטיקות שלך 📈</h3>", unsafe_allow_html=True)
    saved = st.session_state.saved_matches
    if not saved:
        st.info("אין נתונים להצגה.")
    else:
        total_matches = len(saved)
        total_goals = sum([int(m['תוצאה'].split('-')[0]) + int(m['תוצאה'].split('-')[1]) for m in saved if '-' in m.get('תוצאה', '')])
        total_attended = sum([1 for m in saved if m.get('הייתי_במשחק')])
        
        c1, c2 = st.columns(2)
        with c1: st.markdown(f"<div class='stat-card'><div class='stat-title'>משחקים</div><div class='stat-value'>{total_matches}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='stat-card'><div class='stat-title'>שערים</div><div class='stat-value'>{total_goals}</div></div>", unsafe_allow_html=True)
