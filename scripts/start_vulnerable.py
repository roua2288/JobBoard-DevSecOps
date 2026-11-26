"""Open the intentionally vulnerable JobBoard with disposable data."""

import argparse
import os
import secrets
import sqlite3
import tempfile
import webbrowser
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from werkzeug.serving import make_server

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker", action="store_true", help="Use the container network and skip browser launch.")
    args = parser.parse_args()
    host = "0.0.0.0" if args.docker else "127.0.0.1"
    with tempfile.TemporaryDirectory(prefix="jobboard-lab-") as directory:
        root = Path(directory)
        database = root / "lab.db"
        from app import create_app
        app = create_app({
            "SECRET_KEY": secrets.token_hex(32),
            "DB_ENGINE": "sqlite",
            "DATABASE": str(database),
            "UPLOAD_FOLDER": str(root / "cvs"),
            "SESSION_COOKIE_NAME": "jobboard_lab_session",
            "SESSION_COOKIE_SECURE": False,
            "LAB_MODE": False,
        })

        @app.context_processor
        def lab_banner():
            return {"lab": True}

        password = secrets.token_urlsafe(18)
        runner = app.test_cli_runner()
        with patch.dict(os.environ, {"ADMIN_PASSWORD": password, "DEMO_PASSWORD": password}):
            for command in ("init-db", "seed"):
                result = runner.invoke(args=[command])
                if result.exit_code:
                    raise RuntimeError(f"Initialisation du laboratoire échouée ({command}).") from result.exception

        with closing(sqlite3.connect(database)) as db, db:
            db.execute(
                "INSERT INTO jobs(title,company,location,contract,description,owner,status) "
                "SELECT 'OFFRE_FICTIVE_NON_PUBLIEE','Démo','Tunis','Stage','Offre privée du laboratoire',id,'pending' "
                "FROM users WHERE role='recruiter' ORDER BY id LIMIT 1"
            )

        with make_server(host, 8001, app) as server:
            url = "http://127.0.0.1:8001"
            print(f"JobBoard volontairement vulnérable · {url}", flush=True)
            print("Comptes fictifs : roua@example.test, ahmed@example.test, admin@gmail.com", flush=True)
            print(f"Mot de passe de démonstration : {password}", flush=True)
            print("Données temporaires. Ctrl+C pour arrêter.", flush=True)
            if not args.docker:
                webbrowser.open(url)
            server.serve_forever()


if __name__ == "__main__":
    main()
