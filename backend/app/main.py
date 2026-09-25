from fastapi import FastAPI,APIRouter
from app.api import api_router

app = FastAPI(title="Morrow")

#挂载路由
app.include_router(api_router,prefix="/api/v1")

@app.get("/health")# health infra
async def health():
    return {"status":"ok"}
# It's Helloworld, using the command: uvicorn app.main:app --reload. Then see http://127.0.0.1:8000/docs