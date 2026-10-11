# Lab3
from fastapi import APIRouter

router = APIRouter(tags=["diagnostics"])


@router.get("/internal/demo-error")
async def demo_error() -> dict:
    """Raise on purpose to demonstrate the 500 handler.

    In development the response carries the real message; in production it is a
    generic problem+json with no stacktrace or internal detail.
    """
    raise RuntimeError("Deliberate demo error for Lab 3.")
