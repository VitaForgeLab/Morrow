from fastapi import FastAPI,APIRouter
from app.routers import auth

app = FastAPI(title="Morrow")

#挂载路由
app.include_router(auth.router,prefix="/api/v1")

@app.get("/health")# health infra
async def health():
    return {"status":"ok"}
# It's Helloworld, using the command: uvicorn app.main:app --reload. Then see http://127.0.0.1:8000/docs