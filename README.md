# 천하제일 입코딩 대회 2025 - 멘토-멘티 매칭 앱

<div align="center">
  <img src="./images/hero.png" width="500" alt="천하제일입코딩대회 이미지">
  <p style="font-size: 16pt; font-weight: bold;"><strong>제 1회 천하제일 입코딩대회 - 멘토-멘티 매칭 앱</strong></p>
</div>

---

## 프로젝트 개요

이 프로젝트는 천하제일 입코딩 대회 2025의 공식 과제인 **멘토-멘티 매칭 웹앱**입니다. FastAPI(백엔드)와 Streamlit(프론트엔드) 기반으로, 멘토와 멘티가 회원가입/로그인, 프로필 관리, 멘토 리스트 조회, 매칭 요청 등 모든 기능을 웹에서 사용할 수 있습니다.

- **백엔드:** FastAPI, SQLite, JWT 인증, RESTful API
- **프론트엔드:** Streamlit, Lottie, 커스텀 CSS, 반응형 UI
- **API 명세:** [docs/mentor-mentee-api-spec.md](./docs/mentor-mentee-api-spec.md)

---

## 폴더 구조

```
backend/    # FastAPI 백엔드 서버
frontend/   # Streamlit 프론트엔드 앱
  └─ app.py
  └─ .streamlit/config.toml
  └─ requirements.txt
  └─ run_frontend.sh
  ...
docs/       # 요구사항, 명세, 사용자 스토리 등 문서
```

---

## 실행 방법

### 1. 백엔드(FastAPI) 실행

```bash
cd backend
bash run_backend.sh
```
- 서버가 정상적으로 실행되면 `http://localhost:8080`에서 API를 확인할 수 있습니다.
- OpenAPI 문서: [http://localhost:8080/swagger-ui](http://localhost:8080/swagger-ui)
- 서버 로그: `backend/server.log`

### 2. 프론트엔드(Streamlit) 실행

```bash
cd frontend
bash run_frontend.sh
```
- 앱이 실행되면 [http://localhost:3000](http://localhost:3000)에서 웹 UI를 사용할 수 있습니다.

### 3. (선택) 더미 멘토 데이터 추가

```bash
cd backend
python add_dummy_mentors.py
```

---

## 주요 기능

- 회원가입/로그인 (JWT 인증)
- 내 프로필/이미지 관리
- 멘토 리스트/검색/정렬
- 멘토-멘티 매칭 요청/수락/거절/취소
- 실시간 상태, 토스트/애니메이션, 반응형 UI
- API 명세 100% 준수, 자동화된 실행 스크립트 제공

---

## 참고 문서
- [요구사항](./docs/mentor-mentee-app-requirements.md)
- [사용자 스토리](./docs/mentor-mentee-app-user-stories.md)
- [API 명세](./docs/mentor-mentee-api-spec.md)
- [OpenAPI 문서](./docs/openapi.yaml)
- [평가 방식](./mentor-mentee-app-assessment.md)

---

## 문의 및 이슈
- 앱 실행/개발 관련 문의는 GitHub Issues 또는 대회 공식 채널을 이용해 주세요.

---

<div align="center">
  <img src="./images/submit.png" width="150" alt="앱 제출">
  <br><br>
  <b>앱 제출 마감: 2025년 6월 28일 17시</b>
</div>

