import os
import requests
from html.parser import HTMLParser

BASE = "http://127.0.0.1:8002"


class TokenParser(HTMLParser):
    token = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("name") == "csrf":
            self.token = attrs.get("value")


with requests.Session() as client:
    page = client.get(BASE + "/login", timeout=10)
    page.raise_for_status()

    parser = TokenParser()
    parser.feed(page.text)
    assert parser.token, "CSRF token missing"

    response = client.post(
        BASE + "/login",
        data={
            "email": "test@example.test",
            "password": os.environ["DAST_PASSWORD"],
            "csrf": parser.token
        },
        allow_redirects=False,
        timeout=10
    )

    assert response.status_code == 302

    dashboard = client.get(
        BASE + "/dashboard",
        allow_redirects=False,
        timeout=10
    )
    assert dashboard.status_code == 200
    print("PASS - Authenticated session")

    response = client.get(
        BASE + "/", params={"q": "l'emploi"}, timeout=10
    )
    assert response.status_code == 200
    print("PASS - F1 apostrophe handled correctly")

    response = client.get(BASE + "/", timeout=10)
    assert response.status_code == 200
    assert "OFFRE_PRIVEE_TEST" not in response.text
    print("PASS - F1 private job confidentiality")

    response = client.get(
        BASE + "/", params={"q": "<b>TestHTML</b>"}, timeout=10
    )
    assert response.status_code == 200
    assert "<b>TestHTML</b>" not in response.text
    assert "&lt;b&gt;TestHTML&lt;/b&gt;" in response.text
    print("PASS - F2 HTML escaping")

    csp = response.headers.get("Content-Security-Policy", "")
    assert "script-src 'self'" in csp
    assert "'unsafe-inline'" not in csp
    print("PASS - F2 Content Security Policy")

print("All authenticated HTTP security checks passed.")
