import streamlit as st
import requests
import pandas as pd
import os
import urllib.parse
from deep_translator import GoogleTranslator
from datetime import datetime
from collections import Counter
import json

# --- הגדרות ה-API (TheStatsAPI) ---
API_KEY = "fapi_WDeKpURK3YzNbWBySpgzu9MEtFvkP36M"
BASE_URL = "https://www.thestatsapi.com/api/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

CSV_FILE = "my_games.csv"
THEME_FILE = "theme.txt"
UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)
st.set_page_config(page_title="Football Tracker", layout="wide", page_icon="⚽", initial_sidebar_state="collapsed")

if 'api_call_count' not in st.session_state: st.session_state.api_call_count = 0
def increment_api_call(): st.session_state.api_call_count += 1

def load_theme():
    if os.path.exists(THEME_FILE):
        with open(THEME_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "כהה 🌙"

def save_theme(theme_choice):
    with open(THEME_FILE, "w", encoding="utf-8") as f: f.write(theme_choice)

def change_theme():
    save_theme(st.session_state.theme_radio)
    st.session_state.theme = st.session_state.theme_radio

if 'theme' not in st.session_state: st.session_state.theme = load_theme()
if 'saved_matches' not in st.session_state: st.session_state.saved_matches = []
if 'search_results' not in st.session_state: st.session_state.search_results = []
if 't1_opts' not in st.session_state: st.session_state.t1_opts = []
if 't2_opts' not in st.session_state: st.session_state.t2_opts = []

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
html, body, [data-testid="stAppViewContainer"] {{ overflow-x: hidden !important; max-width: 100vw !important; background-color: {bg_color} !important; }}
html, body, div, p, label, h1, h2, h3, h4, h5, h6, li, button, input, span {{ font-family: 'Heebo', sans-serif; color: {text_color} !important; }}
#MainMenu, header, footer {{ visibility: hidden; }}
div.row-widget.stRadio > div {{ flex-direction: row; justify-content: center; background-color: {radio_bg}; padding: 6px; border-radius: 30px; gap: 5px; }}
div.row-widget.stRadio > div > label {{ background-color: transparent !important; padding: 8px 18px !important; border-radius: 22px !important; cursor: pointer; font-weight: 700; }}
div.row-widget.stRadio > div > label[data-checked="true"] {{ background-color: {'#ffffff' if is_light else '#3a3f50'} !important; }}
.stat-card, .match-card {{ background: {card_bg}; border-radius: 16px; box-shadow: {shadow_base}; border: {card_border}; padding: 15px; margin-bottom: 12px; width: 100%; box-sizing: border-box; }}
.stat-card {{ text-align: center; padding: 20px 15px; }}
.stat-value {{ font-size: 2.2em; font-weight: 900; margin: 8px 0; color: #007bff !important; }}
.stat-title {{ font-size: 1em; color: {'#7f8c8d' if is_light else '#adb5bd'} !important; font-weight: 700; text-transform: uppercase; }}
.stButton > button {{ border-radius: 12px !important; font-weight: bold !important; width: 100% !important; }}
</style>
""", unsafe_allow_html=True)

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
    if 'הייתי_במשחק' not in match_data: match_data['הייתי_במשחק'] = False
    current_data.insert(0, match_data)
    df = pd.DataFrame(current_data)
    if not df.empty and 'תאריך' in df.columns:
        df = df.sort_values(by='תאריך', ascending=False)
    df.to_csv(CSV_FILE, index=False)
    st.session_state.saved_matches = df.to_dict('records')

def delete_match_from_file(match_id):
    current_data = [m for m in load_saved_matches() if str(m.get('ID_משחק')) != str(match_id)]
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
            delete_match_from_file(match_id); st.rerun()
    with col2:
        if st.button("ביטול", use_container_width=True): st.rerun()

@st.cache_data(show_spinner=False)
def search_teams_api(team_name):
    increment_api_call()
    url = f"{BASE_URL}/teams"
    try:
        response = requests.get(url, headers=HEADERS, params={"search": team_name})
        data = response.json()
        if isinstance(data, list): return data
        if isinstance(data, dict):
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

if st.session_state.api_call_count >= 90:
    st.error(f"⚠️ **התראה קריטית!** הגעת ל-{st.session_state.api_call_count} קריאות API בסשן הנוכחי.")
else:
    st.sidebar.markdown(f"📊 **קריאות API בסשן:** {st.session_state.api_call_count}")

col_empty, col_theme = st.columns([9, 1])
with col_theme:
    st.radio("עיצוב:", ["כהה 🌙", "בהיר ☀️"], index=0 if st.session_state.theme == "כהה 🌙" else 1, horizontal=True, label_visibility="collapsed", key="theme_radio", on_change=change_theme)

st.markdown("""
<div class="app-logo-wrapper" style="display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 35px; margin-top: 10px; direction: rtl;">
    <div style="width: 65px; height: 65px; background: linear-gradient(135deg, #007bff, #00d2ff); border-radius: 18px; display: flex; align-items: center; justify-content: center; font-size: 2.5em; box-shadow: 0 8px 20px rgba(0,123,255,0.4); transform: rotate(-10deg);">⚽</div>
    <div style="display: flex; flex-direction: column; text-align: right;">
        <div style="font-size: 2.5em; font-weight: 900; line-height: 1;">יומן המשחקים</div>
        <div style="font-size: 1.1em; font-weight: 700; color: #007bff; letter-spacing: 2px; text-transform: uppercase; margin-top: 4px;">הכדורגל שלי</div>
    </div>
</div>
""", unsafe_allow_html=True)

nav_choice = st.radio("ניווט", ["📋 יומן המשחקים", "🔍 חיפוש והוספת משחקים", "➕ הוספה ידנית", "📊 סטטיסטיקות אישיות"], index=1, horizontal=True, label_visibility="collapsed")
st.write("---")

if nav_choice != "🔍 חיפוש והוספת משחקים":
    st.session_state.t1_opts = []
    st.session_state.t2_opts = []
    st.session_state.search_results = []

# ==========================================
# מסך 1: יומן המשחקים
# ==========================================
if nav_choice == "📋 יומן המשחקים":
    if len(st.session_state.saved_matches) > 0:
        with st.container():
            col_search, col_filter = st.columns(2)
            with col_search: search_query = st.text_input("חיפוש קבוצה או אצטדיון...", "")
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
                            if st.button("🗑️ מחק תמונה", key=f"del_img_{match_id}"): os.remove(img_path); st.rerun()
                    else:
                        up_file = st.file_uploader("העלה תמונה מהמשחק", type=["png", "jpg", "jpeg"], key=f"up_{match_id}")
                        if up_file:
                            with open(img_path, "wb") as f: f.write(up_file.getbuffer())
                            st.rerun()
            st.write("")
    else:
        st.info("היומן שלך ריק.")

# ==========================================
# מסך 2: חיפוש משחקים אוטומטי
# ==========================================
elif nav_choice == "🔍 חיפוש והוספת משחקים":
    st.markdown("<h3 style='text-align: center; margin-bottom: 20px; font-weight: 900; font-size: 1.5em;'>חיפוש משחקים 🔍</h3>", unsafe_allow_html=True)
    
    col1, col_vs, col2 = st.columns([5, 1, 5])
    with col1: t1_input = st.text_input("קבוצה 1", placeholder="למשל: Real Madrid", label_visibility="collapsed")
    with col_vs: st.markdown("<div class='vs-badge' style='text-align: center; margin-top: 5px; font-size: 1.5em; font-weight: 900;'>VS</div>", unsafe_allow_html=True)
    with col2: t2_input = st.text_input("קבוצה 2", placeholder="למשל: Barcelona", label_visibility="collapsed")

    if st.button("חפש קבוצות", type="primary", use_container_width=True):
        if t1_input.strip() and t2_input.strip():
            with st.spinner("מחפש קבוצות במאגר..."):
                try:
                    t1_en = GoogleTranslator(source='auto', target='en').translate(t1_input.strip())
                    t2_en = GoogleTranslator(source='auto', target='en').translate(t2_input.strip())
                except:
                    t1_en, t2_en = t1_input.strip(), t2_input.strip()

                res1 = search_teams_api(t1_en)
                res2 = search_teams_api(t2_en)
                if res1 or res2:
                    st.session_state.t1_opts = res1 if res1 else [{'id': t1_en, 'name': t1_input}]
                    st.session_state.t2_opts = res2 if res2 else [{'id': t2_en, 'name': t2_input}]
                else:
                    st.warning("לא נמצאו תוצאות מדויקות, מציג את השמות שהוזנו ישירות.")
                    st.session_state.t1_opts = [{'id': t1_en, 'name': t1_input}]
                    st.session_state.t2_opts = [{'id': t2_en, 'name': t2_input}]
        else:
            st.warning("נא להזין שמות של שתי קבוצות.")

    if st.session_state.t1_opts and st.session_state.t2_opts:
        c1, c2 = st.columns(2)
        with c1: t1_sel = st.selectbox("בחר קבוצה 1:", options=st.session_state.t1_opts, format_func=lambda x: x.get('name', str(x)))
        with c2: t2_sel = st.selectbox("בחר קבוצה 2:", options=st.session_state.t2_opts, format_func=lambda x: x.get('name', str(x)))
            
        if st.button("הצג משחקים ביניהן 🚀", type="primary", use_container_width=True):
            with st.spinner("שולף משחקים..."):
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
                    st.warning("שגיאה בשליפת המשחקים.")

    if st.session_state.search_results:
        st.write("---")
        for m in st.session_state.search_results:
            m_id = m.get('id', f"match_{datetime.now().timestamp()}")
            date = str(m.get('date', '2026-01-01'))[:10]
            comp = m.get('competition', {}).get('name', 'ליגה') if isinstance(m.get('competition'), dict) else 'ליגה'
            stadium = m.get('venue', 'אצטדיון')
            home_team = m.get('homeTeam', {}).get('name', 'בית') if isinstance(m.get('homeTeam'), dict) else 'בית'
            away_team = m.get('awayTeam', {}).get('name', 'חוץ') if isinstance(m.get('awayTeam'), dict) else 'חוץ'
            score = f"{m.get('homeScore', 0)} - {m.get('awayScore', 0)}"

            col_t, col_b = st.columns([5, 1])
            with col_t:
                st.markdown(match_card_html(date, comp, stadium, home_team, away_team, score, st.session_state.theme), unsafe_allow_html=True)
            with col_b:
                st.write(""); st.write("")
                if st.button("➕", key=f"add_{m_id}"):
                    save_match_to_file({
                        "ID_משחק": m_id, "תאריך": date, "תחרות": comp,
                        "מארחת": home_team, "תוצאה": score, "אורחת": away_team,
                        "אצטדיון": stadium, "הייתי_במשחק": False
                    })
                    st.success("נוסף בהצלחה!")
                    st.rerun()

# ==========================================
# מסך 3: הוספה ידנית
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
        
        col1, col2 = st.columns(2)
        with col1: st.markdown(f"<div class='stat-card'><div class='stat-title'>משחקים</div><div class='stat-value'>{total_matches}</div></div>", unsafe_allow_html=True)
        with col2: st.markdown(f"<div class='stat-card'><div class='stat-title'>שערים</div><div class='stat-value'>{total_goals}</div></div>", unsafe_allow_html=True)
