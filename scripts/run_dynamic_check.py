"""One-shot local DAST target, seeded into a disposable directory and always stopped."""
import os
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as tmp:
    env={**os.environ,'SECRET_KEY':secrets.token_hex(32),'DEMO_PASSWORD':secrets.token_urlsafe(24),'DATABASE':str(Path(tmp)/'db.sqlite'),'UPLOAD_FOLDER':str(Path(tmp)/'cvs'),'LAB_MODE':'0'}
    subprocess.run([sys.executable,'-m','flask','--app','app','init-db'],env=env,check=True)
    subprocess.run([sys.executable,'-m','flask','--app','app','seed'],env=env,check=True)
    with open('/tmp/jobboard-dynamic.log','w') as log:
        server=subprocess.Popen([sys.executable,'-m','gunicorn','--bind','127.0.0.1:8000','app:create_app()'],env=env,stdout=log,stderr=log)
        try:subprocess.run([sys.executable,'scripts/dast.py'],env=env,check=True)
        finally:server.terminate();server.wait(timeout=10)
