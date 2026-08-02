import streamlit as st
import requests
import pandas as pd
import os
import urllib.parse
from datetime import datetime
from collections import Counter
import json

API_KEY = "123"  # כאן תכניס את המפתח שלך או השאר 123 למפתח בדיקה חינמי
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

#MainMenu {{visibility: hidden;}}
header {{visibility: hidden;}}
footer {{visibility: hidden;}}

[data-testid="stAppViewContainer"] {{
    background-color: {bg_color} !important;
}}

.stMarkdown, .stText, p, label, h1, h2, h3, h4, h5, h6, li {{
    color: {text_color} !important;
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
        df = pd.DataFrame(columns=["ID_משחק", "תאריך", "תחרות", "מארחת", "תוצאה", "אורחת", "אצטדיון", "לוגו_מארחת", "לוגו_אורחת", "הייתי_במשחק"])
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

# --- חיפוש קבוצות מול TheSportsDB ---
@st.cache_data(show_spinner=False)
def search_teams_api(team_name):
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/searchteams.php"
    querystring = {"t": team_name}
    try:
        response = requests.get(url, params=querystring)
        data = response.json()
        results = []
        if data and data.get('teams'):
            for team in data['teams']:
                # נסנן רק לקבוצות כדורגל (Soccer)
                if team.get('strSport') == 'Soccer':
                    results.append({
                        'id': team['idTeam'],
                        'name': team['strTeam'],
                        'country': team.get('strCountry', 'לא ידוע'),
                        'logo': team.get('strBadge', '')
                    })
        return results
    except Exception:
        return []

# --- שליפת משחקים אחרונים של קבוצה מול TheSportsDB ---
@st.cache_data(show_spinner=False)
def get_team_last_events(team_id):
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventslast.php"
    querystring = {"id": team_id}
    try:
        response = requests.get(url, params=querystring)
        data = response.json()
        if data and data.get('results'):
            return data['results']
        return []
    except:
        return []

def match_card_html(date, competition, stadium, home_team, away_team, score, home_logo, away_logo, theme_name, attended=False):
    is_lht = (theme_name == "בהיר ☀️")
    tc_inline = "#333333 !important" if is_lht else "white !important"
    
    img_home = f"<img src='{home_logo}' width='35' style='vertical-align: middle; margin-left: 8px;'>" if home_logo else ""
    img_away = f"<img src='{away_logo}' width='35' style='vertical-align: middle; margin-right: 8px;'>" if away_logo else ""
    att_tag = "<br><span style='background: linear-gradient(45deg, #28a745, #20c997); color: white !important; padding: 2px 8px; border-radius: 15px; font-size: 0.75em; font-weight: 900; display: inline-block; margin-top: 4px;'>🎟️ באצטדיון</span>" if attended else ""
    
    return f"""
    <div class='match-card'>
        <div style='text-align: center; color: #888 !important; font-size: 0.85em; font-weight: bold; margin-bottom: 10px;'>
            📅 <span style='color: {tc_inline};'>{date}</span> &nbsp;|&nbsp; 🏆 {competition} &nbsp;|&nbsp; 🏟️ {stadium} {att_tag}
        </div>
        <div style='text-align: center; font-size: 1.2em; display: flex; align-items: center; justify-content: center; color: {tc_inline}; font-weight: 900; flex-wrap: wrap; gap: 5px;'>
            {img_home} <span>{home_team}</span> 
            <span style='background: linear-gradient(135deg, #007bff, #0056b3); color: white !important; padding: 4px 15px; border-radius: 20px; font-weight: 900; margin: 0 10px; font-size: 0.9em; letter-spacing: 1px;'>{score}</span> 
            <span>{away_team}</span> {img_away}
        </div>
    </div>
    """

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
            home_logo = match.get('לוגו_מארחת', '')
            away_logo = match.get('לוגו_אורחת', '')
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
                st.markdown(match_card_html(date, competition, stadium, home_team, away_team, score, home_logo, away_logo, st.session_state.theme, attended), unsafe_allow_html=True)
                
                with st.expander("📸 זיכרון מהיציע ותמונות"):
                    img_path = os.path.join(UPLOAD_DIR, f"{match_id}.png")
                    if os.path.exists(img_path):
                        c_img1, c_img2, c_img3 = st.columns([1, 2, 1])
                        with c_img2:
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
        st.info("היומן שלך ריק. עבור למסך החיפוש כדי להתחיל!")

# ==========================================
# מסך 2: חיפוש והוספת משחקים
# ==========================================
elif nav_choice == "🔍 חיפוש והוספת משחקים":
    st.markdown("<h3 style='text-align: center; margin-bottom: 20px; font-weight: 900; font-size: 1.5em;'>חיפוש קבוצה ומשחקים 🔍</h3>", unsafe_allow_html=True)
    
    team_search = st.text_input("הקלד שם קבוצה באנגלית (למשל: Arsenal, Real Madrid):")
    if st.button("חפש קבוצה", type="primary", use_container_width=True):
        if not team_search.strip():
            st.warning("נא להקליד שם קבוצה.")
        else:
            with st.spinner("מחפש קבוצה..."):
                results = search_teams_api(team_search.strip())
                if results:
                    st.session_state.t1_opts = results
                    st.session_state.search_results = []
                else:
                    st.warning("לא נמצאו קבוצות תואמות.")
                    st.session_state.t1_opts = []

    if st.session_state.t1_opts:
        selected_team = st.selectbox(
            "בחר קבוצה מהתוצאות:", 
            options=st.session_state.t1_opts, 
            format_func=lambda x: f"{x['name']} ({x['country']})"
        )
        
        if st.button("הצג משחקים אחרונים של הקבוצה 🚀", type="primary", use_container_width=True):
            with st.spinner("שולף משחקים..."):
                events = get_team_last_events(selected_team['id'])
                if events:
                    st.session_state.search_results = events
                else:
                    st.warning("לא נמצאו משחקים אחרונים זמינים לקבוצה זו.")
                    st.session_state.search_results = []

    if len(st.session_state.search_results) > 0:
        st.write("---")
        st.markdown("<h4 style='text-align: center;'>משחקים אחרונים שנמצאו:</h4>", unsafe_allow_html=True)
        for idx, match in enumerate(st.session_state.search_results):
            match_id = match.get('idEvent')
            date = match.get('dateEvent', '')
            comp = match.get('strLeague', 'ליגה לא ידועה')
            h_team = match.get('strHomeTeam', '')
            a_team = match.get('strAwayTeam', '')
            score_h = match.get('intHomeScore', '0')
            score_a = match.get('intAwayScore', '0')
            stadium = match.get('strVenue', 'אצטדיון לא ידוע')
            h_logo = match.get('strHomeBadge', '')
            a_logo = match.get('strAwayBadge', '')
            
            col_text, col_btn = st.columns([5, 1])
            with col_text:
                st.markdown(match_card_html(date, comp, stadium, h_team, a_team, f"{score_h} - {score_a}", h_logo, a_logo, st.session_state.theme), unsafe_allow_html=True)
            with col_btn:
                st.write("")
                st.write("")
                is_saved = any(str(saved.get('ID_משחק')) == str(match_id) for saved in st.session_state.saved_matches)
                if is_saved:
                    st.button("✅", key=f"saved_{match_id}_{idx}", disabled=True, use_container_width=True)
                else:
                    if st.button("➕", key=f"add_{match_id}_{idx}", use_container_width=True):
                        match_data = {
                            "ID_משחק": match_id,
                            "תאריך": date,
                            "תחרות": comp,
                            "מארחת": h_team,
                            "תוצאה": f"{score_h} - {score_a}",
                            "אורחת": a_team,
                            "אצטדיון": stadium,
                            "לוגו_מארחת": h_logo,
                            "לוגו_אורחת": a_logo,
                            "הייתי_במשחק": False
                        }
                        save_match_to_file(match_data)
                        st.success("נוסף בהצלחה!")
                        st.rerun()

# ==========================================
# מסך 3: סטטיסטיקות אישיות
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
            if stadium and stadium != 'אצטדיון לא ידוע': stadiums_counter[stadium] += 1
            
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
            st.markdown(f"<div class='stat-card'><div class='stat-title'>קבוצה מובילה</div><div class='stat-value' style='font-size: 1.3em; margin-top: 10px;'>🛡️ {top_team}</div></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='stat-card'><div class='stat-title'>משחקי יציע</div><div class='stat-value' style='font-size: 1.6em; color: #ffc107 !important;'>🎟️ {total_attended}</div></div>", unsafe_allow_html=True)

        col5, col6 = st.columns(2)
        with col5:
            st.markdown(f"<div class='stat-card'><div class='stat-title'>חודש שיא בצפייה</div><div class='stat-value' style='font-size: 1.3em;'>📅 {top_month}</div></div>", unsafe_allow_html=True)
        with col6:
            st.markdown(f"<div class='stat-card'><div class='stat-title'>אצטדיון מוביל</div><div class='stat-value' style='font-size: 1.3em;'>🏟️ {top_stadium}</div></div>", unsafe_allow_html=True)

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
