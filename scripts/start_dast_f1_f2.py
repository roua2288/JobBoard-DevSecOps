import secrets
import tempfile
import sqlite3
from pathlib import Path
from app import create_app

with tempfile.TemporaryDirectory(prefix="jobboard-dast-") as tmp:
    root = Path(tmp)
    database = root / "test.db"

    app = create_app({
        "SECRET_KEY": secrets.token_hex(32),
        "DB_ENGINE": "sqlite",
        "DATABASE": str(database),
        "UPLOAD_FOLDER": str(root / "cvs"),
        "LAB_MODE": False,
        "TESTING": True
    })

    result = app.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code == 0

    with sqlite3.connect(database) as db:
        db.execute(
            "INSERT INTO users(id,name,email,password,role) VALUES(?,?,?,?,?)",
            (1, "Test", "test@example.test", "unused", "recruiter")
        )

        db.execute(
            "INSERT INTO jobs(title,company,location,contract,description,owner,status) VALUES(?,?,?,?,?,?,?)",
            ("DevSecOps", "Test", "Tunis", "PFE", "Test", 1, "active")
        )

    app.run(host="127.0.0.1", port=8002, debug=False)
