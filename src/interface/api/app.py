import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.interface.api.routers import chat, health

app = FastAPI(
    title="Стажка API",
    version="0.1.0",
    docs_url="/docs" if True else None,
)

# CORS обрабатывается nginx в проде (api.stazhka.ru → https://avvoby.github.io).
# Для локальной разработки (uvicorn без nginx перед ним) включаем CORSMiddleware,
# чтобы фронт с localhost мог ходить на API напрямую.
# Управление через APP_ENV: "production" (дефолт) → off, всё остальное → on.
if os.getenv("APP_ENV", "production") != "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health.router)
app.include_router(chat.router)


@app.get("/health")
async def root_health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
