from __future__ import annotations


def test_auth_email_is_trimmed_and_lowercased(client):
    raw_email = "  MixedCase@Example.Com  "
    normalized = "mixedcase@example.com"

    register = client.post("/api/auth/register", json={"email": raw_email, "password": "password123"})
    assert register.status_code == 201
    assert register.json()["email"] == normalized

    login = client.post("/api/auth/login", json={"email": normalized, "password": "password123"})
    assert login.status_code == 200

    token = login.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == normalized


def test_auth_email_uniqueness_is_case_insensitive(client):
    first = client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123"})
    assert first.status_code == 201

    dup = client.post("/api/auth/register", json={"email": "DUP@EXAMPLE.COM", "password": "password123"})
    assert dup.status_code == 400

