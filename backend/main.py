from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="BoodschappenApp", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
