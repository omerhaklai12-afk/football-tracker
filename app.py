import streamlit as st
import requests
import pandas as pd
import os
import urllib.parse
from deep_translator import GoogleTranslator
from datetime import datetime
from collections import Counter

API_KEY = "7b8cd7941e0c008eb154b4ca358d3e72"
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

# --- בניית ה-CSS שמונע שבירת עמודות וכופה הצגה מימין לשמאל ---
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
}}

/* כפייה מוחלטת על עמודות להישאר בשורה אחת גם במסכי מובייל קטנים */
[data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 4px !important;
}}

[data-testid="column"] {{
    flex: 1 1 auto !important;
    min-width: 0 !important;
}}

/* החלת הפונט על כל הטקסטים */
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

/* העלמת הטקסט והאייקונים המובנים מאחורי האקורדיון */
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

/* עיצוב הלוגו */
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

/* עיצוב כפתורי ניווט בסגנון מודרני */
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

/* עיצובים מיוחדים לאזור החיפוש */
.vs-badge {{
    text-align: center;
    margin-top: 5px;
    font-size: 1.5em;
    font-weight: 900;
    color: {'#adb5bd' if is_light else '#6c757d'};
}}

/* כרטיסיות משחק מוקטנות ומותאמות להצגה לצד הכפתורים */
.stat-card, .match-card {{
    background: {card_bg};
    border-radius: 12px;
    color: {text_color} !important;
    box-shadow: {shadow_base};
    border: {card_border};
    padding: 10px;
    margin-bottom: 8px;
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

/* כפתורים משודרגים */
.stButton > button {{
    border-radius: 10px !important;
    font-weight: bold !important;
    width: 100% !important;
    min-height: 38px !important;
    font-size: 0.85em !important;
}}
</style>
""", unsafe_allow_html=True)


# --- פונקציות לניהול קובץ השמירה של היומן ---
def load_saved_matches():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE).fillna('').to_dict('records')
    return []

if not st.session_state.saved_matches:
    st.session_state.saved_matches = load_saved_matches()

def save_match_to_file(match_data):
    current_data = load_saved_matches()
    if 'הייתי_במשחק' not in match_data:
        match_data['הייתי_במשחק'] = False
        
    current_data.insert(0, match_data)
    df = pd.DataFrame(current_data)
    df.to_csv(CSV_FILE, index=False)
    st.session_state.saved_matches = current_data

def delete_match_from_file(match_id):
    current_data = load_saved_matches()
    current_data = [m for m in current_data if str(m.get('ID_משחק')) != str(match_id)]
    
    df = pd.DataFrame(current_data)
    if df.empty:
        df = pd.DataFrame(columns=["ID_משחק", "תאריך", "תחרות", "מארחת", "תוצאה", "אורחת", "אצטדיון", "לוגו_מארחת", "לוגו_אורחת", "לוגו_תחרות", "הייתי_במשחק"])
    df.to_csv(CSV_FILE, index=False)
    st.session_state.saved_matches = current_data
    
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
    df.to_csv(CSV_FILE, index=False)
    st.session_state.saved_matches = current_data

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
def get_fixture_details(match_id):
    url = "https://v3.football.api-sports.io/fixtures"
    querystring = {"id": match_id}
    headers = {"x-apisports-key": API_KEY}
    response = requests.get(url, headers=headers, params=querystring)
    return response.json()

def get_stat_num(val):
    if val is None or val == 'None' or val == '': return -1
    if isinstance(val, str) and '%' in val:
        return int(val.replace('%', ''))
    try:
        return int(val)
    except:
        return -1

def search_teams_api(team_name):
    url = "https://v3.football.api-sports.io/teams"
    querystring = {"search": team_name}
    headers = {"x-apisports-key": API_KEY}
    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        
        if data.get('errors'):
            errors = data['errors']
            if isinstance(errors, dict) and len(errors) > 0:
                if 'requests' in errors: return "DAILY_LIMIT"
                elif 'rateLimit' in errors: return "RATE_LIMIT"
                elif 'token' in errors: return "INVALID_KEY"
            return "API_ERROR"
            
        results = []
        if data.get('results', 0) > 0:
            for item in data['response']:
                team = item['team']
                results.append({
                    'id': team['id'],
                    'name': team['name'],
                    'country': team.get('country', 'לא ידוע'),
                    'logo': team['logo']
                })
        return results
    except Exception:
        return "NETWORK_ERROR"

def match_card_html(date, competition, stadium, home_team, away_team, score, home_logo, away_logo, league_logo, theme_name, attended=False):
    is_lht = (theme_name == "בהיר ☀️")
    tc_inline = "#333333 !important" if is_lht else "white !important"
    
    img_league = f"<img src='{league_logo}' width='14' style='vertical-align: middle; margin-left: 3px; border-radius: 50%;'>" if league_logo else ""
    img_home = f"<img src='{home_logo}' width='22' style='vertical-align: middle; margin-left: 4px; flex-shrink: 0;'>" if home_logo else ""
    img_away = f"<img src='{away_logo}' width='22' style='vertical-align: middle; margin-right: 4px; flex-shrink: 0;'>" if away_logo else ""
    
    att_tag = "<span style='background: #28a745; color: white !important; padding: 1px 5px; border-radius: 8px; font-size: 0.65em; font-weight: bold; margin-right: 4px;'>🎟️ באצטדיון</span>" if attended else ""
    
    return f"""
    <div class='match-card'>
        <div style='text-align: center; color: #888 !important; font-size: 0.75em; font-weight: bold; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>
            📅 <span style='color: {tc_inline};'>{date}</span> | 🏆 {img_league} {competition} | 🏟️ {stadium} {att_tag}
        </div>
        <div style='text-align: center; font-size: 0.95em; display: flex; align-items: center; justify-content: center; color: {tc_inline}; font-weight: 900; flex-wrap: nowrap; gap: 4px;'>
            {img_home} <span style='white-space: nowrap;'>{home_team}</span> 
            <span style='background: #007bff; color: white !important; padding: 2px 8px; border-radius: 12px; font-weight: 900; margin: 0 4px; font-size: 0.8em; letter-spacing: 1px; flex-shrink: 0;'>{score}</span> 
            <span style='white-space: nowrap;'>{away_team}</span> {img_away}
        </div>
    </div>
    """

def get_colored_marker(text, bg_marker):
    return f"<div style='text-align: center;'><span style='background-color: {bg_marker}; color: white !important; border-radius: 20px; padding: 5px 15px; font-weight: bold; font-size: 0.9em; box-shadow: 0 2px 5px rgba(0,0,0,0.15);'>{text}</span></div><br>"

def render_match_details(match_id, theme_name):
    is_lht = (theme_name == "בהיר ☀️")
    tc = "#333333" if is_lht else "white"
    bg_info = "#f8f9fa" if is_lht else "rgba(255,255,255,0.05)"
    
    with st.spinner("טוען נתונים..."):
        details_data = get_fixture_details(match_id)
        
    if not details_data or details_data.get('results', 0) == 0:
        st.error("שגיאה בטעינת הנתונים: ייתכן שהגעת למגבלת הקריאות של השרת.")
        return

    full_match = details_data['response'][0]
    events = full_match.get('events', [])
    
    for i, ev in enumerate(events):
        ev['original_index'] = i
    
    home_id = full_match['teams']['home']['id']
    away_id = full_match['teams']['away']['id']
    home_has_red = any(ev['type'] == 'Card' and 'Red' in ev['detail'] and ev['team']['id'] == home_id for ev in events)
    away_has_red = any(ev['type'] == 'Card' and 'Red' in ev['detail'] and ev['team']['id'] == away_id for ev in events)
    
    home_rc_badge = "<span style='font-size: 0.5em; vertical-align: middle; margin-left: 5px;'>🟥</span>" if home_has_red else ""
    away_rc_badge = "<span style='font-size: 0.5em; vertical-align: middle; margin-right: 5px;'>🟥</span>" if away_has_red else ""
    
    c_country = full_match['league']['country']
    c_league = full_match['league']['name']
    c_round = full_match['league'].get('round', '')
    
    round_html = f"<div style='text-align: center; color: #007bff !important; font-size: 0.9em; font-weight: 700; margin-top: -3px;'>{c_round}</div>" if c_round else ""
    st.markdown(f"<div style='text-align: center; color: gray !important; font-size: 1em; font-weight: bold;'>{c_country}, {c_league}</div>{round_html}<br>", unsafe_allow_html=True)
    
    h1, h2, h3 = st.columns([1, 1, 1])
    with h1:
        st.markdown(f"<div style='text-align: center;'><img src='{full_match['teams']['home']['logo']}' width='70' style='filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));'><br><b style='font-size: 1.1em; color: {tc} !important;'>{full_match['teams']['home']['name']}</b></div>", unsafe_allow_html=True)
    with h2:
        score_display = f"{home_rc_badge}{full_match['goals']['home']} - {full_match['goals']['away']}{away_rc_badge}"
        st.markdown(f"<div style='text-align: center;'><h1 style='font-size: 2.8em; margin: 0; color: #007bff !important;'>{score_display}</h1><span style='color: gray !important; font-weight: bold; font-size: 0.8em; text-transform: uppercase;'>הסתיים</span></div>", unsafe_allow_html=True)
    with h3:
        st.markdown(f"<div style='text-align: center;'><img src='{full_match['teams']['away']['logo']}' width='70' style='filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));'><br><b style='font-size: 1.1em; color: {tc} !important;'>{full_match['teams']['away']['name']}</b></div>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown("<h4 style='text-align: center; margin-bottom: 20px; color: gray !important; font-weight: 900;'>אירועי המשחק</h4>", unsafe_allow_html=True)
    
    important_events = [
        ev for ev in events 
        if ev['type'] == 'Goal' 
        or ev['type'] == 'Penalty' 
        or (ev['type'] == 'Card' and 'Red' in str(ev.get('detail', '')))
        or ('Miss' in str(ev.get('detail', '')))
    ]
    
    shootout, extra_time, second_half, first_half = [], [], [], []
    status_short = full_match['fixture']['status']['short']
    
    important_events = sorted(important_events, key=lambda x: (x['time']['elapsed'], x['time']['extra'] or 0, x['original_index']), reverse=True)
    
    for ev in important_events:
        time_el = ev['time']['elapsed']
        comments = str(ev.get('comments') or '')
        
        if 'Penalty Shootout' in comments:
            shootout.append(ev)
        elif status_short == 'PEN' and time_el == 120 and len(extra_time) == 0 and len(second_half) == 0 and (ev['type'] == 'Goal' or ev['type'] == 'Penalty') and ('Penalty' in ev.get('detail', '') or 'Miss' in ev.get('detail', '')):
            shootout.append(ev)
        elif time_el > 90:
            extra_time.append(ev)
        elif time_el > 45:
            second_half.append(ev)
        else:
            first_half.append(ev)
            
    ht_h = full_match['score']['halftime']['home']
    ht_a = full_match['score']['halftime']['away']
    ft_h = full_match['score']['fulltime']['home']
    ft_a = full_match['score']['fulltime']['away']
    if ft_h is None: ft_h = full_match['goals']['home']
    if ft_a is None: ft_a = full_match['goals']['away']
    et_goals_h = full_match['goals']['home']
    et_goals_a = full_match['goals']['away']
    pen_h = full_match['score']['penalty']['home']
    pen_a = full_match['score']['penalty']['away']

    ht_str = get_colored_marker(f"מחצית {ht_h} - {ht_a}" if ht_h is not None else "מחצית", "#17a2b8")
    ft_str = get_colored_marker(f"סוף 90 דקות {ft_h} - {ft_a}" if ft_h is not None else "סוף 90 דקות", "#28a745")
    et_str = get_colored_marker(f"סוף 120 דקות {et_goals_h} - {et_goals_a}" if et_goals_h is not None else "סוף 120 דקות", "#fd7e14")
    pen_str = get_colored_marker(f"פנדלים {pen_h} - {pen_a}" if pen_h is not None else "פנדלים", "#dc3545")

    def draw_events(ev_list):
        for ev in ev_list:
            time_el = ev['time']['elapsed']
            time_ex = ev['time']['extra']
            if time_ex:
                time_display = f"<span style='background-color: rgba(253, 126, 20, 0.15); color: #e67e22 !important; padding: 2px 6px; border-radius: 6px; font-size: 0.9em;'>{time_el}+{time_ex}'</span>"
            else:
                time_display = f"<span style='color: {tc} !important; font-weight: bold;'>{time_el}'</span>"
            
            team_id = ev['team']['id']
            player = ev['player']['name']
            assist = ev['assist']['name'] if ev['assist']['name'] else ""
            ev_type = ev['type']
            ev_detail = str(ev.get('detail', ''))
            
            if ev_type == "Goal" or ev_type == "Penalty" or "Miss" in ev_detail:
                if ev_detail == "Penalty":
                    icon = "<span style='display:inline-block; background-color: #28a745; border-radius: 50%; padding: 2px 4px; color: white !important; font-size: 0.8em;'><b>P✅</b></span>"
                elif "Miss" in ev_detail:
                    icon = "<span style='display:inline-block; background-color: #dc3545; border-radius: 50%; width: 20px; height: 20px; line-height: 20px; color: white !important; font-size: 0.8em; text-align: center; margin: 0 2px;'><b>P</b></span><span style='font-size: 0.7em;'>❌</span>"
                elif ev_detail == "Own Goal":
                    icon = "🔴⚽"
                else:
                    icon = "⚽"
            else:
                icon = "🟥"
                
            is_home = (team_id == home_id)
            
            e1, e2, e3 = st.columns([3, 1, 3])
            if is_home:
                with e1:
                    assist_text = f"<br><small style='color: gray !important; font-size: 0.85em;'>{assist}</small>" if assist and ev_type == 'Goal' else ""
                    st.markdown(f"<div style='text-align: left; line-height: 1.2; color: {tc} !important; font-size: 0.95em;'><b>{player}</b> {icon}{assist_text}</div>", unsafe_allow_html=True)
                with e2:
                    st.markdown(f"<div style='text-align: center;'>{time_display}</div>", unsafe_allow_html=True)
            else:
                with e2:
                    st.markdown(f"<div style='text-align: center;'>{time_display}</div>", unsafe_allow_html=True)
                with e3:
                    assist_text = f"<br><small style='color: gray !important; font-size: 0.85em;'>{assist}</small>" if assist and ev_type == 'Goal' else ""
                    st.markdown(f"<div style='text-align: right; line-height: 1.2; color: {tc} !important; font-size: 0.95em;'>{icon} <b>{player}</b>{assist_text}</div>", unsafe_allow_html=True)

    if status_short == 'PEN':
        st.markdown(pen_str, unsafe_allow_html=True)

    if status_short in ['AET', 'PEN']:
        st.markdown(et_str, unsafe_allow_html=True)
        draw_events(extra_time)
        st.write("")

    st.markdown(ft_str, unsafe_allow_html=True)
    draw_events(second_half)
    st.write("")

    st.markdown(ht_str, unsafe_allow_html=True)
    draw_events(first_half)

    st.divider()
    st.markdown("<h3 style='text-align: center; margin-bottom: 15px; color: gray !important; font-weight: 900;'>סטטיסטיקות</h3>", unsafe_allow_html=True)
    stats = full_match.get('statistics', [])
    if len(stats) == 2:
        home_stats = {s['type']: s['value'] for s in stats[0]['statistics']}
        away_stats = {s['type']: s['value'] for s in stats[1]['statistics']}
        
        stat_types = {
            "Ball Possession": "החזקת כדור",
            "Total Shots": "בעיטות לשער",
            "Shots on Goal": "בעיטות למסגרת"
        }
        
        for en_type, he_type in stat_types.items():
            h_val = home_stats.get(en_type, '0')
            a_val = away_stats.get(en_type, '0')
            h_str = str(h_val) if h_val is not None else '0'
            a_str = str(a_val) if a_val is not None else '0'
            
            h_num = get_stat_num(h_str)
            a_num = get_stat_num(a_str)
            
            win_h_style = "background: linear-gradient(135deg, #007bff, #00d2ff); padding: 4px 15px; border-radius: 12px; color: white !important; font-weight: 900; font-size: 0.9em;"
            win_a_style = "background: linear-gradient(135deg, #28a745, #20c997); padding: 4px 15px; border-radius: 12px; color: white !important; font-weight: 900; font-size: 0.9em;"
            neutral_style = "padding: 4px 15px; color: gray !important; font-weight: bold; background-color: rgba(128,128,128,0.1); border-radius: 12px; font-size: 0.9em;"
            
            if h_num > a_num:
                final_h, final_a = win_h_style, neutral_style
            elif a_num > h_num:
                final_h, final_a = neutral_style, win_a_style
            else:
                final_h, final_a = neutral_style, neutral_style
            
            s1, s2, s3 = st.columns([1, 2, 1])
            with s1: 
                st.markdown(f"<div style='text-align: center;'><span style='{final_h}'>{h_str}</span></div>", unsafe_allow_html=True)
            with s2: 
                st.markdown(f"<div style='text-align: center; color: gray !important; font-weight: bold; font-size: 0.9em;'>{he_type}</div>", unsafe_allow_html=True)
            with s3: 
                st.markdown(f"<div style='text-align: center;'><span style='{final_a}'>{a_str}</span></div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 10px 0; border: 0; border-top: 1px solid rgba(128,128,128,0.2);'>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align: center; color: gray !important;'>אין סטטיסטיקות זמינות למשחק זה.</div>", unsafe_allow_html=True)
        
    st.divider()
    st.markdown("<h4 style='text-align: center; margin-bottom: 15px; color: gray !important; font-weight: 900;'>מידע על המשחק</h4>", unsafe_allow_html=True)
    match_date_str = full_match['fixture']['date']
    try:
        dt = datetime.strptime(match_date_str, "%Y-%m-%dT%H:%M:%S%z")
        formatted_date = dt.strftime("%d/%m/%Y")
    except:
        formatted_date = match_date_str[:10]
        
    stadium = full_match['fixture']['venue']['name']
    c_league_logo = full_match['league']['logo']
    c_round_display = f" ({c_round})" if c_round else ""
    
    st.markdown(f"""
    <div style='text-align: center; font-size: 1em; line-height: 1.8; background-color: {bg_info}; color: {tc} !important; padding: 15px; border-radius: 12px; border: 1px solid rgba(128,128,128,0.1); font-weight: 600;'>
        📅 <b>תאריך:</b> {formatted_date} <br>
        🏆 <b>תחרות:</b> <img src='{c_league_logo}' width='20' style='vertical-align: middle; margin-left: 4px; border-radius: 50%;'> {c_league}{c_round_display} <br>
        🏟️ <b>אצטדיון:</b> {stadium}
    </div>
    """, unsafe_allow_html=True)

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

# --- איפוס חיפוש בעת מעבר מסך ---
if nav_choice != "🔍 חיפוש והוספת משחקים":
    st.session_state.t1_opts = []
    st.session_state.t2_opts = []
    st.session_state.search_results = []

# ==========================================
# מסך 1: יומן המשחקים השמורים
# ==========================================
if nav_choice == "📋 יומן המשחקים":
    if len(st.session_state.saved_matches) > 0:
        
        # --- פיצ'ר "ביום הזה" (Memories) ---
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
                    try:
                        h_g = int(score.split('-')[0].strip())
                        a_g = int(score.split('-')[1].strip())
                        if h_g > a_g: win_txt = f"ראיתי את {h_team} מנצחת"
                        elif a_g > h_g: win_txt = f"ראיתי את {a_team} מנצחת"
                        else: win_txt = f"ראיתי את המשחק ביניהן מסתיים בתיקו"
                    except:
                        win_txt = f"ראיתי אותן משחקות"
                    
                    msg = f"היום לפני {years_str} הייתי באצטדיון ו{win_txt} (תוצאה: {score})! 🏟️"
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
            st.markdown("<h4 style='text-align: right; color: gray !important; font-size: 1.1em;'>חיפוש וסינון ביומן 🔍</h4>", unsafe_allow_html=True)
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
        
        if len(filtered_matches) == 0:
            st.warning("לא נמצאו משחקים שתואמים לחיפוש שלך.")
            
        for idx, match in enumerate(filtered_matches):
            date = match.get('תאריך', '')
            competition = match.get('תחרות', '')
            stadium = match.get('אצטדיון', '')
            home_team = match.get('מארחת', '')
            away_team = match.get('אורחת', '')
            score = match.get('תוצאה', '')
            home_logo = match.get('לוגו_מארחת', '')
            away_logo = match.get('לוגו_אורחת', '')
            league_logo = match.get('לוגו_תחרות', '')
            match_id = match.get('ID_משחק')
            attended = match.get('הייתי_במשחק', False)
            
            # עמודות קומפקטיות שמכריחות את כפתור הסימון והמחיקה לעמוד מימין למשחק
            cols = st.columns([12, 3, 1])
            
            with cols[0]:
                st.markdown(match_card_html(date, competition, stadium, home_team, away_team, score, home_logo, away_logo, league_logo, st.session_state.theme, attended), unsafe_allow_html=True)
                
                with st.expander("📊 הצג אירועים וסטטיסטיקות"):
                    render_match_details(match_id, st.session_state.theme)
                    
                    if attended:
                        st.divider()
                        st.markdown("<h4 style='text-align: center; color: gray !important; font-weight: 900;'>📸 זיכרון מהיציע</h4>", unsafe_allow_html=True)
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

            with cols[1]:
                st.write("") 
                new_attended = st.checkbox("הייתי 🏟️", value=attended, key=f"att_{match_id}")
                if new_attended != attended:
                    update_attendance_in_file(match_id, new_attended)
                    st.rerun()

            with cols[2]:
                st.write("") 
                if st.button("🗑️", key=f"del_out_{match_id}", help="מחק משחק"):
                    delete_confirmation_dialog(match_id, f"{home_team} נגד {away_team}")
            
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
            team1_name = st.text_input("team1", placeholder="קבוצה ראשונה", label_visibility="collapsed")
        with col_vs:
            st.markdown("<div class='vs-badge'>VS</div>", unsafe_allow_html=True)
        with col2:
            team2_name = st.text_input("team2", placeholder="קבוצה שנייה", label_visibility="collapsed")

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
                except Exception:
                    t1_en = team1_name
                    t2_en = team2_name

                res1 = search_teams_api(t1_en)
                res2 = search_teams_api(t2_en)
                
                if res1 == "DAILY_LIMIT" or res2 == "DAILY_LIMIT":
                    st.error("🛑 הגעת למגבלה היומית של השרת! (100 חיפושים ביום).")
                    st.session_state.t1_opts = []
                    st.session_state.t2_opts = []
                elif res1 == "RATE_LIMIT" or res2 == "RATE_LIMIT":
                    st.warning("⏳ הגעת למגבלת השרת לדקה. חכה חצי דקה ונסה שוב!")
                    st.session_state.t1_opts = []
                    st.session_state.t2_opts = []
                elif res1 == "INVALID_KEY" or res2 == "INVALID_KEY":
                    st.error("🔑 מפתח ה-API שלך שגוי או לא פעיל.")
                    st.session_state.t1_opts = []
                    st.session_state.t2_opts = []
                elif res1 == "API_ERROR" or res2 == "API_ERROR" or res1 == "NETWORK_ERROR" or res2 == "NETWORK_ERROR":
                    st.error("⚠️ יש בעיית תקשורת עם השרת.")
                    st.session_state.t1_opts = []
                    st.session_state.t2_opts = []
                elif not res1 or not res2:
                    st.info(f"לא מצאנו את הקבוצות. נסה לאיית באנגלית (כמו Al Hilal).")
                    st.session_state.t1_opts = []
                    st.session_state.t2_opts = []
                else:
                    st.session_state.t1_opts = res1
                    st.session_state.t2_opts = res2
                    st.session_state.search_results = [] 

    if st.session_state.t1_opts and st.session_state.t2_opts:
        st.markdown("<hr style='margin: 20px 0; border: 0; border-top: 2px dashed rgba(128,128,128,0.2);'>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; font-weight: 900; font-size: 1.2em;'>🎯 בחר את הקבוצות המדויקות:</h4>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            t1_sel = st.selectbox("בחר קבוצה 1:", options=st.session_state.t1_opts, format_func=lambda x: f"{x['name']} ({x['country']})")
        with c2:
            t2_sel = st.selectbox("בחר קבוצה 2:", options=st.session_state.t2_opts, format_func=lambda x: f"{x['name']} ({x['country']})")
            
        st.write("")
        _, btn_col2, _ = st.columns([1, 2, 1])
        with btn_col2:
            fetch_matches = st.button("שלב 2: הצג משחקים ביניהן 🚀", use_container_width=True, type="primary")
            
        if fetch_matches:
            with st.spinner("שולף היסטוריית משחקים..."):
                url = "https://v3.football.api-sports.io/fixtures/headtohead"
                querystring = {"h2h": f"{t1_sel['id']}-{t2_sel['id']}"}
                headers = {"x-apisports-key": API_KEY}
                
                response = requests.get(url, headers=headers, params=querystring)
                data = response.json()
                
                if data.get('errors') and len(data['errors']) > 0:
                    err = data['errors']
                    if 'requests' in err: st.error("🛑 הגעת למגבלה היומית של השרת!")
                    elif 'rateLimit' in err: st.warning("⏳ חרגת ממגבלת הקריאות לדקה.")
                    else: st.error("⚠️ שגיאת שרת.")
                elif data.get('results', 0) > 0:
                    matches = data['response']
                    finished_statuses = ['FT', 'AET', 'PEN']
                    past_matches = [m for m in matches if m['fixture']['status']['short'] in finished_statuses]
                    
                    if len(past_matches) > 0:
                        past_matches = sorted(past_matches, key=lambda x: x['fixture']['date'], reverse=True)
                        st.session_state.search_results = past_matches
                    else:
                        st.session_state.search_results = []
                        st.warning("לא נמצאו משחקים שהסתיימו בין הקבוצות האלו.")
                else:
                    st.session_state.search_results = []
                    st.warning("לא נמצאו משחקים בכלל בין הקבוצות האלו.")

    if len(st.session_state.search_results) > 0:
        st.write("---")
        st.markdown("### תוצאות אחרונות שנמצאו:")
        
        for idx, match in enumerate(st.session_state.search_results[:15]):
            date = match['fixture']['date'][:10]
            stadium = match['fixture']['venue']['name']
            competition = match['league']['name']
            home_team = match['teams']['home']['name']
            away_team = match['teams']['away']['name']
            home_goals = match['goals']['home']
            away_goals = match['goals']['away']
            match_id = match['fixture']['id'] 
            
            home_logo = match['teams']['home']['logo']
            away_logo = match['teams']['home']['logo'] # תיקון אוטומטי
            away_logo = match['teams']['away']['logo']
            league_logo = match['league']['logo'] 
            
            col_text, col_btn = st.columns([5, 1])
            
            with col_text:
                st.markdown(match_card_html(date, competition, stadium, home_team, away_team, f"{home_goals} - {away_goals}", home_logo, away_logo, league_logo, st.session_state.theme), unsafe_allow_html=True)
                
            with col_btn:
                st.write("")
                st.write("")
                is_saved = any(str(saved.get('ID_משחק')) == str(match_id) for saved in st.session_state.saved_matches)
                
                if is_saved:
                    st.button("✅", key=f"saved_{match_id}_{idx}", disabled=True, use_container_width=True, help="נשמר")
                else:
                    if st.button("➕", key=f"add_{match_id}_{idx}", use_container_width=True, help="הוסף ליומן"):
                        match_data = {
                            "ID_משחק": match_id,
                            "תאריך": date,
                            "תחרות": competition,
                            "מארחת": home_team,
                            "תוצאה": f"{home_goals} - {away_goals}",
                            "אורחת": away_team,
                            "אצטדיון": stadium,
                            "לוגו_מארחת": home_logo,
                            "לוגו_אורחת": away_logo,
                            "לוגו_תחרות": league_logo,
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
    is_light = (st.session_state.theme == "בהיר ☀️")
    
    if len(saved) == 0:
        st.info("יומן המשחקים שלך עדיין ריק. חפש ושמור משחקים כדי לראות כאן נתונים מעניינים!")
    else:
        total_matches = len(saved)
        total_goals = 0
        total_attended = 0
        teams_counter = Counter()
        stadiums_counter = Counter()
        comps_counter = Counter()
        
        for match in saved:
            if match.get('הייתי_במשחק', False):
                total_attended += 1
                
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
            
            comp = match.get('תחרות', '')
            if comp and comp != 'None': comps_counter[comp] += 1
            
        avg_goals = round(total_goals / total_matches, 2) if total_matches > 0 else 0
        top_team = teams_counter.most_common(1)[0][0] if teams_counter else "אין נתונים"
        top_stadium = stadiums_counter.most_common(1)[0][0] if stadiums_counter else "אין נתונים"
        top_comp = comps_counter.most_common(1)[0][0] if comps_counter else "אין נתונים"
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-title'>משחקים ביומן</div>
                <div class='stat-value'>🏟️ {total_matches}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-title'>שערים שראית</div>
                <div class='stat-value'>⚽ {total_goals}</div>
                <div style='color: gray !important; font-size: 0.85em; font-weight: bold;'>ממוצע {avg_goals} למשחק</div>
            </div>
            """, unsafe_allow_html=True)
            
        col3, col4 = st.columns(2)
        with col3:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-title'>קבוצה מובילה</div>
                <div class='stat-value' style='font-size: 1.4em; margin-top: 10px;'>🛡️ {top_team}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-title'>משחקי יציע</div>
                <div class='stat-value' style='font-size: 1.6em; color: #ffc107 !important;'>🎟️ {total_attended}</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("---")
        st.markdown("<h4 style='text-align: center; color: gray !important; margin-bottom: 15px; font-weight: 900; font-size: 1.1em;'>📤 ייצוא ושיתוף</h4>", unsafe_allow_html=Team := True, unsafe_allow_html=True) # type: ignore
        
        df_export = pd.DataFrame(saved)
        csv_export = df_export.to_csv(index=False).encode('utf-8-sig')
        
        wa_text = f"""⚽ *הסטטיסטיקות שלי ביציע ובספה!* ⚽
        
🏟️ משחקים שצפיתי: {total_matches}
🎟️ משחקים מהיציע: {total_attended}
🥅 סך הכל שערים שראיתי: {total_goals} ({avg_goals} למשחק!)
🛡️ הקבוצה הנצפית ביותר: {top_team}
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
