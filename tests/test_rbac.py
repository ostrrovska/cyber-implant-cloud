# Lab2
from httpx import AsyncClient

from app.models.user import UserRole

_FIRMWARE = {
    "version": "1.0.0",
    "checksum_sha256": "a" * 64,
    "artifact_url": "https://artifacts.local/fw-1.0.0.bin",
}
_IMPLANT = {"serial_number": "SN-1", "model": "neuro-x", "current_firmware_version": "0.9.0"}


async def test_vertical_user_cannot_publish_firmware(client: AsyncClient, make_user) -> None:
    headers = await make_user("user@example.com", role=UserRole.USER)
    resp = await client.post("/api/v1/firmware", json=_FIRMWARE, headers=headers)
    assert resp.status_code == 403


async def test_vertical_admin_can_publish_firmware(client: AsyncClient, make_user) -> None:
    headers = await make_user("admin@example.com", role=UserRole.ADMIN)
    resp = await client.post("/api/v1/firmware", json=_FIRMWARE, headers=headers)
    assert resp.status_code == 201


async def test_vertical_user_denied_admin_dashboard(client: AsyncClient, make_user) -> None:
    headers = await make_user("user2@example.com", role=UserRole.USER)
    resp = await client.get("/api/v1/admin/dashboard", headers=headers)
    assert resp.status_code == 403


async def test_idor_user_cannot_read_others_implant(client: AsyncClient, make_user) -> None:
    alice = await make_user("alice@example.com", role=UserRole.USER)
    bob = await make_user("bob@example.com", role=UserRole.USER)

    created = await client.post("/api/v1/implants", json=_IMPLANT, headers=alice)
    implant_id = created.json()["id"]

    resp = await client.get(f"/api/v1/implants/{implant_id}", headers=bob)
    assert resp.status_code == 403


async def test_idor_user_cannot_modify_others_implant(client: AsyncClient, make_user) -> None:
    alice = await make_user("alice2@example.com", role=UserRole.USER)
    bob = await make_user("bob2@example.com", role=UserRole.USER)

    created = await client.post("/api/v1/implants", json=_IMPLANT, headers=alice)
    implant_id = created.json()["id"]

    resp = await client.patch(
        f"/api/v1/implants/{implant_id}", json={"status": "quarantined"}, headers=bob
    )
    assert resp.status_code == 403


async def test_admin_can_access_any_implant(client: AsyncClient, make_user) -> None:
    alice = await make_user("alice3@example.com", role=UserRole.USER)
    admin = await make_user("admin3@example.com", role=UserRole.ADMIN)

    created = await client.post("/api/v1/implants", json=_IMPLANT, headers=alice)
    implant_id = created.json()["id"]

    resp = await client.get(f"/api/v1/implants/{implant_id}", headers=admin)
    assert resp.status_code == 200
