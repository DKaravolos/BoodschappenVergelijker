from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.database import init_db
from backend.routers import basket, discounts, favourites, products, scrape


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="BoodschappenApp", lifespan=lifespan)

app.include_router(products.router)
app.include_router(discounts.router)
app.include_router(favourites.router)
app.include_router(basket.router)
app.include_router(scrape.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
