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

# --- 회원가입/로그인 폼 ---
def login_signup_ui():
    st_lottie(load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_0yfsb3a1.json"), height=180, key="main_lottie")
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
                    toast("로그인 성공!", "🎉")
                    st.rerun()
                else:
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
                    toast("회원가입 성공! 로그인 해주세요.", "🎉")
                else:
                    st.error(r.json().get("detail", "회원가입 실패"))

# --- 내 정보/프로필 ---
def profile_ui():
    r = requests.get(f"{API_URL}/me", headers=api_headers())
    if r.status_code != 200:
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
        st.rerun()
    st.header("내 프로필 ✨")
    with st.form("profile_form"):
        name = st.text_input("이름", value=user['profile']['name'])
        bio = st.text_area("소개", value=user['profile']['bio'])
        img_file = st.file_uploader("프로필 이미지 (jpg/png, 1MB 이하)", type=["jpg", "png"])
        skills = []
        if user['role'] == "mentor":
            skills = st.text_input("기술 스택 (쉼표로 구분)", value=", ".join(user['profile'].get('skills', [])))
        submitted = st.form_submit_button("프로필 저장")
        if submitted:
            img_b64 = None
            if img_file:
                img_bytes = img_file.read()
                if len(img_bytes) > 1024*1024:
                    st.error("이미지는 1MB 이하만 업로드 가능")
                    return
                img_b64 = base64.b64encode(img_bytes).decode()
            payload = {
                "id": user["id"],
                "name": name,
                "role": user["role"],
                "bio": bio,
                "image": img_b64,
            }
            if user['role'] == "mentor":
                payload["skills"] = [s.strip() for s in skills.split(",") if s.strip()]
            r2 = requests.put(f"{API_URL}/profile", json=payload, headers=api_headers())
            if r2.status_code == 200:
                toast("프로필이 저장되었습니다!", "🎨")
                st.rerun()
            else:
                st.error(r2.json().get("detail", "프로필 저장 실패"))

# --- 멘토 리스트/매칭 ---
def mentor_list_ui():
    st.header("멘토 리스트 👩‍💻👨‍💻")
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
    cols = st.columns(2)
    for idx, m in enumerate(mentors):
        with cols[idx % 2]:
            st.markdown(f'''
                <div style="background: linear-gradient(90deg,#6C63FF,#48C6EF); padding:18px 16px 12px 16px; border-radius:18px; box-shadow:0 4px 16px #0002; margin-bottom:18px; color:white;">
                    <h4 style="margin-bottom:4px;">✨ {m['profile']['name']}</h4>
                    <span style="font-size:13px; opacity:0.8;">{', '.join(m['profile']['skills'])}</span>
                    <div style="margin:8px 0;">
                        <img src='{API_URL}/images/mentor/{m['id']}' width='90' style='border-radius:50%;border:3px solid #fff;box-shadow:0 2px 8px #0003;'>
                    </div>
                    <div style="font-size:14px;">{m['profile']['bio']}</div>
                </div>
            ''', unsafe_allow_html=True)
            if st.session_state.user['role'] == "mentee":
                if st.button(f"멘토링 요청하기 ({m['id']})", key=f"req_{m['id']}"):
                    with st.form(f"req_form_{m['id']}"):
                        msg = st.text_area("요청 메시지", key=f"msg_{m['id']}")
                        submit = st.form_submit_button("요청 보내기")
                        if submit:
                            payload = {
                                "mentorId": m['id'],
                                "menteeId": st.session_state.user['id'],
                                "message": msg,
                            }
                            r2 = requests.post(f"{API_URL}/match-requests", json=payload, headers=api_headers())
                            if r2.status_code == 200:
                                toast("요청이 전송되었습니다!", "📨")
                                st.rerun()
                            else:
                                st.error(r2.json().get("detail", "요청 실패"))

# --- 매칭 요청 목록 ---
def match_requests_ui():
    st.header("매칭 요청 현황 📨")
    user = st.session_state.user
    if user['role'] == "mentor":
        r = requests.get(f"{API_URL}/match-requests/incoming", headers=api_headers())
        st.subheader("들어온 요청")
        for req in r.json():
            st.info(f"멘티ID: {req['menteeId']} | 메시지: {req['message']} | 상태: {req['status']}")
            if req['status'] == "pending":
                c1, c2 = st.columns(2)
                if c1.button("수락", key=f"accept_{req['id']}"):
                    r2 = requests.put(f"{API_URL}/match-requests/{req['id']}/accept", headers=api_headers())
                    if r2.status_code == 200:
                        toast("요청을 수락했습니다!", "👍")
                        st.rerun()
                if c2.button("거절", key=f"reject_{req['id']}"):
                    r2 = requests.put(f"{API_URL}/match-requests/{req['id']}/reject", headers=api_headers())
                    if r2.status_code == 200:
                        toast("요청을 거절했습니다!", "❌")
                        st.rerun()
    else:
        r = requests.get(f"{API_URL}/match-requests/outgoing", headers=api_headers())
        st.subheader("보낸 요청")
        for req in r.json():
            st.info(f"멘토ID: {req['mentorId']} | 상태: {req['status']}")
            if req['status'] == "pending":
                if st.button("요청 취소", key=f"cancel_{req['id']}"):
                    r2 = requests.delete(f"{API_URL}/match-requests/{req['id']}", headers=api_headers())
                    if r2.status_code == 200:
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
    main()
