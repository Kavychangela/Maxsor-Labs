from fastapi.testclient import TestClient

from src.api import app


client = TestClient(app)


def test_register_user():
    response = client.post(
        "/register",
        json={
            "email": "test_auth@example.com",
            "password": "password123",
        },
    )

    assert response.status_code in [201, 409]


def test_login_invalid_credentials():
    response = client.post(
        "/login",
        json={
            "email": "does-not-exist@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401