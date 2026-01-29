from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.itineraries import router as itineraries_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.edit import router as edit_router
from app.core.config import get_settings
from app.core.logging import configure_logging


settings = get_settings()
configure_logging()


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(itineraries_router)
app.include_router(analysis_router)
app.include_router(edit_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
