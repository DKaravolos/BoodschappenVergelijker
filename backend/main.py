from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.database import init_db
from backend.models import Product


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="BoodschappenApp", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/products", response_model=list[Product])
async def get_products():
    return []


@app.get("/discounts", response_model=list[Product])
async def get_discounts():
    return []


@app.post("/scrape")
async def scrape():
    return {"status": "ok"}
