from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.interface.api.routers import chat, health

app = FastAPI(
    title="Стажка API",
    version="0.1.0",
    docs_url="/docs" if True else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)


@app.get("/health")
async def root_health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
