#!/bin/bash
# 백엔드 서버 실행 스크립트 (백그라운드)

cd "$(dirname "$0")"

# 가상환경 활성화 (필요시)
if [ -d "../.venv" ]; then
  source ../.venv/bin/activate
fi

# 필수 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt

# 서버 실행 (백그라운드)
nohup uvicorn backend_code:app --host 0.0.0.0 --port 8080 --reload > server.log 2>&1 &
echo "서버가 백그라운드에서 실행 중입니다. (로그: backend/server.log)"

# 포트가 열릴 때까지 최대 30초 대기
for i in {1..30}; do
  if nc -z localhost 8080; then
    echo "서버가 정상적으로 실행되었습니다."
    break
  fi
  sleep 1
done
