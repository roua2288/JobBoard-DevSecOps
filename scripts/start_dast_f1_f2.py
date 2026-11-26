import os
import secrets
import tempfile
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash
from app import create_app

with tempfile.TemporaryDirectory(prefix="jobboard-dast-") as tmp:
    root = Path(tmp)
    database = root / "test.db"
    password = os.environ["DAST_PASSWORD"]

    app = create_app({
        "SECRET_KEY": secrets.token_hex(32),
        "DB_ENGINE": "sqlite",
        "DATABASE": str(database),
        "UPLOAD_FOLDER": str(root / "cvs"),
        "LAB_MODE": False,
        "TESTING": False
    })

    result = app.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code == 0

    with sqlite3.connect(database) as db:
        db.execute(
            "INSERT INTO users(id,name,email,password,role) VALUES(?,?,?,?,?)",
            (1, "Test", "test@example.test",
             generate_password_hash(password), "recruiter")
        )

        for title, status in [
            ("DevSecOps", "active"),
            ("OFFRE_PRIVEE_TEST", "pending")
        ]:
            db.execute(
                "INSERT INTO jobs(title,company,location,contract,description,owner,status) VALUES(?,?,?,?,?,?,?)",
                (title, "Test", "Tunis", "PFE", "Test", 1, status)
            )

    app.run(host="127.0.0.1", port=8002, debug=False)
