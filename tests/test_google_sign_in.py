"""Sign in with Google (INT-1): an ID token Google signed for this
deployment, with a verified email of an existing account, signs in; a token
for another client, from another issuer, expired, unverified, or for an
address with no account does not; with no client id set up the route says
so and the sign-in page is told not to show the button."""
from __future__ import annotations

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from test_homework import w  # noqa: F401 - `w` is a fixture

CLIENT = "123-abc.apps.googleusercontent.com"
_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _token(email="ana@example.com", *, aud=CLIENT, iss="https://accounts.google.com", verified=True,
           exp_in=600, key=_KEY):
    now = int(time.time())
    return jwt.encode({"iss": iss, "aud": aud, "sub": "g-1", "email": email, "email_verified": verified,
                       "iat": now, "exp": now + exp_in}, key, algorithm="RS256", headers={"kid": "k1"})


@pytest.fixture
def google(monkeypatch):
    from academicos.operations import google_sign_in as g
    g._limiter.reset()
    monkeypatch.setenv("ACOS_GOOGLE_CLIENT_ID", CLIENT)
    monkeypatch.setattr(g, "_signing_key", lambda token: _KEY.public_key())


def test_an_existing_account_signs_in_with_google(w, google):
    r = w.c.post("/api/v1/auth/google", json={"credential": _token("Ana@Example.com")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user"]["email"] == "ana@example.com" and body["token"]
    assert w.c.get("/api/v1/homework", headers={"Authorization": f"Bearer {body['token']}"}).status_code == 200
    assert w.c.get("/api/v1/auth/providers").json()["google"] == {"clientId": CLIENT}


@pytest.mark.parametrize("token, why", [
    (lambda: _token(aud="someone-else"), "could not be checked"),
    (lambda: _token(iss="https://evil.example.com"), "did not come from Google"),
    (lambda: _token(exp_in=-120), "could not be checked"),
    (lambda: _token(verified=False), "not verified"),
    (lambda: _token(key=_OTHER), "could not be checked"),
    (lambda: _token("stranger@example.com"), "No AcademicOS account uses stranger@example.com"),
])
def test_what_google_sign_in_refuses(w, google, token, why):
    r = w.c.post("/api/v1/auth/google", json={"credential": token()})
    assert r.status_code == 401 and why in r.json()["detail"]


def test_without_a_client_id_there_is_no_google_button(w, monkeypatch):
    monkeypatch.delenv("ACOS_GOOGLE_CLIENT_ID", raising=False)
    assert w.c.get("/api/v1/auth/providers").json()["google"] is None
    r = w.c.post("/api/v1/auth/google", json={"credential": _token()})
    assert r.status_code == 503 and "password" in r.json()["detail"]
