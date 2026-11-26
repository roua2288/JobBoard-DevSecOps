import sys
import secrets
import sqlite3
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app


@pytest.fixture
def client(tmp_path):
    database = tmp_path / "test.db"

    app = create_app({
        "TESTING": True,
        "SECRET_KEY": secrets.token_hex(32),
        "DB_ENGINE": "sqlite",
        "DATABASE": str(database),
        "UPLOAD_FOLDER": str(tmp_path / "cvs"),
        "LAB_MODE": False
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
        db.execute(
            "INSERT INTO jobs(title,company,location,contract,description,owner,status) VALUES(?,?,?,?,?,?,?)",
            ("OFFRE_PRIVEE_TEST", "Test", "Tunis", "PFE", "Test", 1, "pending")
        )

    return app.test_client()


def test_f1_search_handles_apostrophe(client):
    response = client.get("/", query_string={"q": "l'emploi"})
    assert response.status_code == 200


def test_f1_private_job_not_visible(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"OFFRE_PRIVEE_TEST" not in response.data


def test_f1_normal_search(client):
    response = client.get("/", query_string={"q": "DevSecOps"})
    assert response.status_code == 200
    assert b"DevSecOps" in response.data


def test_f2_html_escaped(client):
    response = client.get("/", query_string={"q": "<b>TestHTML</b>"})
    assert response.status_code == 200
    assert b"<b>TestHTML</b>" not in response.data


def test_f2_csp_enabled(client):
    response = client.get("/")
    assert "Content-Security-Policy" in response.headers
