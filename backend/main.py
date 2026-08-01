from fastapi import FastAPI

app = FastAPI(title="BoodschappenApp")


@app.get("/health")
async def health():
    return {"status": "ok"}
