import streamlit as st
import requests
import pandas as pd
import os
import urllib.parse
from deep_translator import GoogleTranslator
from datetime import datetime
from collections import Counter
import json

API_KEY = "765e650417c14ceb9d6ca6393af2a105"
CSV_FILE = "my_games.csv"
THEME_FILE = "theme.txt"
UPLOAD_DIR = "uploads"

# יצירת תיקייה לתמונות אם היא לא קיימת
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="Football Tracker", layout="wide", page_icon="⚽", initial_sidebar_state="collapsed")

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
        df = pd.DataFrame(columns=["ID_משחק", "תאריך", "תחרות", "מארחת", "תוצאה", "אורחת", "אצטדיון", "לוגו_מארחת", "לוגו_אורחת", "לוגו_תחרות", "הייתי_במשחק", "אירועים_גולש"])
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

# --- התאמה ל-football-data.org ---
@st.cache_data(show_spinner=False)
def search_teams_api(team_name):
    url = f"https://api.football-data.org/v4/teams"
    # ב-football-data חיפוש ישיר מתבצע לעיתים דרך קבוצות או טורנירים, נשתמש בפרמטרים שלהם או נחפש
    # הערה: ב-football-data.org המסלול החינמי כולל תေးות מסוימות. ננסה לשלוף לפי שם או קבוצות
    headers = {"X-Auth-Token": API_KEY}
    try:
        response = requests.get(f"https://api.football-data.org/v4/teams?name={team_name}", headers=headers)
        if response.status_code != 200:
            return "API_ERROR"
        data = response.json()
        results = []
        for team in data.get('teams', []):
            results.append({
                'id': team['id'],
                'name': team['name'],
                'country': team.get('area', {}).get('name', 'לא ידוע'),
                'logo': team.get('crest', '')
            })
        return results
    except Exception:
        return "NETWORK_ERROR"

@st.cache_data(show_spinner=False)
def get_head_to_head_matches(team1_id, team2_id):
    headers = {"X-Auth-Token": API_KEY}
    try:
        response = requests.get(f"https://api.football-data.org/v4/teams/{team1_id}/matches?status=FINISHED", headers=headers)
        if response.status_code != 200:
            return []
        data = response.json()
        matches = data.get('matches', [])
        # סינון משחקים שבהם הקבוצה השנייה היא היריבה
        h2h = [m for m in matches if m['homeTeam']['id'] == team2_id or m['awayTeam']['id'] == team2_id]
        return h2h
    except:
        return []

@st.cache_data(show_spinner=False)
def get_fixture_details(match_id):
    headers = {"X-Auth-Token": API_KEY}
    try:
        response = requests.get(f"https://api.football-data.org/v4/matches/{match_id}", headers=headers)
        return response.json()
    except:
        return {}

def get_stat_num(val):
    if val is None or val == 'None' or val == '': return -1
    if isinstance(val, str) and '%' in val:
        return int(val.replace('%', ''))
    try:
        return int(val)
    except:
        return -1

def match_card_html(date, competition, stadium, home_team, away_team, score, home_logo, away_logo, league_logo, theme_name, attended=False):
    is_lht = (theme_name == "בהיר ☀️")
    tc_inline = "#333333 !important" if is_lht else "white !important"
    
    img_league = f"<img src='{league_logo}' width='20' style='vertical-align: middle; margin-left: 4px; border-radius: 50%;'>" if league_logo else ""
    img_home = f"<img src='{home_logo}' width='35' style='vertical-align: middle; margin-left: 8px;'>" if home_logo else ""
    img_away = f"<img src='{away_logo}' width='35' style='vertical-align: middle; margin-right: 8px;'>" if away_logo else ""
    
    att_tag = "<br><span style='background: linear-gradient(45deg, #28a745, #20c997); color: white !important; padding: 2px 8px; border-radius: 15px; font-size: 0.75em; font-weight: 900; display: inline-block; margin-top: 4px;'>🎟️ באצטדיון</span>" if attended else ""
    
    return f"""
    <div class='match-card'>
        <div style='text-align: center; color: #888 !important; font-size: 0.85em; font-weight: bold; margin-bottom: 10px;'>
            📅 <span style='color: {tc_inline};'>{date}</span> &nbsp;|&nbsp; 🏆 {img_league} {competition} &nbsp;|&nbsp; 🏟️ {stadium} {att_tag}
        </div>
        <div style='text-align: center; font-size: 1.2em; display: flex; align-items: center; justify-content: center; color: {tc_inline}; font-weight: 900; flex-wrap: wrap; gap: 5px;'>
            {img_home} <span>{home_team}</span> 
            <span style='background: linear-gradient(135deg, #007bff, #0056b3); color: white !important; padding: 4px 15px; border-radius: 20px; font-weight: 900; margin: 0 10px; font-size: 0.9em; letter-spacing: 1px;'>{score}</span> 
            <span>{away_team}</span> {img_away}
        </div>
    </div>
    """

def get_colored_marker(text, bg_marker):
    return f"<div style='text-align: center;'><span style='background-color: {bg_marker}; color: white !important; border-radius: 20px; padding: 5px 15px; font-weight: bold; font-size: 0.9em; box-shadow: 0 2px 5px rgba(0,0,0,0.15);'>{text}</span></div><br>"

def render_match_details(match_id, theme_name):
    is_lht = (theme_name == "בהיר ☀️")
    tc = "#333333" if is_lht else "white"
    
    with st.spinner("טוען נתונים..."):
        match_data = get_fixture_details(match_id)
        
    if not match_data or 'match' not in match_data:
        st.error("שגיאה בטעינת הנתונים מהשרת החדש.")
        return

    m = match_data['match']
    home_team = m['homeTeam']['name']
    away_team = m['awayTeam']['name']
    home_logo = m['homeTeam'].get('crest', '')
    away_logo = m['awayTeam'].get('crest', '')
    score_h = m['score']['fullTime']['home']
    score_a = m['score']['fullTime']['away']
    competition = m['competition']['name']
    c_country = m['competition'].get('area', {}).get('name', '')
    
    st.markdown(f"<div style='text-align: center; color: gray !important; font-size: 1em; font-weight: bold;'>{c_country}, {competition}</div><br>", unsafe_allow_html=True)
    
    h1, h2, h3 = st.columns([1, 1, 1])
    with h1:
        st.markdown(f"<div style='text-align: center;'><img src='{home_logo}' width='70'><br><b style='color: {tc} !important;'>{home_team}</b></div>", unsafe_allow_html=True)
    with h2:
        st.markdown(f"<div style='text-align: center;'><h1 style='font-size: 2.8em; margin: 0; color: #007bff !important;'>{score_h} - {score_a}</h1><span style='color: gray !important; font-weight: bold; font-size: 0.8em;'>הסתיים</span></div>", unsafe_allow_html=True)
    with h3:
        st.markdown(f"<div style='text-align: center;'><img src='{away_logo}' width='70'><br><b style='color: {tc} !important;'>{away_team}</b></div>", unsafe_allow_html=True)

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
        with st.container():
            col_search, col_filter = st.columns(2)
            with col_search:
                search_query = st.text_input("חיפוש קבוצה או אצטדיון...", "")
            with col_filter:
                all_comps = list(set([m.get('תחרות', '') for m in st.session_state.saved_matches if m.get('תחרות', '')]))
                selected_comp = st.selectbox("סנן לפי תחרות:", ["כל התחרויות"] + all_comps)
        
        st.write("---")
        filtered_matches = [m for m in st.session_state.saved_matches if search_query.lower() in f"{m.get('מארחת', '')} {m.get('אורחת', '')}".lower()]
        
        for idx, match in enumerate(filtered_matches):
            match_id = match.get('ID_משחק')
            attended = match.get('הייתי_במשחק', False)
            col_match, col_attend, col_del = st.columns([10, 3, 1])
            with col_del:
                if st.button("🗑️", key=f"del_out_{match_id}"):
                    delete_confirmation_dialog(match_id, f"{match.get('מארחת')} נגד {match.get('אורחת')}")
            with col_attend:
                new_attended = st.checkbox("הייתי באצטדיון 🏟️", value=attended, key=f"att_{match_id}")
                if new_attended != attended:
                    update_attendance_in_file(match_id, new_attended)
                    st.rerun()
            with col_match:
                st.markdown(match_card_html(match.get('תאריך'), match.get('תחרות'), match.get('אצטדיון'), match.get('מארחת'), match.get('אורחת'), match.get('תוצאה'), match.get('לוגו_מארחת'), match.get('לוגו_אורחת'), match.get('לוגו_תחרות'), st.session_state.theme, attended), unsafe_allow_html=True)
                with st.expander("📊 הצג אירועים וסטטיסטיקות"):
                    render_match_details(match_id, st.session_state.theme)
    else:
        st.info("היומן שלך ריק.")

# ==========================================
# מסך 2: חיפוש משחקים חדשים
# ==========================================
elif nav_choice == "🔍 חיפוש והוספת משחקים":
    st.markdown("<h3 style='text-align: center; margin-bottom: 20px; font-weight: 900;'>חיפוש משחקים חדשים 🔍</h3>", unsafe_allow_html=True)
    
    col1, col_vs, col2 = st.columns([5, 1, 5])
    with col1:
        team1_name = st.text_input("team1", placeholder="קבוצה ראשונה (באנגלית, למשל Real Madrid)", label_visibility="collapsed")
    with col_vs:
        st.markdown("<div class='vs-badge'>VS</div>", unsafe_allow_html=True)
    with col2:
        team2_name = st.text_input("team2", placeholder="קבוצה שנייה (באנגלית)", label_visibility="collapsed")

    if st.button("🔍 חפש קבוצות במאגר", use_container_width=True, type="primary"):
        if not team1_name or not team2_name:
            st.warning("נא להזין שמות של שתי קבוצות.")
        else:
            with st.spinner("מחפש..."):
                res1 = search_teams_api(team1_name)
                res2 = search_teams_api(team2_name)
                if isinstance(res1, list) and isinstance(res2, list) and res1 and res2:
                    st.session_state.t1_opts = res1
                    st.session_state.t2_opts = res2
                else:
                    st.error("לא נמצאו קבוצות תואמות. וודא שהשמות באנגלית.")

    if st.session_state.t1_opts and st.session_state.t2_opts:
        c1, c2 = st.columns(2)
        with c1:
            t1_sel = st.selectbox("בחר קבוצה 1:", options=st.session_state.t1_opts, format_func=lambda x: f"{x['name']} ({x['country']})")
        with c2:
            t2_sel = st.selectbox("בחר קבוצה 2:", options=st.session_state.t2_opts, format_func=lambda x: f"{x['name']} ({x['country']})")
            
        if st.button("שלב 2: הצג משחקים ביניהן 🚀", type="primary", use_container_width=True):
            with st.spinner("שולף משחקים..."):
                matches = get_head_to_head_matches(t1_sel['id'], t2_sel['id'])
                st.session_state.search_results = matches

    if st.session_state.search_results:
        st.write("---")
        for idx, match in enumerate(st.session_state.search_results[:15]):
            m_id = match['id']
            date = match['utcDate'][:10]
            comp = match['competition']['name']
            comp_logo = match['competition'].get('emblem', '')
            h_team = match['homeTeam']['name']
            a_team = match['awayTeam']['name']
            h_logo = match['homeTeam'].get('crest', '')
            a_logo = match['awayTeam'].get('crest', '')
            score_h = match['score']['fullTime']['home']
            score_a = match['score']['fullTime']['away']
            stadium = match.get('venue', 'אצטדיון לא ידוע')
            
            c_txt, c_btn = st.columns([5, 1])
            with c_txt:
                st.markdown(match_card_html(date, comp, stadium, h_team, a_team, f"{score_h} - {score_a}", h_logo, a_logo, comp_logo, st.session_state.theme), unsafe_allow_html=True)
            with c_btn:
                is_saved = any(str(s.get('ID_משחק')) == str(m_id) for s in st.session_state.saved_matches)
                if is_saved:
                    st.button("✅", key=f"saved_{m_id}_{idx}", disabled=True, use_container_width=True)
                else:
                    if st.button("➕", key=f"add_{m_id}_{idx}", use_container_width=True):
                        match_data = {
                            "ID_משחק": m_id,
                            "תאריך": date,
                            "תחרות": comp,
                            "מארחת": h_team,
                            "תוצאה": f"{score_h} - {score_a}",
                            "אורחת": a_team,
                            "אצטדיון": stadium,
                            "לוגו_מארחת": h_logo,
                            "לוגו_אורחת": a_logo,
                            "לוגו_תחרות": comp_logo,
                            "הייתי_במשחק": False,
                            "אירועים_גולש": json.dumps([], ensure_ascii=False)
                        }
                        save_match_to_file(match_data)
                        st.rerun()

# ==========================================
# מסך 3: סטטיסטיקות אישיות
# ==========================================
elif nav_choice == "📊 סטטיסטיקות אישיות":
    st.markdown("<h3 style='text-align: center; margin-bottom: 25px; font-weight: 900;'>הסטטיסטיקות שלך 📈</h3>", unsafe_allow_html=True)
    saved = st.session_state.saved_matches
    if not saved:
        st.info("יומן המשחקים ריק.")
    else:
        total_matches = len(saved)
        total_goals = sum(int(str(m.get('תוצאה', '0-0')).split('-')[0].strip()) + int(str(m.get('תוצאה', '0-0')).split('-')[1].strip()) for m in saved if '-' in str(m.get('תוצאה', '')))
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div class='stat-card'><div class='stat-title'>משחקים ביומן</div><div class='stat-value'>🏟️ {total_matches}</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='stat-card'><div class='stat-title'>שערים שראית</div><div class='stat-value'>⚽ {total_goals}</div></div>", unsafe_allow_html=True)
