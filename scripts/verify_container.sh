#!/usr/bin/env bash
set -euo pipefail
image=${1:-jobboard:41}
port=${2:-8000}
test "$(docker image inspect --format '{{.Config.User}}' "$image")" = '10001:10001'
export SECRET_KEY
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
container=$(docker run -d --read-only --tmpfs /tmp --cap-drop ALL \
  --security-opt no-new-privileges --env SECRET_KEY \
  --tmpfs /data:uid=10001,gid=10001,mode=0700 \
  -p "127.0.0.1::${port}" "$image")
trap 'docker rm -f "$container" >/dev/null' EXIT
address=$(docker port "$container" "$port/tcp")
python - "$address" <<'PY'
import sys, time, urllib.request
for attempt in range(30):
    try:
        with urllib.request.urlopen(f"http://{sys.argv[1]}/health", timeout=2) as response:
            if response.status == 200:
                print("HTTP 200 /health")
                break
    except OSError:
        pass
    time.sleep(1)
else:
    raise SystemExit("Conteneur indisponible")
PY
docker exec "$container" sh -ec 'test "$(id -u)" = 10001; test ! -e /srv/.git; test ! -e /srv/.env; test ! -e /srv/app/lab.py; id'
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.69.3 \
  image --scanners secret --exit-code 1 "$image"
