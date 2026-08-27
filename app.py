import streamlit as st
import requests
import pandas as pd
import os
import urllib.parse
from deep_translator import GoogleTranslator
from datetime import datetime
from collections import Counter
import json

# --- הגדרות ה-API החדש (TheStatsAPI) והמפתח שלך ---
API_KEY = "fapi_WDeKpURK3YzNbWBySpgzu9MEtFvkP36M"
BASE_URL = "https://www.thestatsapi.com/api/football"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

CSV_FILE = "my_games.csv"
THEME_FILE = "theme.txt"
UPLOAD_DIR = "uploads"

# יצירת תיקייה לתמונות אם היא לא קיימת
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="Football Tracker", layout="wide", page_icon="⚽", initial_sidebar_state="collapsed")

# --- ניהול מונה קריאות ל-API והתראות ---
if 'api_call_count' not in st.session_state:
    st.session_state.api_call_count = 0

def increment_api_call():
    st.session_state.api_call_count += 1

# --- פונקציות לשמירה וטעינה של בחירת העיצוב (מצב יום/לילה) ---
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

# --- הגדרת המשתנים הראשוניים ---
if 'theme' not in st.session_state: st.session_state.theme = load_theme()
if 'saved_matches' not in st.session_state: st.session_state.saved_matches = []
if 'search_results' not in st.session_state: st.session_state.search_results = []
if 't1_opts' not in st.session_state: st.session_state.t1_opts = []
if 't2_opts' not in st.session_state: st.session_state.t2_opts = []

# --- בניית ה-CSS הדינמי המותאם למובייל ---
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

html, body, [data-testid="stAppViewContainer"] {{
    overflow-x: hidden !important;
    max-width: 100vw !important;
}}

html, body, div, p, label, h1, h2, h3, h4, h5, h6, li, button, input, span {{
    font-family: 'Heebo', sans-serif;
}}
.material-icons, .material-symbols-rounded, [data-testid="stExpanderToggleIcon"] {{
    font-family: 'Material Symbols Rounded', 'Material Icons' !important;
}}

#MainMenu {{visibility: hidden;}}
header {{visibility: hidden;}}
footer {{visibility: hidden;}}

[data-testid="stAppViewContainer"] {{
    background-color: {bg_color} !important;
}}

.stMarkdown, .stText, p, label, h1, h2, h3, h4, h5, h6, li {{
    color: {text_color} !important;
}}

details > summary {{
    list-style: none !important;
}}
details > summary::-webkit-details-marker {{
    display: none !important;
}}
[data-testid="stExpanderToggleIcon"],
summary > div > span:last-child,
summary svg,
summary .material-icons {{
    display: none !important;
    font-size: 0 !important;
    color: transparent !important;
    opacity: 0 !important;
    visibility: hidden !important;
}}

.app-logo-wrapper {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    margin-bottom: 35px;
    margin-top: 10px;
    direction: rtl;
    flex-wrap: wrap;
}}
.app-icon-box {{
    width: 65px;
    height: 65px;
    background: linear-gradient(135deg, #007bff, #00d2ff);
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5em;
    box-shadow: 0 8px 20px rgba(0,123,255,0.4);
    transform: rotate(-10deg);
}}
.app-text-box {{
    display: flex;
    flex-direction: column;
    text-align: right;
}}
.app-text-main {{
    font-size: 2.5em;
    font-weight: 900;
    color: {text_color} !important;
    line-height: 1;
    letter-spacing: -1px;
}}
.app-text-sub {{
    font-size: 1.1em;
    font-weight: 700;
    color: #007bff;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 4px;
}}

div.row-widget.stRadio > div {{
    flex-direction: row;
    justify-content: center;
    background-color: {radio_bg};
    padding: 6px;
    border-radius: 30px;
    gap: 5px;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
    flex-wrap: wrap;
}}
div.row-widget.stRadio > div > label {{
    background-color: transparent !important;
    padding: 8px 18px !important;
    border-radius: 22px !important;
    cursor: pointer;
    font-weight: 700;
    font-size: 0.95em;
    transition: all 0.3s ease;
}}
div.row-widget.stRadio > div > label[data-checked="true"] {{
    background-color: {'#ffffff' if is_light else '#3a3f50'} !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}}
div.row-widget.stRadio > div > label:hover {{
    background-color: {radio_hover} !important;
}}

.vs-badge {{
    text-align: center;
    margin-top: 5px;
    font-size: 1.5em;
    font-weight: 900;
    color: {'#adb5bd' if is_light else '#6c757d'};
}}

.stat-card, .match-card {{
    background: {card_bg};
    border-radius: 16px;
    color: {text_color} !important;
    box-shadow: {shadow_base};
    border: {card_border};
    padding: 15px;
    margin-bottom: 12px;
    width: 100%;
    box-sizing: border-box;
}}
.stat-card {{
    text-align: center;
    padding: 20px 15px;
}}
.stat-value {{
    font-size: 2.2em;
    font-weight: 900;
    margin: 8px 0;
    color: #007bff !important;
}}
.stat-title {{
    font-size: 1em;
    color: {'#7f8c8d' if is_light else '#adb5bd'} !important;
    font-weight: 700;
    text-transform: uppercase;
}}

.stButton > button {{
    border-radius: 12px !important;
    font-weight: bold !important;
    width: 100% !important;
}}
</style>
""", unsafe_allow_html=True)


# --- פונקציות לניהול קובץ השמירה של היומן ---
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
    if os.path.exists(img_path):
        os.remove(img_path)

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

@st.cache_data(show_spinner=False)
def search_teams_api(team_name):
    increment_api_call()
    url = f"{BASE_URL}/teams"
    try:
        response = requests.get(url, headers=HEADERS, params={"search": team_name})
        data = response.json()
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get('data', data.get('teams', []))
        return []
    except:
        return []

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

# --- התראה קריטית על קריאות API ---
if st.session_state.api_call_count >= 90:
    st.error(f"⚠️ **התראה קריטית!** הגעת ל-{st.session_state.api_call_count} קריאות API בסשן הנוכחי.")
else:
    st.sidebar.markdown(f"📊 **קריאות API בסשן:** {st.session_state.api_call_count}")

# --- פריסת תפריט כפתור העיצוב ---
col_empty, col_theme = st.columns([9, 1])
with col_theme:
    st.radio(
        "עיצוב:", 
        ["כהה 🌙", "בהיר ☀️"], 
        index=0 if st.session_state.theme == "כהה 🌙" else 1, 
        horizontal=True, 
        label_visibility="collapsed", 
        key="theme_radio", 
        on_change=change_theme
    )

# --- הלוגו ---
st.markdown("""
<div class="app-logo-wrapper">
    <div class="app-icon-box">⚽</div>
    <div class="app-text-box">
        <div class="app-text-main">יומן המשחקים</div>
        <div class="app-text-sub">הכדורגל שלי</div>
    </div>
</div>
""", unsafe_allow_html=True)

nav_choice = st.radio("ניווט", ["📋 יומן המשחקים", "🔍 חיפוש והוספת משחקים", "📊 סטטיסטיקות אישיות"], index=1, horizontal=True, label_visibility="collapsed")
st.write("---")

if nav_choice != "🔍 חיפוש והוספת משחקים":
    st.session_state.t1_opts = []
    st.session_state.t2_opts = []
    st.session_state.search_results = []

# ==========================================
# מסך 1: יומן המשחקים השמורים
# ==========================================
if nav_choice == "📋 יומן המשחקים":
    if len(st.session_state.saved_matches) > 0:
        
        today = datetime.now()
        memories = []
        for match in st.session_state.saved_matches:
            try:
                date_str = match.get('תאריך', '')[:10]
                d_obj = datetime.strptime(date_str, "%Y-%m-%d")
                if d_obj.month == today.month and d_obj.day == today.day and d_obj.year < today.year:
                    memories.append((match, today.year - d_obj.year))
            except:
                pass

        if memories:
            st.markdown("<h3 style='text-align: center; color: #ffc107; margin-bottom: 15px; font-weight: 900;'>✨ ביום הזה בעבר...</h3>", unsafe_allow_html=True)
            for mem_match, years in memories:
                h_team = mem_match.get('מארחת', '')
                a_team = mem_match.get('אורחת', '')
                score = mem_match.get('תוצאה', '0 - 0')
                attended = mem_match.get('הייתי_במשחק', False)
                years_str = "שנה" if years == 1 else "שנתיים" if years == 2 else f"{years} שנים"
                
                if attended:
                    msg = f"היום לפני {years_str} הייתי באצטדיון במשחק בין {h_team} ל-{a_team} (תוצאה: {score})! 🏟️"
                else:
                    msg = f"היום לפני {years_str} ראיתי מהספה את {h_team} נגד {a_team} והתוצאה הייתה {score} 📺"
                    
                bg_mem = "linear-gradient(135deg, #fff8e1, #ffecb3)" if is_light else "linear-gradient(135deg, rgba(255, 193, 7, 0.1), rgba(255, 193, 7, 0.05))"
                bord_mem = "#ffeeba" if is_light else "rgba(255, 193, 7, 0.3)"
                tc_mem = "#856404" if is_light else "#ffc107"
                
                st.markdown(f"""
                <div style='background: {bg_mem}; padding: 15px; border-radius: 12px; border: 1px solid {bord_mem}; text-align: center; font-size: 1.1em; color: {tc_mem} !important; font-weight: 900; margin-bottom: 15px;'>
                    {msg}
                </div>
                """, unsafe_allow_html=True)
            st.write("---")

        with st.container():
            col_search, col_filter = st.columns(2)
            with col_search:
                search_query = st.text_input("חיפוש קבוצה או אצטדיון...", "")
            with col_filter:
                all_comps = list(set([m.get('תחרות', '') for m in st.session_state.saved_matches if m.get('תחרות', '')]))
                selected_comp = st.selectbox("סנן לפי תחרות:", ["כל התחרויות"] + all_comps)
        
        st.write("---")
        
        filtered_matches = []
        for match in st.session_state.saved_matches:
            match_str = f"{match.get('מארחת', '')} {match.get('אורחת', '')} {match.get('אצטדיון', '')}".lower()
            text_match = search_query.lower() in match_str
            comp_match = (selected_comp == "כל התחרויות" or match.get('תחרות', '') == selected_comp)
            if text_match and comp_match:
                filtered_matches.append(match)
        
        st.markdown(f"<p style='color: gray !important; font-size: 0.9em; font-weight: bold;'>מציג {len(filtered_matches)} מתוך {len(st.session_state.saved_matches)} משחקים שמורים ביומן</p>", unsafe_allow_html=True)
        
        for idx, match in enumerate(filtered_matches):
            date = match.get('תאריך', '')
            competition = match.get('תחרות', '')
            stadium = match.get('אצטדיון', '')
            home_team = match.get('מארחת', '')
            away_team = match.get('אורחת', '')
            score = match.get('תוצאה', '')
            match_id = match.get('ID_משחק')
            attended = match.get('הייתי_במשחק', False)
            
            col_match, col_attend, col_del = st.columns([10, 3, 1])
            with col_del:
                st.write("")
                st.write("") 
                if st.button("🗑️", key=f"del_out_{match_id}"):
                    delete_confirmation_dialog(match_id, f"{home_team} נגד {away_team}")
                    
            with col_attend:
                st.write("")
                st.write("")
                st.write("")
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
                                os.remove(img_path)
                                st.rerun()
                    else:
                        uploaded_file = st.file_uploader("העלה תמונה מהמשחק (סלפי, כרטיס...)", type=["png", "jpg", "jpeg"], key=f"up_{match_id}")
                        if uploaded_file is not None:
                            with open(img_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            st.rerun()
            st.write("")
    else:
        st.info("הרשימה שלך ריקה. עבור למסך החיפוש כדי להתחיל!")

# ==========================================
# מסך 2: חיפוש משחקים חדשים
# ==========================================
elif nav_choice == "🔍 חיפוש והוספת משחקים":
    st.markdown("<h3 style='text-align: center; margin-bottom: 20px; font-weight: 900; font-size: 1.5em;'>חיפוש משחקים חדשים 🔍</h3>", unsafe_allow_html=True)
    
    with st.container():
        col1, col_vs, col2 = st.columns([5, 1, 5])
        with col1:
            team1_name = st.text_input("team1", placeholder="קבוצה ראשונה (למשל: Real Madrid)", label_visibility="collapsed")
        with col_vs:
            st.markdown("<div class='vs-badge'>VS</div>", unsafe_allow_html=True)
        with col2:
            team2_name = st.text_input("team2", placeholder="קבוצה שנייה (למשל: Barcelona)", label_visibility="collapsed")

        st.write("")
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            search_teams_clicked = st.button("🔍 חפש קבוצות במאגר", use_container_width=True, type="primary")

    if search_teams_clicked:
        if team1_name.strip() == "" or team2_name.strip() == "":
            st.warning("אנא הכנס שמות של שתי קבוצות.")
        else:
            with st.spinner('מחפש קבוצות בשרת...'):
                try:
                    t1_en = GoogleTranslator(source='auto', target='en').translate(team1_name)
                    t2_en = GoogleTranslator(source='auto', target='en').translate(team2_name)
                except:
                    t1_en, t2_en = team1_name, team2_name

                res1 = search_teams_api(t1_en)
                res2 = search_teams_api(t2_en)
                
                if res1 or res2:
                    st.session_state.t1_opts = res1 if res1 else [{'id': t1_en, 'name': team1_name}]
                    st.session_state.t2_opts = res2 if res2 else [{'id': t2_en, 'name': team2_name}]
                    st.session_state.search_results = []
                else:
                    st.warning("⚠️ לא נמצאו תוצאות מדויקות, משתמש בשמות שהוזנו.")
                    st.session_state.t1_opts = [{'id': t1_en, 'name': team1_name}]
                    st.session_state.t2_opts = [{'id': t2_en, 'name': team2_name}]

    valid_t1 = isinstance(st.session_state.t1_opts, list) and len(st.session_state.t1_opts) > 0
    valid_t2 = isinstance(st.session_state.t2_opts, list) and len(st.session_state.t2_opts) > 0

    if valid_t1 and valid_t2:
        st.markdown("<hr style='margin: 20px 0; border: 0; border-top: 2px dashed rgba(128,128,128,0.2);'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            t1_sel = st.selectbox("בחר קבוצה 1:", options=st.session_state.t1_opts, format_func=lambda x: x.get('name', str(x)))
        with c2:
            t2_sel = st.selectbox("בחר קבוצה 2:", options=st.session_state.t2_opts, format_func=lambda x: x.get('name', str(x)))
            
        st.write("")
        _, btn_col2, _ = st.columns([1, 2, 1])
        with btn_col2:
            fetch_matches = st.button("שלב 2: הצג משחקים ביניהן 🚀", use_container_width=True, type="primary")
            
        if fetch_matches:
            with st.spinner("שולף היסטוריית משחקים..."):
                increment_api_call()
                try:
                    t1_id = t1_sel.get('id') if isinstance(t1_sel, dict) else t1_sel
                    t2_id = t2_sel.get('id') if isinstance(t2_sel, dict) else t2_sel
                    resp = requests.get(f"{BASE_URL}/matches", headers=HEADERS, params={"team_id": t1_id})
                    data = resp.json()
                    matches = data.get('data', data.get('matches', data)) if isinstance(data, dict) else data
                    h2h = []
                    if isinstance(matches, list):
                        for m in matches:
                            teams_str = str(m).lower()
                            if str(t2_id).lower() in teams_str or str(t2_sel.get('name', '')).lower() in teams_str:
                                h2h.append(m)
                    st.session_state.search_results = h2h if h2h else (matches[:15] if isinstance(matches, list) else [])
                except:
                    st.session_state.search_results = []
                    st.warning("לא נמצאו משחקים בין הקבוצות.")

    if len(st.session_state.search_results) > 0:
        st.write("---")
        for idx, match in enumerate(st.session_state.search_results[:15]):
            m_id = match.get('id', f"match_{idx}")
            date = str(match.get('date', ''))[:10]
            stadium = match.get('venue', 'לא ידוע')
            competition = match.get('competition', {}).get('name', 'ליגה') if isinstance(match.get('competition'), dict) else 'ליגה'
            home_team = match.get('homeTeam', {}).get('name', 'בית') if isinstance(match.get('homeTeam'), dict) else 'בית'
            away_team = match.get('awayTeam', {}).get('name', 'חוץ') if isinstance(match.get('awayTeam'), dict) else 'חוץ'
            home_goals = match.get('homeScore', 0)
            away_goals = match.get('awayScore', 0)
            score = f"{home_goals} - {away_goals}"
            
            col_text, col_btn = st.columns([5, 1])
            with col_text:
                st.markdown(match_card_html(date, competition, stadium, home_team, away_team, score, st.session_state.theme), unsafe_allow_html=True)
            with col_btn:
                st.write("")
                st.write("")
                is_saved = any(str(saved.get('ID_משחק')) == str(m_id) for saved in st.session_state.saved_matches)
                if is_saved:
                    st.button("✅", key=f"saved_{m_id}_{idx}", disabled=True, use_container_width=True)
                else:
                    if st.button("➕", key=f"add_{m_id}_{idx}", use_container_width=True):
                        match_data = {
                            "ID_משחק": m_id,
                            "תאריך": date,
                            "תחרות": competition,
                            "מארחת": home_team,
                            "תוצאה": score,
                            "אורחת": away_team,
                            "אצטדיון": stadium,
                            "הייתי_במשחק": False
                        }
                        save_match_to_file(match_data)
                        st.rerun()

# ==========================================
# מסך 3: סטטיסטיקות אישיות ושיתוף
# ==========================================
elif nav_choice == "📊 סטטיסטיקות אישיות":
    st.markdown("<h3 style='text-align: center; margin-bottom: 25px; font-weight: 900; font-size: 1.5em;'>הסטטיסטיקות שלך 📈</h3>", unsafe_allow_html=True)
    
    saved = st.session_state.saved_matches
    if len(saved) == 0:
        st.info("יומן המשחקים שלך ריק עדיין.")
    else:
        total_matches = len(saved)
        total_goals = 0
        total_attended = 0
        teams_counter = Counter()
        stadiums_counter = Counter()
        months_counter = Counter()
        
        hebrew_months = {
            1: "ינואר", 2: "פברואר", 3: "מרץ", 4: "אפריל", 5: "מאי", 6: "יוני",
            7: "יולי", 8: "אוגוסט", 9: "ספטמבר", 10: "אוקטובר", 11: "נובמבר", 12: "דצמבר"
        }

        for match in saved:
            if match.get('הייתי_במשחק', False):
                total_attended += 1
                
            date_str = match.get('תאריך', '')[:10]
            try:
                dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
                m_name = hebrew_months.get(dt_obj.month, str(dt_obj.month))
                months_counter[m_name] += 1
            except:
                pass
                
            score_str = str(match.get('תוצאה', '0 - 0'))
            try:
                parts = score_str.split('-')
                if len(parts) == 2:
                    total_goals += int(parts[0].strip()) + int(parts[1].strip())
            except:
                pass
                
            h_team = match.get('מארחת', '')
            a_team = match.get('אורחת', '')
            if h_team: teams_counter[h_team] += 1
            if a_team: teams_counter[a_team] += 1
            
            stadium = match.get('אצטדיון', '')
            if stadium and stadium != 'None': stadiums_counter[stadium] += 1
            
        avg_goals = round(total_goals / total_matches, 2) if total_matches > 0 else 0
        top_team = teams_counter.most_common(1)[0][0] if teams_counter else "אין נתונים"
        top_month = months_counter.most_common(1)[0][0] if months_counter else "אין נתונים"
        top_stadium = stadiums_counter.most_common(1)[0][0] if stadiums_counter else "אין נתונים"
        
        total_hours = total_matches * 2
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div class='stat-card'><div class='stat-title'>משחקים ביומן</div><div class='stat-value'>🏟️ {total_matches}</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='stat-card'><div class='stat-title'>שערים שראית</div><div class='stat-value'>⚽ {total_goals}</div><div style='color: gray !important; font-size: 0.85em; font-weight: bold;'>ממוצע {avg_goals} למשחק</div></div>", unsafe_allow_html=True)
            
        col3, col4 = st.columns(2)
        with col3:
            st.markdown(f"<div class='stat-card'><div class='stat-title'>קבוצה מובילה</div><div class='stat-value' style='font-size: 1.1em; margin-top: 10px;'>🛡️ {top_team}</div></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='stat-card'><div class='stat-title'>משחקי יציע</div><div class='stat-value' style='font-size: 1.6em; color: #ffc107 !important;'>🎟️ {total_attended}</div></div>", unsafe_allow_html=True)

        col5, col6 = st.columns(2)
        with col5:
            st.markdown(f"<div class='stat-card'><div class='stat-title'>חודש שיא בצפייה</div><div class='stat-value' style='font-size: 1.3em;'>📅 {top_month}</div></div>", unsafe_allow_html=True)
        with col6:
            st.markdown(f"<div class='stat-card'><div class='stat-title'>האצטדיון המוביל</div><div class='stat-value' style='font-size: 1.1em;'>🏟️ {top_stadium}</div></div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class='stat-card' style='margin-top: 12px; background: linear-gradient(135deg, rgba(0,123,255,0.1), rgba(0,210,255,0.05));'>
            <div class='stat-title'>⏱️ סך כל שעות הצפייה בכדורגל</div>
            <div class='stat-value' style='font-size: 2.5em; color: #00d2ff !important;'>~{total_hours} שעות</div>
            <div style='color: gray !important; font-size: 0.9em; font-weight: bold;'>הושקעו בצפייה במשחקים ששמרת ביומן</div>
        </div>
        """, unsafe_allow_html=True)

        st.write("---")
        st.markdown("<h4 style='text-align: center; color: gray !important; margin-bottom: 15px; font-weight: 900; font-size: 1.1em;'>📤 ייצוא ושיתוף</h4>", unsafe_allow_html=True)
        
        df_export = pd.DataFrame(saved)
        csv_export = df_export.to_csv(index=False).encode('utf-8-sig')
        
        wa_text = f"""⚽ *הסטטיסטיקות שלי ביציע ובספה!* ⚽
        
🏟️ משחקים שצפיתי: {total_matches}
⏱️ שעות כדורגל: ~{total_hours} שעות
🎟️ משחקים מהיציע: {total_attended}
🥅 סך הכל שערים שראיתי: {total_goals} ({avg_goals} למשחק!)
🛡️ הקבוצה הנצפית ביותר: {top_team}
📅 חודש השיא שלי: {top_month}
📍 האצטדיון שלי: {top_stadium}

הופק באמצעות "יומן משחקי הכדורגל שלי" 🏆"""
        
        encoded_wa_text = urllib.parse.quote(wa_text)
        wa_link = f"https://api.whatsapp.com/send?text={encoded_wa_text}"
        
        col_dl1, col_dl2, col_dl3 = st.columns([1, 8, 1])
        with col_dl2:
            st.download_button(
                label="⬇️ הורד גיבוי לאקסל",
                data=csv_export,
                file_name="my_football_diary.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.markdown(f"""
            <a href="{wa_link}" target="_blank" style="display: block; background-color: #25D366; color: white !important; padding: 10px 15px; border-radius: 12px; text-decoration: none; font-weight: 900; text-align: center; margin-top: 10px; font-size: 0.95em; box-shadow: 0 4px 6px rgba(37,211,102,0.3);">
                📲 שתף בוואטסאפ
            </a>
            """, unsafe_allow_html=True)
