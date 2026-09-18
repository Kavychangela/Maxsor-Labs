from fastapi.testclient import TestClient

from src.api import app


client = TestClient(app)


def register_and_login(email: str):
    client.post(
        "/register",
        json={
            "email": email,
            "password": "password123",
        },
    )

    response = client.post(
        "/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    return response.json()["access_token"]


def test_create_ticket():
    token = register_and_login("ticket_test@example.com")

    response = client.post(
        "/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": "My order arrived damaged.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["message"] == "My order arrived damaged."
    assert data["decision"]["action"] == "NEEDS_MORE_INFORMATION"


def test_get_tickets_requires_authentication():
    response = client.get("/tickets")

    assert response.status_code in [401, 403]


def test_user_cannot_access_another_users_ticket():
    alice_token = register_and_login("alice_ticket@example.com")

    response = client.post(
        "/tickets",
        headers={
            "Authorization": f"Bearer {alice_token}"
        },
        json={
            "message": "Alice's private ticket",
        },
    )

    assert response.status_code == 201

    ticket_id = response.json()["id"]

    bob_token = register_and_login("bob_ticket@example.com")

    response = client.get(
        f"/tickets/{ticket_id}",
        headers={
            "Authorization": f"Bearer {bob_token}"
        },
    )

    assert response.status_code == 404