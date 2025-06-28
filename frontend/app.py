"""
멘토-멘티 매칭 Streamlit UI (http://localhost:3000)
- 회원가입/로그인, 프로필, 멘토리스트, 매칭 요청 등 주요 기능 구현
- FastAPI 백엔드와 연동 (http://localhost:8080)
- 와우포인트: 컬러풀한 카드, 실시간 상태, 이미지 업로드, 토스트, 다크모드 등
"""
import streamlit as st
import requests
import base64
from streamlit_lottie import st_lottie
import json

API_URL = "http://localhost:8080/api"

st.set_page_config(page_title="멘토-멘티 매칭", page_icon="🤝", layout="wide", initial_sidebar_state="expanded")

# --- 세션 상태 ---
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

def api_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}

def toast(msg, icon="✅"):
    st.toast(msg, icon=icon)

def load_lottie_url(url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

def status_badge(status):
    color = {
        "pending": "#FFD600",
        "accepted": "#00C853",
        "rejected": "#D50000",
        "cancelled": "#757575"
    }.get(status, "#90A4AE")
    emoji = {
        "pending": "⏳",
        "accepted": "✅",
        "rejected": "❌",
        "cancelled": "🗑️"
    }.get(status, "🔖")
    label = {
        "pending": "대기중",
        "accepted": "수락됨",
        "rejected": "거절됨",
        "cancelled": "취소됨"
    }.get(status, status)
    return f"<span style='background:{color};color:#222;padding:2px 10px;border-radius:12px;font-size:13px;font-weight:600;display:inline-block;margin-left:8px;'>{emoji} {label}</span>"

def lottie_anim(url, height=120, key=None):
    anim = load_lottie_url(url)
    if anim:
        st_lottie(anim, height=height, key=key)
    else:
        st.markdown("<div style='color:#888;text-align:center;font-size:16px;'>⚠️ 애니메이션 로드 실패</div>", unsafe_allow_html=True)

# --- 회원가입/로그인 폼 ---
def login_signup_ui():
    lottie_anim("https://assets2.lottiefiles.com/packages/lf20_0yfsb3a1.json", height=180, key="main_lottie")
    st.title("멘토-멘티 매칭 서비스 🤝")
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    with tab1:
        with st.form("login_form"):
            email = st.text_input("이메일", key="login_email")
            pw = st.text_input("비밀번호", type="password", key="login_pw")
            submitted = st.form_submit_button("로그인")
            if submitted:
                data = {"username": email, "password": pw}
                r = requests.post(f"{API_URL}/login", data=data)
                if r.status_code == 200:
                    st.session_state.token = r.json()["token"]
                    lottie_anim("https://assets2.lottiefiles.com/packages/lf20_4kx2q32n.json", height=90, key="login_success")
                    toast("로그인 성공!", "🎉")
                    st.rerun()
                else:
                    lottie_anim("https://assets2.lottiefiles.com/packages/lf20_2ks3pjua.json", height=90, key="login_fail")
                    st.error(r.json().get("detail", "로그인 실패"))
    with tab2:
        with st.form("signup_form"):
            email = st.text_input("이메일", key="signup_email")
            pw = st.text_input("비밀번호", type="password", key="signup_pw")
            name = st.text_input("이름", key="signup_name")
            role = st.radio("역할", ["mentor", "mentee"], horizontal=True)
            submitted = st.form_submit_button("회원가입")
            if submitted:
                data = {"email": email, "password": pw, "name": name, "role": role}
                r = requests.post(f"{API_URL}/signup", json=data)
                if r.status_code == 201:
                    lottie_anim("https://assets2.lottiefiles.com/packages/lf20_4kx2q32n.json", height=90, key="signup_success")
                    toast("회원가입 성공! 로그인 해주세요.", "🎉")
                else:
                    lottie_anim("https://assets2.lottiefiles.com/packages/lf20_2ks3pjua.json", height=90, key="signup_fail")
                    st.error(r.json().get("detail", "회원가입 실패"))

# --- 내 정보/프로필 ---
def profile_ui():
    r = requests.get(f"{API_URL}/me", headers=api_headers())
    if r.status_code != 200:
        lottie_anim("https://assets2.lottiefiles.com/packages/lf20_2ks3pjua.json", height=90, key="auth_fail")
        st.error("인증 오류. 다시 로그인 해주세요.")
        st.session_state.token = None
        st.session_state.user = None
        st.rerun()
    user = r.json()
    st.session_state.user = user
    st.sidebar.markdown(f"#### 👤 {user['profile']['name']} ({user['role']})")
    st.sidebar.image(f"{API_URL}/images/{user['role']}/{user['id']}", width=100)
    st.sidebar.write(user['email'])
    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.token = None
        st.session_state.user = None
        lottie_anim("https://assets2.lottiefiles.com/packages/lf20_2ks3pjua.json", height=80, key="logout_anim")
        st.rerun()
    st.markdown('<div class="section-title">내 프로필 ✨</div>', unsafe_allow_html=True)
    with st.form("profile_form"):
        name = st.text_input("이름", value=user['profile']['name'])
        bio = st.text_area("소개", value=user['profile']['bio'])
        img_file = st.file_uploader("프로필 이미지 (jpg/png, 1MB 이하)", type=["jpg", "png"])
        if img_file:
            img_bytes = img_file.read()
            if len(img_bytes) > 1024*1024:
                lottie_anim("https://assets2.lottiefiles.com/packages/lf20_2ks3pjua.json", height=80, key="img_too_big")
                st.error("이미지는 1MB 이하만 업로드 가능")
                return
            img_b64 = base64.b64encode(img_bytes).decode()
            st.markdown(f'<img src="data:image/png;base64,{img_b64}" class="img-preview">', unsafe_allow_html=True)
        else:
            st.markdown(f'<img src="{API_URL}/images/{user["role"]}/{user["id"]}" class="img-preview">', unsafe_allow_html=True)
        skills = []
        if user['role'] == "mentor":
            skills = st.text_input("기술 스택 (쉼표로 구분)", value=", ".join(user['profile'].get('skills', [])))
        submitted = st.form_submit_button("프로필 저장")
        if submitted:
            payload = {
                "id": user["id"],
                "name": name,
                "role": user["role"],
                "bio": bio,
                "image": img_b64 if img_file else None,
            }
            if user['role'] == "mentor":
                payload["skills"] = [s.strip() for s in skills.split(",") if s.strip()]
            r2 = requests.put(f"{API_URL}/profile", json=payload, headers=api_headers())
            if r2.status_code == 200:
                lottie_anim("https://assets2.lottiefiles.com/packages/lf20_4kx2q32n.json", height=80, key="profile_save")
                toast("프로필이 저장되었습니다!", "🎨")
                st.rerun()
            else:
                lottie_anim("https://assets2.lottiefiles.com/packages/lf20_2ks3pjua.json", height=80, key="profile_fail")
                st.error(r2.json().get("detail", "프로필 저장 실패"))

# --- 멘토 리스트/매칭 ---
def mentor_list_ui():
    st.markdown('<div class="section-title">멘토 리스트 👩‍💻👨‍💻</div>', unsafe_allow_html=True)
    skill = st.text_input("기술 스택으로 검색", key="search_skill")
    order = st.radio("정렬 기준", ["id", "name", "skill"], horizontal=True)
    params = {}
    if skill:
        params["skill"] = skill
    if order:
        params["order_by"] = order
    r = requests.get(f"{API_URL}/mentors", headers=api_headers(), params=params)
    if r.status_code != 200:
        st.error("멘토 리스트를 불러올 수 없습니다.")
        return
    mentors = r.json()
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    cols = st.columns(2)
    # --- 멘토링 요청 폼 상태 관리 ---
    if 'requesting_mentor_id' not in st.session_state:
        st.session_state.requesting_mentor_id = None
    for idx, m in enumerate(mentors):
        with cols[idx % 2]:
            st.markdown(f'''
                <div class="mentor-card" style="background: linear-gradient(90deg,#6C63FF,#48C6EF); padding:18px 16px 12px 16px; border-radius:18px; box-shadow:0 4px 16px #0002; margin-bottom:18px; color:white; position:relative;">
                    <h4 style="margin-bottom:4px;">✨ {m['profile']['name']}</h4>
                    <span style="font-size:13px; opacity:0.8;">{', '.join(m['profile']['skills'])}</span>
                    <div style="margin:8px 0;">
                        <img src='{API_URL}/images/mentor/{m['id']}' width='90' class='img-preview'>
                    </div>
                    <div style="font-size:14px;">{m['profile']['bio']}</div>
                </div>
            ''', unsafe_allow_html=True)
            if st.session_state.user['role'] == "mentee":
                # 버튼을 누르면 해당 멘토에만 폼이 보이도록 상태 저장
                if st.session_state.requesting_mentor_id == m['id']:
                    with st.form(f"req_form_{m['id']}"):
                        msg = st.text_area("요청 메시지", key=f"msg_{m['id']}")
                        submit = st.form_submit_button("요청 보내기")
                        if submit:
                            payload = {
                                "mentorId": m['id'],
                                "menteeId": st.session_state.user['id'],
                                "message": msg,
                            }
                            st.write(f"멘토ID: {m['id']}, 멘티ID: {st.session_state.user['id']}")  # 로그창에 출력
                            r2 = requests.post(f"{API_URL}/match-requests", json=payload, headers=api_headers())
                            if r2.status_code == 200:
                                # 화려한 안내: Lottie + Balloon + 컬러 메시지
                                lottie_anim("https://assets2.lottiefiles.com/packages/lf20_4kx2q32n.json", height=120, key=f"req_success_{m['id']}")
                                st.markdown('<div style="background:linear-gradient(90deg,#6C63FF,#48C6EF);color:#fff;padding:18px 20px 14px 20px;border-radius:18px;font-size:1.2rem;font-weight:700;box-shadow:0 4px 16px #0002;margin-bottom:12px;display:flex;align-items:center;gap:12px;">🎉 <span>멘토링 요청이 <span style="color:#FFD600;">성공적으로</span> 전송되었습니다!</span> 🚀</div>', unsafe_allow_html=True)
                                st.balloons()
                                toast("요청이 전송되었습니다!", "📨")
                                st.session_state.requesting_mentor_id = None
                                st.rerun()
                            else:
                                st.error(r2.json().get("detail", "요청 실패"))
                else:
                    if st.button(f"멘토링 요청하기 ({m['id']})", key=f"req_{m['id']}", help="멘토에게 매칭 요청을 보냅니다."):
                        st.session_state.requesting_mentor_id = m['id']
                        st.rerun()

# --- 매칭 요청 목록 ---
def match_requests_ui():
    st.header("매칭 요청 현황 📨")
    user = st.session_state.user
    if user['role'] == "mentor":
        r = requests.get(f"{API_URL}/match-requests/incoming", headers=api_headers())
        st.subheader("들어온 요청")
        if r.status_code != 200:
            st.error("매칭 요청을 불러오지 못했습니다.")
            st.write(r.text)
            return
        data = r.json()
        st.write(data)  # 실제 응답 확인용
        if not data:
            st.info("들어온 매칭 요청이 없습니다.")
        for req in data:
            st.markdown(f"멘티ID: <b>{req['menteeId']}</b> | 메시지: {req['message']} | 상태: {status_badge(req['status'])}", unsafe_allow_html=True)
            if req['status'] == "pending":
                c1, c2 = st.columns(2)
                if c1.button("수락", key=f"accept_{req['id']}"):
                    r2 = requests.put(f"{API_URL}/match-requests/{req['id']}/accept", headers=api_headers())
                    if r2.status_code == 200:
                        lottie_anim("https://assets2.lottiefiles.com/packages/lf20_4kx2q32n.json", height=70, key=f"accept_anim_{req['id']}")
                        toast("요청을 수락했습니다!", "👍")
                        st.balloons()
                        st.rerun()
                if c2.button("거절", key=f"reject_{req['id']}"):
                    r2 = requests.put(f"{API_URL}/match-requests/{req['id']}/reject", headers=api_headers())
                    if r2.status_code == 200:
                        lottie_anim("https://assets2.lottiefiles.com/packages/lf20_2ks3pjua.json", height=70, key=f"reject_anim_{req['id']}")
                        toast("요청을 거절했습니다!", "❌")
                        st.snow()
                        st.rerun()
    else:
        r = requests.get(f"{API_URL}/match-requests/outgoing", headers=api_headers())
        st.subheader("보낸 요청")
        if r.status_code != 200:
            st.error("매칭 요청을 불러오지 못했습니다.")
            st.write(r.text)
            return
        data = r.json()
        st.write(data)  # 실제 응답 확인용
        if not data:
            st.info("보낸 매칭 요청이 없습니다.")
        for req in data:
            st.markdown(f"멘토ID: <b>{req['mentorId']}</b> | 상태: {status_badge(req['status'])}", unsafe_allow_html=True)
            # 상태별 화려한 안내 메시지
            if req['status'] == "accepted":
                lottie_anim("https://assets2.lottiefiles.com/packages/lf20_4kx2q32n.json", height=90, key=f"accepted_{req['id']}")
                st.markdown('<div style="background:linear-gradient(90deg,#00C853,#48C6EF);color:#fff;padding:14px 18px 12px 18px;border-radius:16px;font-size:1.1rem;font-weight:600;box-shadow:0 2px 8px #0002;margin-bottom:10px;display:flex;align-items:center;gap:10px;">🎊 <span>멘토링 매칭이 <span style="color:#FFD600;">성공</span>했습니다! 멘토와 함께 멋진 경험을 시작해보세요 🙌</span></div>', unsafe_allow_html=True)
                st.balloons()
            elif req['status'] == "rejected":
                lottie_anim("https://assets2.lottiefiles.com/packages/lf20_2ks3pjua.json", height=80, key=f"rejected_{req['id']}")
                st.markdown('<div style="background:linear-gradient(90deg,#D50000,#757575);color:#fff;padding:14px 18px 12px 18px;border-radius:16px;font-size:1.05rem;font-weight:500;box-shadow:0 2px 8px #0002;margin-bottom:10px;display:flex;align-items:center;gap:10px;">❌ <span>아쉽게도 매칭이 거절되었습니다.<br>다른 멘토에게 다시 도전해보세요!</span></div>', unsafe_allow_html=True)
                st.snow()
            elif req['status'] == "cancelled":
                lottie_anim("https://assets2.lottiefiles.com/packages/lf20_3rwasyjy.json", height=70, key=f"cancelled_{req['id']}")
                st.markdown('<div style="background:linear-gradient(90deg,#757575,#90A4AE);color:#fff;padding:12px 16px 10px 16px;border-radius:14px;font-size:1.02rem;font-weight:500;box-shadow:0 1px 4px #0001;margin-bottom:8px;display:flex;align-items:center;gap:8px;">🗑️ <span>매칭 요청이 취소되었습니다.</span></div>', unsafe_allow_html=True)
            if req['status'] == "pending":
                if st.button("요청 취소", key=f"cancel_{req['id']}"):
                    r2 = requests.delete(f"{API_URL}/match-requests/{req['id']}", headers=api_headers())
                    if r2.status_code == 200:
                        lottie_anim("https://assets2.lottiefiles.com/packages/lf20_3rwasyjy.json", height=80, key=f"cancel_anim_{req['id']}")
                        toast("요청을 취소했습니다!", "🗑️")
                        st.rerun()

# --- 메인 라우팅 ---
def main():
    if not st.session_state.token:
        login_signup_ui()
        return
    profile_ui()
    menu = ["멘토 리스트", "매칭 요청 현황"]
    if st.session_state.user['role'] == "mentor":
        menu = ["매칭 요청 현황"]
    choice = st.sidebar.radio("메뉴", menu)
    if choice == "멘토 리스트":
        mentor_list_ui()
    if choice == "매칭 요청 현황":
        match_requests_ui()

if __name__ == "__main__":
    # --- 글로벌 스타일: 카드/버튼/섹션 구분 CSS ---
    st.markdown('''
        <style>
        /* 전체 배경: 감성 멀티 컬러 그라데이션 (보라-파랑-민트-노랑) */
        body, .stApp {
            background: linear-gradient(135deg, #6C63FF 0%, #48C6EF 40%, #43E97B 70%, #FFD600 100%) !important;
            background-attachment: fixed !important;
        }
        /* 카드/폼 완전 투명+블러 효과, 그림자 최소화, 경계 제거 */
        .mentor-card, .stForm, .stTextInput, .stTextArea, .stRadio, .stButton, .stSelectbox, .stFileUploader, .stSidebar, .stAlert, .stMarkdown, .stToast {
            background: rgba(255,255,255,0.32) !important;
            backdrop-filter: blur(10px) saturate(1.2);
            box-shadow: 0 2px 8px #0001 !important;
            border: none !important;
        }
        .mentor-card, .stForm, .stTextInput, .stTextArea, .stRadio, .stButton, .stSelectbox, .stFileUploader, .stSidebar, .stAlert, .stMarkdown, .stToast {
            border-radius: 22px !important;
        }
        /* 기존 스타일 유지 */
        .mentor-card {transition: transform 0.18s cubic-bezier(.4,2,.6,1), box-shadow 0.18s;}
        .mentor-card:hover {transform: scale(1.035) translateY(-2px); box-shadow:0 8px 32px #0002; z-index:2;}
        .pretty-btn {background: linear-gradient(90deg,#6C63FF,#48C6EF); color:#fff; border:none; border-radius:16px; padding:8px 22px; font-weight:600; font-size:16px; box-shadow:0 2px 8px #0002; cursor:pointer; transition:background 0.2s,box-shadow 0.2s; margin:6px 0;}
        .pretty-btn:hover {background: linear-gradient(90deg,#48C6EF,#6C63FF); box-shadow:0 4px 16px #0003;}
        .img-preview {border-radius:50%; border:3px solid #fff; box-shadow:0 2px 8px #0003; width:90px; margin:8px 0;}
        .section-title {font-size:1.3rem; font-weight:700; margin:18px 0 10px 0; letter-spacing:-1px; color:#6C63FF;}
        .divider {height:1px; background:linear-gradient(90deg,#6C63FF22,#48C6EF44,#6C63FF22); border:none; margin:18px 0 12px 0;}
        </style>
    ''', unsafe_allow_html=True)
    main()
