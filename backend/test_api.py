import requests
import base64

API = "http://localhost:8080/api"

MENTOR_EMAIL = "mentor_test@test.com"
MENTEE_EMAIL = "mentee_test@test.com"
PASSWORD = "test1234"


def test_signup():
    # 멘토 회원가입
    r = requests.post(f"{API}/signup", json={
        "email": MENTOR_EMAIL,
        "password": PASSWORD,
        "name": "테스트멘토",
        "role": "mentor"
    })
    assert r.status_code in (201, 400)
    # 멘티 회원가입
    r = requests.post(f"{API}/signup", json={
        "email": MENTEE_EMAIL,
        "password": PASSWORD,
        "name": "테스트멘티",
        "role": "mentee"
    })
    assert r.status_code in (201, 400)

def test_login():
    # 멘토 로그인
    r = requests.post(f"{API}/login", data={"username": MENTOR_EMAIL, "password": PASSWORD})
    assert r.status_code == 200
    mentor_token = r.json()["token"]
    # 멘티 로그인
    r = requests.post(f"{API}/login", data={"username": MENTEE_EMAIL, "password": PASSWORD})
    assert r.status_code == 200
    mentee_token = r.json()["token"]
    return mentor_token, mentee_token

def get_user_id(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{API}/me", headers=headers)
    assert r.status_code == 200
    return r.json()["id"]

def test_profile_update(token, role, user_id):
    # 프로필 수정 (멘토/멘티)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "id": user_id,
        "name": "수정된이름",
        "role": role,
        "bio": "자기소개 수정",
        "image": None,
    }
    if role == "mentor":
        payload["skills"] = ["python", "fastapi"]
    r = requests.put(f"{API}/profile", json=payload, headers=headers)
    assert r.status_code == 200

def test_mentor_list(mentee_token):
    headers = {"Authorization": f"Bearer {mentee_token}"}
    r = requests.get(f"{API}/mentors", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    return r.json()

def test_match_request(mentee_token, mentor_id, mentee_id):
    headers = {"Authorization": f"Bearer {mentee_token}"}
    r = requests.post(f"{API}/match-requests", json={
        "mentorId": mentor_id,
        "menteeId": mentee_id,
        "message": "멘토링 요청합니다!"
    }, headers=headers)
    assert r.status_code in (200, 400)

def test_incoming_outgoing(mentor_token, mentee_token):
    # 멘토: 들어온 요청
    r = requests.get(f"{API}/match-requests/incoming", headers={"Authorization": f"Bearer {mentor_token}"})
    assert r.status_code == 200
    # 멘티: 보낸 요청
    r = requests.get(f"{API}/match-requests/outgoing", headers={"Authorization": f"Bearer {mentee_token}"})
    assert r.status_code == 200

def test_profile_image(token, role, user_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{API}/images/{role}/{user_id}", headers=headers, allow_redirects=False)
    assert r.status_code in (200, 307, 302)

def run_all():
    test_signup()
    mentor_token, mentee_token = test_login()
    mentor_id = get_user_id(mentor_token)
    mentee_id = get_user_id(mentee_token)
    # 멘토/멘티 프로필 수정
    test_profile_update(mentor_token, "mentor", mentor_id)
    test_profile_update(mentee_token, "mentee", mentee_id)
    # 멘토 리스트
    mentors = test_mentor_list(mentee_token)
    assert len(mentors) > 0
    # 매칭 요청
    test_match_request(mentee_token, mentor_id, mentee_id)
    # 매칭 요청 목록
    test_incoming_outgoing(mentor_token, mentee_token)
    # 프로필 이미지(멘토/멘티)
    test_profile_image(mentor_token, "mentor", mentor_id)
    test_profile_image(mentee_token, "mentee", mentee_id)
    print("✅ 모든 주요 API 테스트 통과!")

if __name__ == "__main__":
    run_all()
