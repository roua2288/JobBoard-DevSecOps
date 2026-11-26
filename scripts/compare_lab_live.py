"""Replay the eight initial attacks on an isolated, ephemeral localhost HTTP server."""
import io
import os
import re
import secrets
import sqlite3
import sys
import tempfile
import threading
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import requests
from flask import Flask
from pypdf import PdfWriter
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import create_app

SQL_PAYLOAD = "' OR 1=1 -- "
XSS_PAYLOAD = "<script>document.body.dataset.xss=1</script>"
DRAFT = "OFFRE_FICTIVE_NON_PUBLIEE"
PROFILE_MARKER = "Nom modifie sans consentement"
FAKE_PDF = b"<html>Fichier fictif de demonstration</html>"


def replay(factory, directory, vulnerable):
    database = directory / "test.db"
    password = secrets.token_urlsafe(24)
    app = factory({
        "TESTING": True, "DB_ENGINE": "sqlite", "DATABASE": str(database),
        "UPLOAD_FOLDER": str(directory / "cvs"), "SECRET_KEY": secrets.token_hex(32),
        "LAB_MODE": False, "SESSION_COOKIE_SECURE": False,
    })
    with patch.dict(os.environ, {"DEMO_PASSWORD": password, "ADMIN_PASSWORD": password}):
        for command in ["init-db", "seed"]:
            result = app.test_cli_runner().invoke(args=[command])
            if result.exit_code:
                raise RuntimeError(f"Initialisation échouée: {command}") from result.exception
    with closing(sqlite3.connect(database)) as db, db:
        admin_id = db.execute("SELECT id FROM users WHERE role='admin'").fetchone()[0]
        db.execute(
            "INSERT INTO jobs(title,company,location,contract,description,owner,status) "
            "SELECT ?, 'Fictive', 'Tunis', 'Stage', 'Test', id, 'pending' FROM users WHERE role='recruiter' LIMIT 1",
            (DRAFT,),
        )
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def get(client, path, **kwargs):
        return client.get(base + path, timeout=10, **kwargs)

    def post(client, path, fields, files=None):
        form = get(client, "/login")
        csrf = re.search(r'name="csrf" value="([^"]+)"', form.text).group(1)
        return client.post(base + path, data={**fields, "csrf": csrf}, files=files,
                           timeout=10, allow_redirects=False)

    def login(client, email):
        return post(client, "/login", {"email": email, "password": password})

    try:
        with requests.Session() as candidate, requests.Session() as stranger, requests.Session() as attacker, requests.Session() as forged:
            for client in (candidate, stranger, attacker, forged):
                client.trust_env = False
            assert login(candidate, "roua@example.test").status_code == 302
            assert login(stranger, "other@example.test").status_code == 302
            content = io.BytesIO()
            pdf = PdfWriter()
            pdf.add_blank_page(width=200, height=200)
            pdf.write(content)
            assert post(candidate, "/cv/upload", {}, {"cv": ("cv.pdf", content.getvalue())}).status_code == 302
            dashboard = get(candidate, "/dashboard")
            cv = re.search(r'href="/cv/(\d+)"', dashboard.text).group(1)

            sql = get(candidate, "/", params={"q": SQL_PAYLOAD})
            assert sql.status_code == 200
            assert (DRAFT in sql.text) == vulnerable

            # Separate payload avoids overlapping the SQLi and XSS demonstrations.
            xss_payload = XSS_PAYLOAD
            xss = get(candidate, "/", params={"q": xss_payload})
            assert xss.status_code == 200
            assert (xss_payload in xss.text) == vulnerable
            assert ("Content-Security-Policy" not in xss.headers) == vulnerable
            if not vulnerable:
                assert "&lt;script&gt;" in xss.text

            idor = get(stranger, f"/cv/{cv}")
            assert idor.status_code == (200 if vulnerable else 403)
            assert (idor.content.startswith(b"%PDF-")) == vulnerable

            email = "attacker@example.test"
            signup = post(attacker, "/register", {
                "name": "Test fictif", "email": email, "password": password,
                "confirm": password, "role": "admin",
            })
            assert signup.status_code == (302 if vulnerable else 400)
            assert login(attacker, email).status_code == (302 if vulnerable else 401)
            metrics = get(attacker, "/metrics", allow_redirects=False)
            assert metrics.status_code == (200 if vulnerable else 302)

            # A different localhost port is a different origin on the same site.
            profile = stranger.post(
                base + "/profile",
                data={"name": PROFILE_MARKER, "email": "other@example.test"},
                headers={"Origin": "http://127.0.0.1:1"},
                timeout=10, allow_redirects=False,
            )
            profile_changed = PROFILE_MARKER in get(stranger, "/profile").text
            assert profile.status_code == (302 if vulnerable else 400)
            assert profile_changed == vulnerable

            upload_dir = directory / "cvs"
            before_upload = set(upload_dir.iterdir())
            upload = post(candidate, "/cv/upload", {}, {"cv": ("faux.pdf", FAKE_PDF)})
            new_files = set(upload_dir.iterdir()) - before_upload
            assert upload.status_code == (302 if vulnerable else 400)
            assert len(new_files) == int(vulnerable)
            assert all(path.read_bytes() == FAKE_PDF for path in new_files)

            exposed_key = get(forged, "/lab/session-key")
            assert exposed_key.status_code == (200 if vulnerable else 404)
            signing_app = Flask("lab_signer")
            signing_app.secret_key = exposed_key.json()["signing_key"] if vulnerable else secrets.token_hex(32)
            signer = signing_app.session_interface.get_signing_serializer(signing_app)
            forged.cookies.clear()
            forged.cookies.set(app.config["SESSION_COOKIE_NAME"], signer.dumps({"uid": admin_id}))
            forged_metrics = get(forged, "/metrics", allow_redirects=False)
            assert forged_metrics.status_code == (200 if vulnerable else 302)

            # Reset this IP's counter through a legitimate login before testing the limit.
            assert login(candidate, "roua@example.test").status_code == 302
            for _ in range(5):
                invalid = post(attacker, "/login", {"email": "admin@gmail.com", "password": "wrong"})
                assert invalid.status_code == 401
            sixth = login(attacker, "admin@gmail.com")
            assert sixth.status_code == (302 if vulnerable else 429)

            label = "AVANT" if vulnerable else "APRÈS"
            print(f"{label} F1 SQLi offre privée visible={DRAFT in sql.text}")
            print(f"{label} F2 XSS script brut={xss_payload in xss.text}, CSP={'Content-Security-Policy' in xss.headers}")
            print(f"{label} F3 IDOR HTTP {idor.status_code}")
            print(f"{label} F4 rôle admin inscription HTTP {signup.status_code}, métriques HTTP {metrics.status_code}")
            print(f"{label} F5 CSRF HTTP {profile.status_code}, profil modifié={profile_changed}")
            print(f"{label} F6 limitation connexion sixième essai HTTP {sixth.status_code}")
            print(f"{label} F7 faux PDF HTTP {upload.status_code}, fichiers enregistrés={len(new_files)}")
            print(f"{label} F8 fuite de clé HTTP {exposed_key.status_code}, session forgée métriques HTTP {forged_metrics.status_code}")
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="jobboard-audit-") as tmp:
        root = Path(tmp)
        replay(create_app, root, vulnerable=True)
    print("OK: 8 failles reproduites sur HTTP local.")
