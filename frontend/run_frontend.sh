#!/bin/bash
# 프론트엔드 Streamlit 실행 스크립트 (백그라운드)

cd "$(dirname "$0")"

# 가상환경 활성화 (필요시)
if [ -d "../.venv" ]; then
  source ../.venv/bin/activate
fi

# 필수 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt

# 서버 실행 (백그라운드)
nohup streamlit run app.py --server.port 3000 > frontend.log 2>&1 &
echo "Streamlit 프론트엔드가 백그라운드에서 실행 중입니다. (로그: frontend/frontend.log)"
