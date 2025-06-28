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

# 포트가 열릴 때까지 최대 30초 대기
for i in {1..15}; do
  if nc -z localhost 8080; then
    echo "서버가 정상적으로 실행되었습니다."
    exit 0
  fi
  sleep 1
done

# 실패 시 로그 출력
echo "[에러] 서버가 30초 내에 실행되지 않았습니다. server.log 마지막 20줄:"
tail -20 server.log
exit 1
