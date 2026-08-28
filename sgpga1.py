import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import numpy as np
from io import BytesIO

# =========================================================
# 페이지 설정 및 KPGA 스타일 디자인 (모바일 반응형 CSS 추가)
# =========================================================
st.set_page_config(
    page_title="SGPGA - (주)시공사 골프협회",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# KPGA 브랜드 컬러 및 디자인 시스템 적용 + 모바일 반응형 UI 보완
st.markdown("""
    <style>
    /* 메인 배경 및 폰트 설정 */
    .stApp {
        background-color: #f7f9fa;
        font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    }
    
    /* 상단 헤더 스타일 */
    .kpga-header {
        background: linear-gradient(135deg, #0A192F 0%, #1E3A8A 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .kpga-header h1 {
        margin: 0;
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .kpga-header p {
        margin: 5px 0 0 0;
        font-size: 12px;
        color: #93c5fd;
    }

    /* 사이드바 스타일링 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }

    /* 카드 및 컨테이너 스타일 */
    .kpga-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* 테이블 및 데이터프레임 헤더 강조 */
    thead tr th {
        background-color: #0A192F !important;
        color: white !important;
        text-align: center !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }

    /* 버튼 스타일 다듬기 */
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 4px;
        border: none;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: background-color 0.2s;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #0A192F;
        color: white;
    }

    /* 탭 스타일 조정 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 4px 4px 0 0;
        border: 1px solid #e2e8f0;
        padding: 8px 12px;
        font-weight: 600;
        color: #475569;
        font-size: 13px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A !important;
        color: white !important;
        border-color: #1E3A8A !important;
    }

    /* =========================================================
       모바일 화면(너비 768px 이하) 최적화 미디어 쿼리
       ========================================================= */
    @media (max-width: 768px) {
        /* 상단 헤더 세로 정렬로 변경하여 찌그러짐 방지 */
        .kpga-header {
            flex-direction: column;
            align-items: flex-start;
            padding: 15px;
        }
        .kpga-header h1 {
            font-size: 18px;
        }
        .kpga-header div:last-child {
            margin-top: 8px;
            text-align: left !important;
        }
        
        /* 스코어 입력 등 9개 컬럼 인풋 셀이 모바일에서 좁아지지 않도록 간격 조정 */
        .stNumberInput input {
            font-size: 14px !important;
            padding: 2px !important;
        }
        
        /* 여백 줄이기 */
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# 상단 브랜드 헤더 영역
st.markdown("""
    <div class="kpga-header">
        <div>
            <h1>SGPGA 공식 토너먼트 운영 시스템</h1>
            <p>SMART GOLF PROFESSIONAL GOLF ASSOCIATION</p>
        </div>
        <div style="text-align: right; font-size: 12px; color: #cbd5e1;">
            OFFICIAL PORTAL<br><b>V2.0 MOBILE</b>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# 세션 상태(Session State) 초기화
# =========================================================
AFFILIATION_OPTIONS = [
    "회장", "부회장", "대표이사", "전무이사", "상무이사", 
    "이사", "직장", "부장", "차장", "반장", "과장", "조장", "대리", "실무", "협력사대표"
]

STAGE_OPTIONS = ["예선전", "8강전", "4강전", "결승(FINAL)"]
DEFAULT_PARS = [4, 4, 3, 5, 4, 4, 3, 4, 5,  4, 4, 3, 5, 4, 4, 3, 4, 5] # 18홀 기본 PAR (총 72파)
TOTAL_PAR = sum(DEFAULT_PARS) # 72

# 각 골프장별 코스별 상세 홀 PAR 정보 데이터베이스 정의
GOLF_COURSE_HOLE_PARS = {
    "정산CC": {
        "해우": [4, 5, 3, 5, 4, 3, 4, 4, 4],
        "달우": [5, 3, 4, 4, 5, 4, 4, 3, 4],
        "별우": [5, 3, 4, 4, 5, 4, 4, 3, 4]
    },
    "보라CC": {
        "에드워드": [4, 3, 5, 4, 4, 5, 3, 4, 4],
        "윌리엄": [5, 4, 4, 3, 4, 5, 4, 3, 4],
        "헨리": [4, 5, 4, 3, 4, 5, 3, 4, 4]
    },
    "드비치CC": {
        "OUT": [4, 5, 4, 4, 4, 3, 5, 3, 4],
        "IN": [4, 4, 5, 3, 4, 4, 4, 3, 5]
    },
    "타미우스CC": {
        "마운틴": [4, 4, 3, 5, 4, 3, 5, 4, 4],
        "우드": [4, 4, 3, 5, 4, 4, 3, 4, 5],
        "레이크": [4, 5, 3, 4, 4, 5, 3, 4, 4]
    },
    "밀양노벨CC": {
        "LAKE": [4, 4, 5, 3, 4, 3, 4, 5, 4],
        "HILL": [4, 4, 5, 3, 5, 3, 4, 4, 4]
    }
}

GOLF_COURSES = {cc: list(courses.keys()) for cc, courses in GOLF_COURSE_HOLE_PARS.items()}

if "score_reset_version" not in st.session_state:
    st.session_state.score_reset_version = 0

# 1. 대회 리스트 관리 (대회 생성 및 상금/상금할당 포함)
if "tournaments_list" not in st.session_state:
    st.session_state.tournaments_list = [
        {
            "대회ID": "SG001",
            "대회명": "제2회 SGPGA 오픈 챔피언십",
            "골프장": "정산CC",
            "총상금": 4000000,
            "상금배분": {"1위": 50, "2위": 25, "3위": 15, "4위": 10}
        }
    ]

# 2. 역대 우승자 기록 데이터베이스
if "hall_of_fame" not in st.session_state:
    st.session_state.hall_of_fame = [
        {"회차": "제1회 대회", "대회명": "제1회 SGPGA 오픈 챔피언십", "우승자": "윤 덕", "소속": "대표이사", "스코어": 90, "날짜": "2025-10-30"}
    ]

# 3. 실시간 멋진 샷(홀인원, 이글 등) 알림 피드
if "shot_achievements" not in st.session_state:
    st.session_state.shot_achievements = [
        "⛳ [알림] 제2회 SGPGA 오픈 챔피언십 대회가 개최되었습니다. 멋진 샷을 기대합니다!",
        "🔥 [실시간] 박상주 선수 버디 기록!",
        "🦅 [실시간] 윤덕 선수 이글 기록 달성!"
    ]

# 4. 선수 데이터베이스 (16명 샘플)
if "players" not in st.session_state:
    st.session_state.players = pd.DataFrame([
        {"선수ID": "SG001", "이름": "윤 덕", "소속": "대표이사", "핸디캡": 21, "연락처": "010-7708-5600", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 94, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG002", "이름": "윤중환", "소속": "전무이사", "핸디캡": 31, "연락처": "010-9180-2342", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 101, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG003", "이름": "윤시준", "소속": "대리", "핸디캡": 27, "연락처": "010-6862-7819", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 99, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG005", "이름": "박원진", "소속": "상무이사", "핸디캡": 16, "연락처": "010-5050-9491", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 88, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG006", "이름": "김정미", "소속": "부장", "핸디캡": 44, "연락처": "010-3484-3297", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 0, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG007", "이름": "박호일", "소속": "직장", "핸디캡": 38, "연락처": "010-8509-6711", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 114, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG008", "이름": "박상주", "소속": "직장", "핸디캡": 23, "연락처": "010-3768-2975", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 88, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG009", "이름": "임주민", "소속": "차장", "핸디캡": 27, "연락처": "010-2844-9013", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 99, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG010", "이름": "이문종", "소속": "반장", "핸디캡": 20, "연락처": "010-6663-0358", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 88, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG011", "이름": "김민석", "소속": "반장", "핸디캡": 25, "연락처": "010-8509-6033", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 102, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG012", "이름": "심왕국", "소속": "부장", "핸디캡": 28, "연락처": "010-4643-6722", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 99, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG013", "이름": "김형국", "소속": "조장", "핸디캡": 27, "연락처": "010-3333-4444", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 99, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG014", "이름": "박순정", "소속": "과장", "핸디캡": 33, "연락처": "010-2631-8262", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 102, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG015", "이름": "장호승", "소속": "과장", "핸디캡": 25, "연락처": "010-4644-4175", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 100, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG016", "이름": "김광식", "소속": "반장", "핸디캡": 32, "연락처": "010-9398-3171", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 100, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG017", "이름": "김민식", "소속": "조장", "핸디캡": 32, "연락처": "010-2800-0924", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 102, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG018", "이름": "김지산", "소속": "과장", "핸디캡": 27, "연락처": "010-3754-0935", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 99, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG019", "이름": "변상기", "소속": "실무", "핸디캡": 20, "연락처": "010-2403-7259", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 88, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG020", "이름": "이정우", "소속": "차장", "핸디캡": 30, "연락처": "010-6281-1414", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 97, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0},
        {"선수ID": "SG021", "이름": "류명수", "소속": "반장", "핸디캡": 30, "연락처": "010-2561-6654", "경기상태": "진행중", "최종진출단계": "예선전", "예선스코어": 98, "8강전스코어": 0, "4강전스코어": 0, "결승스코어": 0}
    ])

# 플레이어별 다중 라운드 스코어 기록 관리용 초기화
if "detailed_hole_scores_multi" not in st.session_state:
    st.session_state.detailed_hole_scores_multi = {}
    for _, p in st.session_state.players.iterrows():
        p_name = p["이름"]
        initial_holes = {f"{h}홀": DEFAULT_PARS[h-1] for h in range(1, 19)}
        st.session_state.detailed_hole_scores_multi[p_name] = [initial_holes]

if "detailed_hole_scores" not in st.session_state:
    st.session_state.detailed_hole_scores = {}
    for p_name, rounds in st.session_state.detailed_hole_scores_multi.items():
        st.session_state.detailed_hole_scores[p_name] = rounds[-1]

if "teams" not in st.session_state:
    st.session_state.teams = []

if "bracket" not in st.session_state:
    st.session_state.bracket = {
        "8강전": [],
        "4강전": [],
        "결승(FINAL)": []
    }

if "matches" not in st.session_state:
    st.session_state.matches = pd.DataFrame([
        {
            "대회명": "제2회 SGPGA 오픈 챔피언십", 
            "경기구분": "예선전", 
            "경기장 및 코스": "정산CC 별우, 해우코스",
            "날짜": "2026-08-21", 
            "조": "1조", 
            "선수": "박상주, 김광식, 류명수, 김민식", 
            "티오프시간": "13:38"
        },
        {
            "대회명": "제2회 SGPGA 오픈 챔피언십", 
            "경기구분": "예선전", 
            "경기장 및 코스": "정산CC 별우, 해우코스",
            "날짜": "2026-09-04", 
            "조": "2조", 
            "선수": "윤시준, 변상기, 김형국, 이문종", 
            "티오프시간": "08:08"
        }
    ])

if "history" not in st.session_state:
    st.session_state.history = []

if "nav_menu" not in st.session_state:
    st.session_state.nav_menu = "대회/선수 관리"

if "final_winner" not in st.session_state:
    st.session_state.final_winner = None

# =========================================================
# 헬퍼 함수
# =========================================================
def parse_course_info(course_str):
    golf_club = "정산CC"
    front_c = "별우"
    back_c = "해우"
    
    for cc_name, courses in GOLF_COURSE_HOLE_PARS.items():
        if cc_name in course_str:
            golf_club = cc_name
            c_keys = list(courses.keys())
            
            found_courses = []
            for k in c_keys:
                idx = course_str.find(k)
                if idx != -1:
                    found_courses.append((idx, k))
            
            found_courses.sort(key=lambda x: x[0])
            matched = [k for _, k in found_courses]
            
            if len(matched) >= 2:
                front_c = matched[0]
                back_c = matched[1]
            elif len(matched) == 1:
                front_c = matched[0]
                remaining = [k for k in c_keys if k != matched[0]]
                back_c = remaining[0] if remaining else matched[0]
            break
    return golf_club, front_c, back_c

def parse_course_pars(course_str):
    front_pars = DEFAULT_PARS[0:9]
    back_pars = DEFAULT_PARS[9:18]
    
    cc, f_c, b_c = parse_course_info(course_str)
    if cc in GOLF_COURSE_HOLE_PARS:
        courses = GOLF_COURSE_HOLE_PARS[cc]
        if f_c in courses:
            front_pars = courses[f_c]
        if b_c in courses:
            back_pars = courses[b_c]
    return front_pars, back_pars

def get_team_players(team_name):
    target_team = next((t for t in st.session_state.teams if t["팀명"] == team_name), None)
    if not target_team:
        return []
    p1 = target_team["선수1"]
    p2 = target_team["선수2"]
    players = [p1] if p1 and p1 != "-" else []
    if p2 and p2 != "-":
        players.append(p2)
    return players

def update_player_status(player_names, stage_name, status_name):
    for p_name in player_names:
        idx = st.session_state.players[st.session_state.players["이름"] == p_name].index
        if not idx.empty:
            st.session_state.players.loc[idx, "최종진출단계"] = stage_name
            st.session_state.players.loc[idx, "경기상태"] = status_name

def get_player_ranking_df():
    df = st.session_state.players.copy()
    if df.empty:
        return df

    avg_handicaps = []
    score_cols = ["예선스코어", "8강전스코어", "4강전스코어", "결승(FINAL)스코어"]

    for _, row in df.iterrows():
        over_strokes = [(row[col] - TOTAL_PAR) for col in score_cols if col in row and row.get(col, 0) > 0]
        if over_strokes:
            avg_h = sum(over_strokes) / len(over_strokes)
            avg_handicaps.append(round(avg_h, 2))
        else:
            avg_handicaps.append(None)

    df["_평균핸디_num"] = avg_handicaps
    df = df.sort_values(by=["_평균핸디_num", "선수ID"], ascending=[True, True], na_position="last").reset_index(drop=True)

    valid_mask = df["_평균핸디_num"].notna()
    df["순위"] = "-"
    df["평균핸디"] = "-"

    if valid_mask.any():
        df.loc[valid_mask, "순위"] = df.loc[valid_mask, "_평균핸디_num"].rank(method="min").astype(int).astype(str) + "위"
        df.loc[valid_mask, "평균핸디"] = df.loc[valid_mask, "_평균핸디_num"].apply(lambda x: f"{x:+.1f}" if x != 0 else "0.0")

    df = df.drop(columns=["_평균핸디_num"])
    cols = ["순위", "평균핸디"] + [c for c in df.columns if c not in ["순위", "평균핸디"]]
    return df[cols]

def calculate_match_skins(team1_name, team2_name, stage_name="8강전", course_info=""):
    if not team1_name or not team2_name or team2_name == "부전승" or "TBD" in team1_name or "TBD" in team2_name:
        return 0, 0, False, "대기 중"

    t1_players = get_team_players(team1_name)
    t2_players = get_team_players(team2_name)

    if not t1_players or not t2_players:
        return 0, 0, False, "선수 정보 없음"

    front_pars, back_pars = parse_course_pars(course_info)
    all_pars = front_pars + back_pars

    score_col = f"{stage_name}스코어"

    t1_ready = all(
        st.session_state.players[st.session_state.players["이름"] == p][score_col].values[0] > 0
        for p in t1_players if not st.session_state.players[st.session_state.players["이름"] == p].empty
    )
    t2_ready = all(
        st.session_state.players[st.session_state.players["이름"] == p][score_col].values[0] > 0
        for p in t2_players if not st.session_state.players[st.session_state.players["이름"] == p].empty
    )

    if not (t1_ready and t2_ready):
        return 0, 0, False, "스코어 입력 진행 중"

    t1_wins = 0
    t2_wins = 0

    for h in range(1, 19):
        h_key = f"{h}홀"
        par_val = all_pars[h-1]
        t1_hole_score = sum([
            st.session_state.detailed_hole_scores.get(p, {}).get(h_key, par_val)
            for p in t1_players
        ])
        t2_hole_score = sum([
            st.session_state.detailed_hole_scores.get(p, {}).get(h_key, par_val)
            for p in t2_players
        ])

        if t1_hole_score < t2_hole_score:
            t1_wins += 1
        elif t2_hole_score < t1_hole_score:
            t2_wins += 1

    detail_str = f"{t1_wins}승 vs {t2_wins}승"
    return t1_wins, t2_wins, True, detail_str

def get_team_players_str(team_name):
    t = next((team for team in st.session_state.teams if team["팀명"] == team_name), None)
    if t:
        return t.get("선수목록", "")
    return ""

def update_tournament_bracket():
    for m in st.session_state.bracket.get("8강전", []):
        t1_p = get_team_players(m["팀1"])
        t2_p = get_team_players(m["팀2"])

        if m["팀2"] == "부전승":
            m["승리팀"] = m["팀1"]
            update_player_status(t1_p, "4강전", "진행중")
            continue
            
        match_row = st.session_state.matches[st.session_state.matches["조"].str.contains(m["매치ID"], na=False)]
        c_info = match_row["경기장 및 코스"].values[0] if not match_row.empty else ""

        t1_wins, t2_wins, is_done, _ = calculate_match_skins(m["팀1"], m["팀2"], "8강전", c_info)
        if is_done:
            if t1_wins >= t2_wins:
                m["승리팀"] = m["팀1"]
                update_player_status(t1_p, "4강전", "진행중")
                update_player_status(t2_p, "8강전", "종료")
            else:
                m["승리팀"] = m["팀2"]
                update_player_status(t2_p, "4강전", "진행중")
                update_player_status(t1_p, "8강전", "종료")

    sf_matches = st.session_state.bracket.get("4강전", [])
    b_matches = st.session_state.bracket.get("8강전", [])
    b_all_done = len(b_matches) > 0 and all(bm.get("승리팀") is not None for bm in b_matches)
    
    if len(b_matches) >= 4 and len(sf_matches) >= 2:
        sf_matches[0]["팀1"] = b_matches[0].get("승리팀") or "TBD (8강1경기 승자)"
        sf_matches[0]["팀2"] = b_matches[1].get("승리팀") or "TBD (8강2경기 승자)"
        sf_matches[1]["팀1"] = b_matches[2].get("승리팀") or "TBD (8강3경기 승자)"
        sf_matches[1]["팀2"] = b_matches[3].get("승리팀") or "TBD (8강4경기 승자)"

        if b_all_done:
            if st.session_state.matches[st.session_state.matches["경기구분"] == "4강전"].empty:
                today_str = datetime.today().strftime("%Y-%m-%d")
                sf_schedule = [
                    {
                        "대회명": "제2회 SGPGA 오픈 챔피언십",
                        "경기구분": "4강전",
                        "경기장 및 코스": "정산CC 별우, 해우코스",
                        "날짜": today_str,
                        "조": f"SF1 ({sf_matches[0]['팀1']} vs {sf_matches[0]['팀2']})",
                        "선수": f"{get_team_players_str(sf_matches[0]['팀1'])} / {get_team_players_str(sf_matches[0]['팀2'])}",
                        "티오프시간": "10:00"
                    },
                    {
                        "대회명": "제2회 SGPGA 오픈 챔피언십",
                        "경기구분": "4강전",
                        "경기장 및 코스": "정산CC 별우, 해우코스",
                        "날짜": today_str,
                        "조": f"SF2 ({sf_matches[1]['팀1']} vs {sf_matches[1]['팀2']})",
                        "선수": f"{get_team_players_str(sf_matches[1]['팀1'])} / {get_team_players_str(sf_matches[1]['팀2'])}",
                        "티오프시간": "10:20"
                    }
                ]
                st.session_state.matches = pd.concat([st.session_state.matches, pd.DataFrame(sf_schedule)], ignore_index=True)

    for sf in sf_matches:
        if "TBD" not in sf.get("팀1", "") and "TBD" not in sf.get("팀2", ""):
            t1_p = get_team_players(sf["팀1"])
            t2_p = get_team_players(sf["팀2"])
            match_row = st.session_state.matches[st.session_state.matches["조"].str.contains(sf["매치ID"], na=False)]
            c_info = match_row["경기장 및 코스"].values[0] if not match_row.empty else ""

            t1_wins, t2_wins, is_done, _ = calculate_match_skins(sf["팀1"], sf["팀2"], "4강전", c_info)
            if is_done:
                if t1_wins >= t2_wins:
                    sf["승리팀"] = sf["팀1"]
                    update_player_status(t1_p, "결승(FINAL)", "진행중")
                    update_player_status(t2_p, "4강전", "종료")
                else:
                    sf["승리팀"] = sf["팀2"]
                    update_player_status(t2_p, "결승(FINAL)", "진행중")
                    update_player_status(t1_p, "4강전", "종료")

    f_matches = st.session_state.bracket.get("결승(FINAL)", [])
    sf_all_done = len(sf_matches) > 0 and all(sf.get("승리팀") is not None for sf in sf_matches)

    if len(sf_matches) >= 2 and len(f_matches) >= 1:
        f_matches[0]["팀1"] = sf_matches[0].get("승리팀") or "TBD (4강1경기 승자)"
        f_matches[0]["팀2"] = sf_matches[1].get("승리팀") or "TBD (4강2경기 승자)"

        if sf_all_done:
            if st.session_state.matches[st.session_state.matches["경기구분"] == "결승(FINAL)"].empty:
                today_str = datetime.today().strftime("%Y-%m-%d")
                f_schedule = [{
                    "대회명": "제2회 SGPGA 오픈 챔피언십",
                    "경기구분": "결승(FINAL)",
                    "경기장 및 코스": "정산CC 별우, 해우코스",
                    "날짜": today_str,
                    "조": f"F1 ({f_matches[0]['팀1']} vs {f_matches[0]['팀2']})",
                    "선수": f"{get_team_players_str(f_matches[0]['팀1'])} / {get_team_players_str(f_matches[0]['팀2'])}",
                    "티오프시간": "14:00"
                }]
                st.session_state.matches = pd.concat([st.session_state.matches, pd.DataFrame(f_schedule)], ignore_index=True)

    for f in f_matches:
        if "TBD" not in f.get("팀1", "") and "TBD" not in f.get("팀2", ""):
            t1_p = get_team_players(f["팀1"])
            t2_p = get_team_players(f["팀2"])
            match_row = st.session_state.matches[st.session_state.matches["조"].str.contains(f["매치ID"], na=False)]
            c_info = match_row["경기장 및 코스"].values[0] if not match_row.empty else ""

            t1_wins, t2_wins, is_done, _ = calculate_match_skins(f["팀1"], f["팀2"], "결승(FINAL)", c_info)
            if is_done:
                winner = f["팀1"] if t1_wins >= t2_wins else f["팀2"]
                loser = f["팀2"] if t1_wins >= t2_wins else f["팀1"]
                f["승리팀"] = winner
                winning_player_str = get_team_players_str(winner)
                st.session_state.final_winner = f"{winner} ({winning_player_str})"
                
                update_player_status(get_team_players(winner), "우승", "종료")
                update_player_status(get_team_players(loser), "결승(FINAL)", "종료")
                
                today_date = datetime.today().strftime("%Y-%m-%d")
                if not any(item["우승자"] == winning_player_str for item in st.session_state.hall_of_fame):
                    st.session_state.hall_of_fame.append({
                        "회차": f"제{len(st.session_state.hall_of_fame)+1}회 대회",
                        "대회명": "SGPGA 챔피언십",
                        "우승자": winning_player_str,
                        "소속": "대표팀",
                        "스코어": 68,
                        "날짜": today_date
                    })

def auto_match_and_create_bracket(stage_name, course_info, match_date, start_time_str, interval_minutes, shuffle=False):
    stage_order = {"예선전": 0, "8강전": 1, "4강전": 2, "결승(FINAL)": 3}
    curr_idx = stage_order.get(stage_name, 1)
    
    passed_players = st.session_state.players[
        (st.session_state.players["경기상태"] == "진행중") & 
        (st.session_state.players["최종진출단계"].map(lambda x: stage_order.get(x, 0)) >= curr_idx)
    ].copy()

    if shuffle:
        passed_players = passed_players.sample(frac=1).reset_index(drop=True)
    else:
        passed_players = passed_players.sort_values(by="예선스코어", ascending=True).reset_index(drop=True)
    
    n = len(passed_players)
    if n < 2:
        return False, "팀 매칭을 진행하기 위한 선수(2명 이상)가 부족합니다."
    
    teams = []
    i, j = 0, n - 1
    team_idx = 1
    
    while i < j:
        p1 = passed_players.iloc[i]
        p2 = passed_players.iloc[j]
        team_score = p1["예선스코어"] + p2["예선스코어"]
        teams.append({
            "팀명": f"팀 {team_idx}",
            "선수1": p1["이름"],
            "선수2": p2["이름"],
            "합계스코어": team_score,
            "선수목록": f"{p1['이름']}, {p2['이름']}"
        })
        i += 1
        j -= 1
        team_idx += 1
        
    if i == j:
        p_single = passed_players.iloc[i]
        teams.append({
            "팀명": f"팀 {team_idx}",
            "선수1": p_single["이름"],
            "선수2": "-",
            "합계스코어": p_single["예선스코어"] * 2,
            "선수목록": p_single["이름"]
        })

    st.session_state.teams = teams

    teams_sorted = sorted(teams, key=lambda x: x["합계스코어"])
    num_t = len(teams_sorted)
    
    bracket_matches = []
    t_left, t_right = 0, num_t - 1
    m_count = 1
    
    while t_left < t_right:
        bracket_matches.append({
            "매치ID": f"M{m_count}",
            "팀1": teams_sorted[t_left]["팀명"],
            "팀2": teams_sorted[t_right]["팀명"],
            "선수1": teams_sorted[t_left]["선수목록"],
            "선수2": teams_sorted[t_right]["선수목록"],
            "승리팀": None
        })
        t_left += 1
        t_right -= 1
        m_count += 1
        
    if t_left == t_right:
        bracket_matches.append({
            "매치ID": f"M{m_count}",
            "팀1": teams_sorted[t_left]["팀명"],
            "팀2": "부전승",
            "선수1": teams_sorted[t_left]["선수목록"],
            "선수2": "-",
            "승리팀": teams_sorted[t_left]["팀명"]
        })

    st.session_state.bracket["8강전"] = bracket_matches
    st.session_state.bracket["4강전"] = [
        {"매치ID": "4강1경기", "팀1": "TBD (8강1경기승자)", "팀2": "TBD (8강2경기승자)", "승리팀": None},
        {"매치ID": "4강2경기", "팀1": "TBD (8강3경기승자)", "팀2": "TBD (8강4경기승자)", "승리팀": None}
    ]
    st.session_state.bracket["결승(FINAL)"] = [
        {"매치ID": "F1", "팀1": "TBD (4강1경기승자)", "팀2": "TBD (4강2경기승자)", "승리팀": None}
    ]

    st.session_state.final_winner = None

    start_dt = datetime.strptime(start_time_str, "%H:%M")
    new_matches = []
    
    for g_idx, bm in enumerate(bracket_matches):
        t_time = (start_dt + timedelta(minutes=g_idx * interval_minutes)).strftime("%H:%M")
        new_matches.append({
            "대회명": f"SGPGA {stage_name}",
            "경기구분": stage_name,
            "경기장 및 코스": course_info,
            "날짜": str(match_date),
            "조": f"{bm['매치ID']} ({bm['팀1']} vs {bm['팀2']})",
            "선수": f"{bm['선수1']} / {bm['선수2']}",
            "티오프시간": t_time
        })

    st.session_state.matches = st.session_state.matches[st.session_state.matches["경기구분"] != stage_name]
    st.session_state.matches = pd.concat([st.session_state.matches, pd.DataFrame(new_matches)], ignore_index=True)
    
    return True, f"총 {len(teams)}개 팀 매칭 및 토너먼트 대진표({len(bracket_matches)}경기)가 자동 구성되었습니다."

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

# =========================================================
# 롤링 배너 HTML/CSS 컴포넌트 함수 (왼쪽 -> 오른쪽 방향 적용)
# =========================================================
def render_rolling_banner(notices):
    if not notices:
        notices = ["제2회 SGPGA 오픈 챔피언십 대회가 개최되었습니다. 멋진 샷을 기대합니다!"]
    
    # 텍스트 아이템들을 두 번 반복하여 끊김 없는 무한 스크롤 구현
    notices_html = "".join([f'<div class="rolling-item">📢 {notice}</div>' for notice in notices])
    loop_html = notices_html + notices_html

    banner_html = f"""
    <style>
    .rolling-container {{
        background-color: #fffae6;
        border-left: 5px solid #ffc107;
        padding: 0 15px;
        margin-bottom: 15px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        height: 45px;
        overflow: hidden;
        display: flex;
        align-items: center;
        position: relative;
        width: 100%;
    }}
    .rolling-track {{
        display: flex;
        white-space: nowrap;
        position: absolute;
        will-change: transform;
        /* 왼쪽에서 오른쪽으로 흐르도록 수정 (전체 길이의 50% 지점에서 시작해 0%로 이동) */
        animation: scrollRightToLeft 25s linear infinite;
    }}
    .rolling-track:hover {{
        animation-play-state: paused;
    }}
    .rolling-item {{
        display: inline-flex;
        align-items: center;
        font-weight: bold;
        color: #856404;
        font-size: 15px;
        margin-right: 60px;
    }}
    @keyframes scrollRightToLeft {{
        0% {{ transform: translateX(-50%); }}
        100% {{ transform: translateX(0%); }}
    }}
    </style>
    <div class="rolling-container">
        <div class="rolling-track">{loop_html}</div>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)

# 예선전 동일인 다중 라운드 참여 지원 스코어카드 렌더링 및 저장 함수
def render_and_save_scorecard_section(player_names, stage_name, course_info):
    front_pars, back_pars = parse_course_pars(course_info)
    all_pars = front_pars + back_pars
    
    if "detailed_hole_scores_multi" not in st.session_state:
        st.session_state.detailed_hole_scores_multi = {}

    with st.form(key=f"scorecard_form_{stage_name}_{'_'.join(player_names)}"):
        st.subheader(f"[{stage_name}] 스코어 일괄 입력 및 저장")
        
        if stage_name == "예선전":
            st.info("💡 **예선전 안내**: 동일 선수가 여러 번 라운드(재참여)할 수 있습니다. 저장 시 기존 기록에 새로운 라운드 기록이 누적되며, 선수 리스트에는 **가장 좋은(최저타) 성적**이 공식 예선 스코어로 반영됩니다.")
        
        temp_scores = {}
        
        for p_name in player_names:
            if p_name not in st.session_state.detailed_hole_scores_multi:
                st.session_state.detailed_hole_scores_multi[p_name] = [{f"{h}홀": DEFAULT_PARS[h-1] for h in range(1, 19)}]
                
            round_count = len(st.session_state.detailed_hole_scores_multi[p_name])
            st.markdown(f"**플레이어: {p_name}** (현재 등록된 예선 라운드 횟수: {round_count}회)")
                
            player_scores = {}
            
            cols = st.columns(9)
            for h in range(1, 19):
                h_key = f"{h}홀"
                default_par = all_pars[h-1]
                current_val = st.session_state.detailed_hole_scores_multi[p_name][-1].get(h_key, default_par)
                
                col_idx = (h - 1) % 9
                with cols[col_idx]:
                    val = st.number_input(
                        f"{h}H(P{default_par})", 
                        min_value=1, 
                        max_value=10, 
                        value=int(current_val), 
                        step=1, 
                        key=f"input_{p_name}_{stage_name}_{h}_{round_count}"
                    )
                    player_scores[h_key] = val
            
            temp_scores[p_name] = player_scores
            st.divider()

        submitted = st.form_submit_button("저장하기", type="primary", use_container_width=True)
        
        if submitted:
            score_map_col = {
                "예선전": "예선스코어",
                "8강전": "8강전스코어",
                "4강전": "4강전스코어",
                "결승(FINAL)": "결승스코어"
            }
            score_col = score_map_col.get(stage_name, "예선스코어")
            
            for p_name, p_scores in temp_scores.items():
                total_strokes = sum(p_scores.values())
                
                if stage_name == "예선전":
                    if p_name not in st.session_state.detailed_hole_scores_multi:
                        st.session_state.detailed_hole_scores_multi[p_name] = []
                    st.session_state.detailed_hole_scores_multi[p_name].append(p_scores)
                    
                    st.session_state.detailed_hole_scores[p_name] = p_scores
                    
                    all_round_scores = [sum(r.values()) for r in st.session_state.detailed_hole_scores_multi[p_name]]
                    best_score = min(all_round_scores)
                    
                    p_idx = st.session_state.players[st.session_state.players["이름"] == p_name].index
                    if not p_idx.empty:
                        st.session_state.players.loc[p_idx, score_col] = best_score
                else:
                    if p_name not in st.session_state.detailed_hole_scores:
                        st.session_state.detailed_hole_scores[p_name] = {}
                    st.session_state.detailed_hole_scores[p_name].update(p_scores)
                    
                    p_idx = st.session_state.players[st.session_state.players["이름"] == p_name].index
                    if not p_idx.empty:
                        st.session_state.players.loc[p_idx, score_col] = total_strokes
            
            st.success("스코어가 성공적으로 저장되었습니다! (데이터 유실 방지 및 다중 라운드 누적 반영 완료)")
            st.rerun()

update_tournament_bracket()

# =========================================================
# 사이드바 Navigation
# =========================================================
st.sidebar.title("🏆 SGPGA 메뉴")

menu_options = [
    "대회/선수 관리", 
    "단계별 종료 및 컷오프", 
    "경기 일정 및 조 편성 관리", 
    "토너먼트 대진표 & 승패 관리", 
    "실시간 스코어 입력", 
    "리더보드",
    "📊 대회 통계 리포트",
    "🌟 역대 대회 우승자 명예의 전당"
]

selected_menu = st.sidebar.radio(
    "원하시는 기능을 선택하세요:",
    menu_options,
    index=menu_options.index(st.session_state.nav_menu) if st.session_state.nav_menu in menu_options else 0
)

st.session_state.nav_menu = selected_menu

# =========================================================
# 메인 페이지 화면 구성
# =========================================================
st.title("⛳ SGPGA 통합 관리 시스템")

# 실시간 롤링 배너 출력
notices_to_show = st.session_state.get("shot_achievements") or [
    "제2회 SGPGA 오픈 챔피언십 대회가 개최되었습니다. 멋진 샷을 기대합니다!"
]
render_rolling_banner(notices_to_show)

if st.session_state.final_winner:
    st.success(f"🏆 **[대회 최종 우승 확정]** 👑 **{st.session_state.final_winner}** 👑 축하합니다! 🎉")

st.markdown("---")

# =========================================================
# 메뉴 1: 대회/선수 관리
# =========================================================
if st.session_state.nav_menu == "대회/선수 관리":
    st.header("🏆 대회 생성 및 선수 명단 관리")
    
    with st.expander("⛳ 신규 대회 개설 및 순위별 상금 할당 설정", expanded=True):
        with st.form("create_tournament_form"):
            col_t1, col_t2, col_t3 = st.columns(3)
            new_t_id = col_t1.text_input("대회 ID", value=f"T0{len(st.session_state.tournaments_list)+1:02d}")
            new_t_name = col_t2.text_input("대회명", placeholder="제2회 SGPGA 오픈 챔피언십")
            new_t_cc = col_t3.selectbox("개최 골프장", options=list(GOLF_COURSES.keys()))
            
            col_t4, col_t5 = st.columns(2)
            total_prize_pool = col_t4.number_input("대회 총상금 (원)", min_value=0, value=20000000, step=1000000, format="%d")
            
            st.markdown("---")
            st.markdown("🎖️ **순위별 상금 배분율 설정 (%)** (합계가 100%가 되도록 입력해주세요)")
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            p1_rate = col_p1.number_input("1위 (%)", min_value=0, max_value=100, value=50)
            p2_rate = col_p2.number_input("2위 (%)", min_value=0, max_value=100, value=30)
            p3_rate = col_p3.number_input("3위 (%)", min_value=0, max_value=100, value=15)
            p4_rate = col_p4.number_input("4위 (%)", min_value=0, max_value=100, value=5)
            
            submit_tour = st.form_submit_button("🚀 신규 대회 개설 및 상금 배분 저장", type="primary", use_container_width=True)
            if submit_tour:
                total_rate = p1_rate + p2_rate + p3_rate + p4_rate
                if total_rate != 100:
                    st.error(f"❌ 상금 배분율의 합계가 100%여야 합니다. (현재 합계: {total_rate}%)")
                elif not new_t_name:
                    st.error("대회명을 입력해 주세요.")
                else:
                    new_tour_dict = {
                        "대회ID": new_t_id,
                        "대회명": new_t_name,
                        "골프장": new_t_cc,
                        "총상금": total_prize_pool,
                        "상금배분": {"1위": p1_rate, "2위": p2_rate, "3위": p3_rate, "4위": p4_rate}
                    }
                    st.session_state.tournaments_list.append(new_tour_dict)
                    st.success(f"🎉 '{new_t_name}' 대회가 성공적으로 생성되었습니다! (총상금: {total_prize_pool:,}원)")
                    st.rerun()

    if st.session_state.tournaments_list:
        st.subheader("📋 등록된 대회 및 순위별 상금 내역")
        tour_summary_data = []
        for t in st.session_state.tournaments_list:
            prize = t["총상금"]
            dist = t["상금배분"]
            row_data = {
                "대회ID": t["대회ID"],
                "대회명": t["대회명"],
                "개최골프장": t["골프장"],
                "총상금": f"{prize:,}원",
                "1위 상금": f"{int(prize * dist.get('1위', 0) / 100):,}원 ({dist.get('1위', 0)}%)",
                "2위 상금": f"{int(prize * dist.get('2위', 0) / 100):,}원 ({dist.get('2위', 0)}%)",
                "3위 상금": f"{int(prize * dist.get('3위', 0) / 100):,}원 ({dist.get('3위', 0)}%)",
                "4위 상금": f"{int(prize * dist.get('4위', 0) / 100):,}원 ({dist.get('4위', 0)}%)",
            }
            tour_summary_data.append(row_data)
        st.dataframe(pd.DataFrame(tour_summary_data), use_container_width=True)

    st.markdown("---")
    
    col_a1, col_a2 = st.columns(2)
    
    with col_a1:
        with st.expander("➕ 신규 선수 등록", expanded=False):
            with st.form("add_player_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                p_id = c1.text_input("선수 ID", value=f"P{len(st.session_state.players)+1:03d}")
                p_name = c2.text_input("이름")
                
                c3, c4 = st.columns(2)
                p_affiliation = c3.selectbox("소속", options=AFFILIATION_OPTIONS)
                p_handicap = c4.number_input("핸디캡", min_value=0, max_value=30, value=10)
                p_phone = st.text_input("연락처", placeholder="010-0000-0000")
                
                submit_player = st.form_submit_button("선수 등록", type="primary", use_container_width=True)
                if submit_player:
                    if p_name:
                        new_player = pd.DataFrame([{
                            "선수ID": p_id, 
                            "이름": p_name, 
                            "소속": p_affiliation, 
                            "핸디캡": p_handicap, 
                            "연락처": p_phone,
                            "경기상태": "진행중",
                            "최종진출단계": "예선전",
                            "예선스코어": 0,
                            "8강전스코어": 0,
                            "4강전스코어": 0,
                            "결승스코어": 0
                        }])
                        st.session_state.players = pd.concat([st.session_state.players, new_player], ignore_index=True)
                        st.session_state.detailed_hole_scores[p_name] = {f"{h}홀": DEFAULT_PARS[h-1] for h in range(1, 19)}
                        st.session_state.detailed_hole_scores_multi[p_name] = [{f"{h}홀": DEFAULT_PARS[h-1] for h in range(1, 19)}]
                        st.success(f"{p_name} 선수가 등록되었습니다.")
                        st.rerun()
                    else:
                        st.error("선수 이름을 입력해 주세요.")

        with st.expander("📁 엑셀 파일로 선수 일괄 등록", expanded=False):
            st.caption("선수ID, 이름, 소속, 핸디캡, 연락처 컬럼이 포함된 엑셀 파일을 업로드하세요.")
            uploaded_file = st.file_uploader("엑셀 파일 선택", type=["xlsx", "xls"])
            if uploaded_file is not None:
                try:
                    df_upload = pd.read_excel(uploaded_file)
                    required_cols = ["선수ID", "이름", "소속", "핸디캡", "연락처"]
                    if all(col in df_upload.columns for col in required_cols):
                        for _, row in df_upload.iterrows():
                            row_dict = {
                                "선수ID": str(row["선수ID"]),
                                "이름": str(row["이름"]),
                                "소속": str(row["소속"]),
                                "핸디캡": int(row["핸디캡"]),
                                "연락처": str(row["연락처"]),
                                "경기상태": "진행중",
                                "최종진출단계": "예선전",
                                "예선스코어": 0,
                                "8강전스코어": 0,
                                "4강전스코어": 0,
                                "결승스코어": 0
                            }
                            if not (st.session_state.players["선수ID"] == row_dict["선수ID"]).any():
                                st.session_state.players = pd.concat([st.session_state.players, pd.DataFrame([row_dict])], ignore_index=True)
                                st.session_state.detailed_hole_scores[row_dict["이름"]] = {f"{h}홀": DEFAULT_PARS[h-1] for h in range(1, 19)}
                                st.session_state.detailed_hole_scores_multi[row_dict["이름"]] = [{f"{h}홀": DEFAULT_PARS[h-1] for h in range(1, 19)}]
                        st.success("엑셀 선수 명단이 성공적으로 업로드되었습니다!")
                        st.rerun()
                    else:
                        st.error("엑셀 파일의 컬럼명을 확인해주세요 (선수ID, 이름, 소속, 핸디캡, 연락처)")
                except Exception as e:
                    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

    with col_a2:
        with st.expander("🗑️ 등록 선수 삭제", expanded=False):
            if not st.session_state.players.empty:
                player_options = st.session_state.players.apply(lambda row: f"{row['선수ID']} - {row['이름']} ({row['소속']})", axis=1).tolist()
                selected_del_player = st.selectbox("삭제할 선수를 선택하세요:", options=player_options)
                
                if st.button("❌ 선택한 선수 명단에서 삭제", type="secondary", use_container_width=True):
                    del_id = selected_del_player.split(" - ")[0]
                    del_name = selected_del_player.split(" - ")[1].split(" (")[0]
                    st.session_state.players = st.session_state.players[st.session_state.players["선수ID"] != del_id].reset_index(drop=True)
                    if del_name in st.session_state.detailed_hole_scores:
                        del st.session_state.detailed_hole_scores[del_name]
                    if del_name in st.session_state.detailed_hole_scores_multi:
                        del st.session_state.detailed_hole_scores_multi[del_name]
                    st.success(f"선수 [{selected_del_player}] 가 명단에서 삭제되었습니다.")
                    st.rerun()
            else:
                st.info("등록된 선수가 없습니다.")

    st.markdown("---")
    
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.subheader(f"📋 전체 선수 명단 (총 {len(st.session_state.players)}명 - 🏆 평균핸디 랭킹순 정렬)")
    with col_t2:
        ranked_players_df = get_player_ranking_df()
        excel_data = to_excel(ranked_players_df)
        st.download_button(
            label="📥 엑셀로 다운로드",
            data=excel_data,
            file_name=f"SGPGA_선수명단_{datetime.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    st.dataframe(ranked_players_df, use_container_width=True)

# =========================================================
# 메뉴 2: 단계별 종료 및 컷오프
# =========================================================
elif st.session_state.nav_menu == "단계별 종료 및 컷오프":
    st.header("🏁 예선전 종료 및 컷오프 탈락자 처리")
    st.info("💡 **안내**: 컷오프 타수 기준 탈락 처리는 **예선전**에만 적용됩니다. 8강전 이후부터는 **팀 매치 홀 스킨스(홀별 승패)** 결과로 진출이 자동 결정됩니다.")
    
    stage_score_key = "예선스코어"
    
    st.markdown("---")
    st.subheader(f"📌 [예선전] 스코어 현황 및 컷오프")
    
    active_players = st.session_state.players[
        st.session_state.players["최종진출단계"] == "예선전"
    ].copy()

    st.dataframe(active_players, use_container_width=True)

    with st.form("close_stage_form"):
        st.warning("⚠️ [예선전] 종료를 실행하면 컷오프 타수를 초과하거나 스코어가 미입력(0타)된 선수는 '종료(컷오프)' 처리되며, 기준 이하 선수는 '8강전' 진출 자격을 얻습니다.")
        cutoff_strokes = st.number_input("[예선전] 탈락 기준 타수 (예: 99타 초과 시 탈락)", min_value=50, max_value=150, value=99)
        
        submit_close = st.form_submit_button("🔒 [예선전] 공식 종료 및 본선 진출자 확정", type="primary")
        
        if submit_close:
            for idx, row in st.session_state.players.iterrows():
                if row["최종진출단계"] == "예선전" and row["경기상태"] == "진행중":
                    score = row.get(stage_score_key, 0)
                    if score > cutoff_strokes or score == 0:
                        st.session_state.players.at[idx, "경기상태"] = "종료(컷오프)"
                    else:
                        st.session_state.players.at[idx, "최종진출단계"] = "8강전"
                        st.session_state.players.at[idx, "경기상태"] = "진행중"
                        
            st.success(f"🎉 [예선전]이 종료되었습니다. {cutoff_strokes}타 이하 합격자는 [8강전] 진출이 확정되었습니다.")
            st.rerun()

# =========================================================
# 메뉴 3: 경기 일정 및 조 편성 관리
# =========================================================
elif st.session_state.nav_menu == "경기 일정 및 조 편성 관리":
    st.header("📅 경기 일정 및 조 편성 관리")
    st.caption("경기를 신규 생성하거나, 아래에서 **기존 일정을 선택하여 내용을 수정**할 수 있습니다.")
    
    tab1, tab2, tab3 = st.tabs(["📝 경기 일정 신규 생성", "✏️ 기존 경기 일정 수정", "⚡ 8강전 자동 팀 매칭 생성"])

    with tab1:
        st.subheader("➕ 경기 일정 수동 생성")
        
        col_cc, col_front, col_back = st.columns(3)
        selected_cc = col_cc.selectbox("골프장 선택", options=list(GOLF_COURSES.keys()), key="manual_golf_club")
        
        available_courses = GOLF_COURSES[selected_cc]
        selected_front_course = col_front.selectbox("전반 코스 선택", options=available_courses, key="manual_front_course")
        selected_back_course = col_back.selectbox("후반 코스 선택", options=available_courses, index=min(1, len(available_courses)-1), key="manual_back_course")
        
        m_course = f"{selected_cc} {selected_front_course}, {selected_back_course}코스"

        with st.form("manual_schedule_form", clear_on_submit=True):
            col_m1, col_m2 = st.columns(2)
            tour_options_list = [t["대회명"] for t in st.session_state.tournaments_list] if st.session_state.tournaments_list else ["제2회 SGPGA 오픈 챔피언십"]
            m_tour_name = col_m1.selectbox("대회 선택", options=tour_options_list)
            m_stage = col_m2.selectbox("경기구분", options=["예선전", "8강전", "4강전", "결승(FINAL)"], key="manual_stage_select")

            col_m5, col_m6 = st.columns(2)
            m_date = col_m5.date_input("날짜")
            m_time = col_m6.time_input("티오프시간", value=datetime.strptime("08:00", "%H:%M").time())

            selected_group_str = ""
            selected_players_str = ""

            if m_stage == "예선전":
                qual_group_options = [f"{i}조" for i in range(1, 9)]
                m_group = st.selectbox("조 선택", options=qual_group_options)
                
                all_player_names = st.session_state.players["이름"].tolist() if not st.session_state.players.empty else []
                selected_players = st.multiselect("선수 선택", options=all_player_names)
                selected_players_str = ", ".join(selected_players)
                selected_group_str = m_group

            elif m_stage == "8강전":
                b_matches = st.session_state.bracket.get("8강전", [])
                if b_matches:
                    b_options = [f"{m['매치ID']} ({m['팀1']} vs {m['팀2']})" for m in b_matches]
                    selected_b_match = st.selectbox("8강전 대진 매치 선택", options=b_options)
                    
                    match_id_sel = selected_b_match.split(" ")[0]
                    target_bm = next((m for m in b_matches if m["매치ID"] == match_id_sel), None)
                    if target_bm:
                        selected_group_str = f"{target_bm['매치ID']} ({target_bm['팀1']} vs {target_bm['팀2']})"
                        selected_players_str = f"{target_bm['선수1']} / {target_bm['선수2']}"
                else:
                    st.warning("등록된 8강전 대진표가 없습니다.")
                    selected_group_str = "8강전 매치 없음"

            elif m_stage == "4강전":
                sf_matches = st.session_state.bracket.get("4강전", [])
                if sf_matches:
                    sf_options = [f"{m['매치ID']} ({m['팀1']} vs {m['팀2']})" for m in sf_matches]
                    selected_sf_match = st.selectbox("4강전 대진 매치 선택", options=sf_options)
                    
                    match_id_sel = selected_sf_match.split(" ")[0]
                    target_sf = next((m for m in sf_matches if m["매치ID"] == match_id_sel), None)
                    if target_sf:
                        selected_group_str = f"{target_sf['매치ID']} ({target_sf['팀1']} vs {target_sf['팀2']})"
                        selected_players_str = f"{get_team_players_str(target_sf['팀1'])} / {get_team_players_str(target_sf['팀2'])}"
                else:
                    st.warning("4강전 대진이 생성되지 않았습니다.")
                    selected_group_str = "4강전 매치 없음"

            elif m_stage == "결승(FINAL)":
                f_matches = st.session_state.bracket.get("결승(FINAL)", [])
                if f_matches:
                    f_options = [f"{m['매치ID']} ({m['팀1']} vs {m['팀2']})" for m in f_matches]
                    selected_f_match = st.selectbox("결승(FINAL) 대진 매치 선택", options=f_options)
                    
                    match_id_sel = selected_f_match.split(" ")[0]
                    target_f = next((m for m in f_matches if m["매치ID"] == match_id_sel), None)
                    if target_f:
                        selected_group_str = f"{target_f['매치ID']} ({target_f['팀1']} vs {target_f['팀2']})"
                        selected_players_str = f"{get_team_players_str(target_f['팀1'])} / {get_team_players_str(target_f['팀2'])}"
                else:
                    st.warning("결승(FINAL) 대진이 생성되지 않았습니다.")
                    selected_group_str = "결승(FINAL) 매치 없음"

            st.text_input("출전 선수 자동 확인", value=selected_players_str, disabled=True)

            submit_manual = st.form_submit_button("➕ 경기 일정 생성 및 저장", type="primary", use_container_width=True)

            if submit_manual:
                if not m_tour_name or not selected_group_str or not selected_players_str or "매치 없음" in selected_group_str:
                    st.error("올바른 대회명, 조 및 선수 정보를 확인해 주세요.")
                else:
                    new_match_data = {
                        "대회명": m_tour_name,
                        "경기구분": m_stage,
                        "경기장 및 코스": m_course,
                        "날짜": str(m_date),
                        "조": selected_group_str,
                        "선수": selected_players_str,
                        "티오프시간": m_time.strftime("%H:%M")
                    }
                    st.session_state.matches = pd.concat([st.session_state.matches, pd.DataFrame([new_match_data])], ignore_index=True)
                    st.success(f"✅ [{m_stage}] {selected_group_str} 경기 일정이 등록되었습니다.")
                    st.rerun()

    with tab2:
        st.subheader("✏️ 등록된 경기 일정 선택 후 수정하기")
        
        if not st.session_state.matches.empty:
            match_edit_options = []
            for idx, r in st.session_state.matches.iterrows():
                match_edit_options.append(f"{idx}: [{r['경기구분']}] {r['대회명']} - 조: {r['조']} ({r['날짜']} {r['티오프시간']})")
            
            selected_edit_item = st.selectbox("수정할 경기를 선택하세요:", options=match_edit_options, key="edit_match_select_box")
            target_idx = int(selected_edit_item.split(":")[0])
            
            curr_match_row = st.session_state.matches.loc[target_idx]
            curr_course_str = str(curr_match_row.get("경기장 및 코스", ""))
            
            default_cc, default_front, default_back = parse_course_info(curr_course_str)

            cc_list = list(GOLF_COURSES.keys())
            
            tour_options_list = [t["대회명"] for t in st.session_state.tournaments_list] if st.session_state.tournaments_list else ["제2회 SGPGA 오픈 챔피언십"]
            curr_tour_name = curr_match_row["대회명"]
            tour_idx = tour_options_list.index(curr_tour_name) if curr_tour_name in tour_options_list else 0

            st.markdown("---")
            e_tour_name = st.selectbox("대회명 선택", options=tour_options_list, index=tour_idx, key=f"edit_tour_name_{target_idx}")
            
            stages = ["예선전", "8강전", "4강전", "결승(FINAL)"]
            stage_idx = stages.index(curr_match_row["경기구분"]) if curr_match_row["경기구분"] in stages else 0
            e_stage = st.selectbox("경기구분 수정", options=stages, index=stage_idx, key=f"edit_stage_{target_idx}")
            
            col_ec1, col_ec2, col_ec3 = st.columns(3)
            
            selected_edit_cc_key = f"edit_golf_club_{target_idx}"
            if selected_edit_cc_key not in st.session_state:
                st.session_state[selected_edit_cc_key] = default_cc if default_cc in cc_list else cc_list[0]
                
            edit_cc = col_ec1.selectbox("골프장 선택", options=cc_list, key=selected_edit_cc_key)
            
            edit_available_courses = GOLF_COURSES[edit_cc]
            
            f_key = f"edit_front_course_{target_idx}"
            b_key = f"edit_back_course_{target_idx}"
            
            if f_key not in st.session_state or st.session_state[f_key] not in edit_available_courses:
                st.session_state[f_key] = default_front if default_front in edit_available_courses else edit_available_courses[0]
                
            if b_key not in st.session_state or st.session_state[b_key] not in edit_available_courses:
                st.session_state[b_key] = default_back if default_back in edit_available_courses else (edit_available_courses[1] if len(edit_available_courses) > 1 else edit_available_courses[0])

            edit_front_course = col_ec2.selectbox("전반 코스 선택", options=edit_available_courses, key=f"edit_front_course_{target_idx}")
            edit_back_course = col_ec3.selectbox("후반 코스 선택", options=edit_available_courses, key=f"edit_back_course_{target_idx}")
            
            e_course = f"{edit_cc} {edit_front_course}, {edit_back_course}코스"
            
            try:
                default_date = datetime.strptime(str(curr_match_row["날짜"]), "%Y-%m-%d").date()
            except:
                default_date = datetime.today().date()
            
            try:
                default_time = datetime.strptime(str(curr_match_row["티오프시간"]), "%H:%M").time()
            except:
                default_time = datetime.strptime("08:00", "%H:%M").time()

            col_e1, col_e2 = st.columns(2)
            e_date = col_e1.date_input("날짜 수정", value=default_date, key=f"edit_date_{target_idx}")
            e_time = col_e2.time_input("티오프시간 수정", value=default_time, key=f"edit_time_{target_idx}")
            
            e_group = st.text_input("조 정보 수정", value=curr_match_row["조"], key=f"edit_group_{target_idx}")
            e_players = st.text_input("출전 선수 수정", value=curr_match_row["선수"], key=f"edit_players_{target_idx}")
            
            if st.button("💾 수정 사항 저장하기", type="primary", use_container_width=True):
                st.session_state.matches.loc[target_idx, "대회명"] = e_tour_name
                st.session_state.matches.loc[target_idx, "경기구분"] = e_stage
                st.session_state.matches.loc[target_idx, "경기장 및 코스"] = e_course
                st.session_state.matches.loc[target_idx, "날짜"] = str(e_date)
                st.session_state.matches.loc[target_idx, "조"] = e_group
                st.session_state.matches.loc[target_idx, "선수"] = e_players
                st.session_state.matches.loc[target_idx, "티오프시간"] = e_time.strftime("%H:%M")
                
                st.success("✅ 선택하신 경기 일정 정보가 성공적으로 수정·저장되었습니다!")
                st.rerun()
        else:
            st.info("수정할 경기 일정이 없습니다.")

    with tab3:
        st.subheader("🤝 8강전 자동 2인 1팀 매칭")
        
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        match_stage = col_s1.selectbox("진행할 경기 단계", options=["8강전"])
        auto_cc = col_s2.selectbox("골프장 선택", options=list(GOLF_COURSES.keys()), key="auto_cc")
        
        auto_available_courses = GOLF_COURSES[auto_cc]
        auto_front_c = col_s3.selectbox("전반 코스", options=auto_available_courses, key="auto_front_c")
        auto_back_c = col_s4.selectbox("후반 코스", options=auto_available_courses, index=min(1, len(auto_available_courses)-1), key="auto_back_c")
        
        match_course = f"{auto_cc} {auto_front_c}, {auto_back_c}코스"

        with st.form("auto_matching_form"):
            col_s5, col_s6 = st.columns(2)
            match_date = col_s5.date_input("경기 날짜", key="auto_date")
            time_interval = col_s6.number_input("매치 내 티오프 간격 (분)", min_value=5, max_value=30, value=10)

            start_time = st.time_input("첫 매치 티오프 시간", value=datetime.strptime("08:00", "%H:%M").time(), key="auto_time")
            shuffle_teams = st.checkbox("🎲 랜덤 조 추첨(Shuffle) 적용하기", value=False)
            
            submit_auto = st.form_submit_button("⚡ 자동 팀 매칭 & 토너먼트 대진표 생성", type="primary")
            
            if submit_auto:
                success, msg = auto_match_and_create_bracket(
                    stage_name=match_stage,
                    course_info=match_course,
                    match_date=match_date,
                    start_time_str=start_time.strftime("%H:%M"),
                    interval_minutes=time_interval,
                    shuffle=shuffle_teams
                )
                if success:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")

    if st.session_state.teams:
        st.markdown("---")
        st.subheader("👥 생성된 2인 1팀 명단")
        st.dataframe(pd.DataFrame(st.session_state.teams), use_container_width=True)

    st.markdown("---")
    st.subheader("📋 등록된 전체 경기 일정 및 조 명단")
    
    if not st.session_state.matches.empty:
        req_cols = ["대회명", "경기구분", "경기장 및 코스", "날짜", "조", "선수", "티오프시간"]
        display_matches = st.session_state.matches[[c for c in req_cols if c in st.session_state.matches.columns]]
        st.dataframe(display_matches, use_container_width=True)

        with st.expander("🗑️ 등록된 경기 일정 삭제"):
            match_del_options = display_matches.apply(
                lambda r: f"[{r['경기구분']}] {r['대회명']} - {r['조']} ({r['날짜']} {r['티오프시간']})", axis=1
            ).tolist()
            selected_del_match = st.selectbox("삭제할 경기를 선택하세요:", options=match_del_options)
            if st.button("❌ 선택 경기 삭제", type="secondary"):
                del_idx = match_del_options.index(selected_del_match)
                st.session_state.matches = st.session_state.matches.drop(st.session_state.matches.index[del_idx]).reset_index(drop=True)
                st.success("선택한 경기 일정이 삭제되었습니다.")
                st.rerun()
    else:
        st.info("등록된 경기 일정이 없습니다.")

# =========================================================
# 메뉴 4: 토너먼트 대진표 & 승패 관리
# =========================================================
elif st.session_state.nav_menu == "토너먼트 대진표 & 승패 관리":
    st.header("🌲 팀 매치 홀 스킨스(Match Play) 대진표")
    st.caption("각 홀별로 두 팀의 합산 스코어를 비교하여 더 많은 홀을 승리한 팀이 자동으로 다음 라운드에 진출합니다.")
    
    col_b1, col_b2, col_b3 = st.columns(3)
    
    with col_b1:
        st.subheader("🥊 8강전")
        b_matches = st.session_state.bracket.get("8강전", [])
        if not b_matches:
            st.info("구성된 8강전 대진표가 없습니다.")
        for m in b_matches:
            with st.container(border=True):
                st.markdown(f"**[{m['매치ID']}] {m['팀1']} vs {m['팀2']}**")
                match_row = st.session_state.matches[st.session_state.matches["조"].str.contains(m["매치ID"], na=False)]
                c_info = match_row["경기장 및 코스"].values[0] if not match_row.empty else ""

                t1_w, t2_w, is_done, status_str = calculate_match_skins(m["팀1"], m["팀2"], "8강전", c_info)
                
                if m["팀2"] == "부전승":
                    st.caption("🔵 부전승 처리")
                else:
                    st.caption(f"📊 스킨스 포인터: **{status_str}**")
                
                if m["승리팀"]:
                    st.success(f"🏆 승리/진출: **{m['승리팀']}**")
                else:
                    st.warning("⏳ 8강전 스코어 입력 대기 중")

    with col_b2:
        st.subheader("🥈 4강전")
        sf_matches = st.session_state.bracket.get("4강전", [])
        if not sf_matches:
            st.info("4강전 대진이 없습니다.")
        for m in sf_matches:
            with st.container(border=True):
                st.markdown(f"**[{m['매치ID']}] {m['팀1']} vs {m['팀2']}**")
                if "TBD" not in m["팀1"] and "TBD" not in m["팀2"]:
                    match_row = st.session_state.matches[st.session_state.matches["조"].str.contains(m["매치ID"], na=False)]
                    c_info = match_row["경기장 및 코스"].values[0] if not match_row.empty else ""

                    t1_w, t2_w, is_done, status_str = calculate_match_skins(m["팀1"], m["팀2"], "4강전", c_info)
                    st.caption(f"📊 스킨스 포인터: **{status_str}**")
                    if m["승리팀"]:
                        st.success(f"🏆 승리/진출: **{m['승리팀']}**")
                    else:
                        st.warning("⏳ 4강전 스코어 입력 대기 중")
                else:
                    st.caption("⏳ 8강전 승자 확정 및 대진 구성 대기 중")

    with col_b3:
        st.subheader("🥇 결승전(FINAL)")
        f_matches = st.session_state.bracket.get("결승(FINAL)", [])
        if not f_matches:
            st.info("결승(FINAL) 대진이 없습니다.")
        for m in f_matches:
            with st.container(border=True):
                st.markdown(f"**[{m['매치ID']}] {m['팀1']} vs {m['팀2']}**")
                if "TBD" not in m["팀1"] and "TBD" not in m["팀2"]:
                    match_row = st.session_state.matches[st.session_state.matches["조"].str.contains(m["매치ID"], na=False)]
                    c_info = match_row["경기장 및 코스"].values[0] if not match_row.empty else ""

                    t1_w, t2_w, is_done, status_str = calculate_match_skins(m["팀1"], m["팀2"], "결승", c_info)
                    st.caption(f"📊 스킨스 포인터: **{status_str}**")
                    if m["승리팀"]:
                        st.balloons()
                        st.success(f"🎉 **최종 우승팀: {m['승리팀']}** 🎉")
                    else:
                        st.warning("⏳ 결승(FINAL) 스코어 입력 대기 중")
                else:
                    st.caption("⏳ 4강전 승자 확정 및 대진 구성 대기 중")

# =========================================================
# 메뉴 5: 실시간 스코어 입력
# =========================================================
elif st.session_state.nav_menu == "실시간 스코어 입력":
    st.header("⛳ 18홀 대화형 골프장 스코어카드 (예선 다중 라운드 일괄 저장)")
    st.caption("경기를 선택한 후, 각 홀별 타수를 입력하고 하단의 [저장하기] 버튼을 누르면 총 스코어가 일괄 반영됩니다. (예선전은 여러 번 재참여 가능)")
    
    if st.session_state.matches.empty:
        st.warning("등록된 경기 일정이 없습니다.")
    else:
        match_options = st.session_state.matches.apply(
            lambda row: f"[{row['경기구분']}] {row['대회명']} - {row['조']} ({row.get('경기장 및 코스', '')}) | {row['날짜']} {row['티오프시간']} | 출전: {row['선수']}", axis=1
        ).tolist()
        
        selected_match_str = st.selectbox("📋 입력할 경기를 선택하세요:", options=match_options)
        selected_match_idx = match_options.index(selected_match_str)
        selected_match = st.session_state.matches.iloc[selected_match_idx]
        
        selected_stage = selected_match["경기구분"]
        course_str = selected_match.get("경기장 및 코스", "")
        players_raw = selected_match["선수"]
        
        match_players = []
        for segment in players_raw.split("/"):
            for name in segment.split(","):
                clean_name = name.strip()
                if clean_name and clean_name != "-" and clean_name not in match_players:
                    match_players.append(clean_name)

        if match_players:
            render_and_save_scorecard_section(match_players, selected_stage, course_str)
        else:
            st.info("해당 경기에 출전한 선수가 없습니다.")

# =========================================================
# 메뉴 6: 리더보드
# =========================================================
elif st.session_state.nav_menu == "리더보드":
    st.header("🏆 SGPGA 공식 리더보드")
    st.caption("대회 참가 선수들의 실시간 순위 및 스코어 현황판입니다.")
    
    if not st.session_state.players.empty:
        lb_df = get_player_ranking_df()
        st.dataframe(lb_df, use_container_width=True)
    else:
        st.info("등록된 선수 데이터가 없습니다.")

# =========================================================
# 메뉴 7: 대회 통계 리포트
# =========================================================
elif st.session_state.nav_menu == "📊 대회 통계 리포트":
    st.header("📊 대회 통계 및 분석 리포트")
    st.caption("전체 대회의 스코어 분포 및 선수 현황 통계를 시각적으로 확인합니다.")
    
    if not st.session_state.players.empty:
        df_stats = st.session_state.players.copy()
        
        col_st1, col_st2, col_st3 = st.columns(3)
        col_st1.metric("총 등록 선수", f"{len(df_stats)}명")
        
        active_cnt = len(df_stats[df_stats["경기상태"] == "진행중"])
        col_st2.metric("진행 중 선수", f"{active_cnt}명")
        
        avg_hcap = df_stats["핸디캡"].mean() if "핸디캡" in df_stats.columns else 0
        col_st3.metric("평균 핸디캡", f"{avg_hcap:.1f}")

        st.markdown("---")
        st.subheader("📈 소속별 선수 분포")
        if "소속" in df_stats.columns:
            affil_counts = df_stats["소속"].value_counts()
            st.bar_chart(affil_counts)
    else:
        st.info("통계를 생성할 데이터가 없습니다.")

# =========================================================
# 메뉴 8: 역대 대회 우승자 명예의 전당
# =========================================================
elif st.session_state.nav_menu == "🌟 역대 대회 우승자 명예의 전당":
    st.header("🌟 SGPGA 명예의 전당 (Hall of Fame)")
    st.caption("역대 SGPGA 오픈 챔피언십 우승자들의 영광스러운 기록입니다.")
    
    if st.session_state.hall_of_fame:
        hof_df = pd.DataFrame(st.session_state.hall_of_fame)
        st.dataframe(hof_df, use_container_width=True)
    else:
        st.info("아직 기록된 우승자 정보가 없습니다.")
