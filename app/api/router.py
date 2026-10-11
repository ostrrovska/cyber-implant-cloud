from fastapi import APIRouter

from app.api.routes import auth, dashboards, firmware, health, implants, ota  # Lab2

api_router = APIRouter()
api_router.include_router(health.router)

# Lab2: business API under a versioned prefix.
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth.router)
v1_router.include_router(implants.router)
v1_router.include_router(firmware.router)
v1_router.include_router(ota.router)
v1_router.include_router(dashboards.router)
api_router.include_router(v1_router)
