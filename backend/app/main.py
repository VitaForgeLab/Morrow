from fastapi import FastAPI

app = FastAPI(title="Morrow")

@app.get("/health")# health infra
async def health():
    return {"status":"ok"}
# It's Helloworld, using the command: uvicorn app.main:app --reload. Then see http://127.0.0.1:8000/docs