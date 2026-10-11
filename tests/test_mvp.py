# Lab2
from httpx import AsyncClient

from app.models.user import UserRole


async def test_full_rollout_flow(client: AsyncClient, make_user) -> None:
    owner = await make_user("owner@example.com", role=UserRole.USER)
    admin = await make_user("ops@example.com", role=UserRole.ADMIN)

    # Owner registers an implant.
    implant = await client.post(
        "/api/v1/implants",
        json={"serial_number": "SN-FLOW", "model": "neuro-x", "current_firmware_version": "0.9.0"},
        headers=owner,
    )
    assert implant.status_code == 201
    implant_id = implant.json()["id"]

    # Admin publishes firmware.
    firmware = await client.post(
        "/api/v1/firmware",
        json={
            "version": "2.0.0",
            "checksum_sha256": "b" * 64,
            "artifact_url": "https://artifacts.local/fw-2.0.0.bin",
        },
        headers=admin,
    )
    assert firmware.status_code == 201
    firmware_id = firmware.json()["id"]

    # Admin launches a rollout to that implant.
    rollout = await client.post(
        "/api/v1/ota/rollouts",
        json={"firmware_version_id": firmware_id, "implant_ids": [implant_id]},
        headers=admin,
    )
    assert rollout.status_code == 201
    assert rollout.json()["jobs_created"] == 1
    job_id = rollout.json()["job_ids"][0]

    # Owner sees the job for their implant and reports success.
    jobs = await client.get("/api/v1/ota/jobs", headers=owner)
    assert jobs.status_code == 200
    assert len(jobs.json()) == 1

    reported = await client.post(
        f"/api/v1/ota/jobs/{job_id}/status", json={"status": "succeeded"}, headers=owner
    )
    assert reported.status_code == 200
    assert reported.json()["status"] == "succeeded"


async def test_user_lists_only_own_implants(client: AsyncClient, make_user) -> None:
    alice = await make_user("a-list@example.com", role=UserRole.USER)
    bob = await make_user("b-list@example.com", role=UserRole.USER)

    await client.post(
        "/api/v1/implants",
        json={"serial_number": "SN-A", "model": "m", "current_firmware_version": "1.0.0"},
        headers=alice,
    )
    await client.post(
        "/api/v1/implants",
        json={"serial_number": "SN-B", "model": "m", "current_firmware_version": "1.0.0"},
        headers=bob,
    )

    alice_list = await client.get("/api/v1/implants", headers=alice)
    assert len(alice_list.json()) == 1
    assert alice_list.json()[0]["serial_number"] == "SN-A"
