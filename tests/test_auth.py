# Lab2
from httpx import AsyncClient


async def test_register_returns_created(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register", json={"email": "newuser@example.com", "password": "password123"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "newuser@example.com"
    assert body["role"] == "user"


async def test_login_success_returns_token(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register", json={"email": "login@example.com", "password": "password123"}
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "login@example.com", "password": "password123"}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register", json={"email": "wrong@example.com", "password": "password123"}
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "wrong@example.com", "password": "nope-nope-nope"}
    )
    assert resp.status_code == 401


async def test_anonymous_access_to_protected_route_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/implants")
    assert resp.status_code == 401


async def test_duplicate_email_returns_409(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "password": "password123"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
