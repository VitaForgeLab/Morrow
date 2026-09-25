from fastapi import APIRouter

from app.routers import auth, conversations

# 只有这个对象和 main.py 打交道
api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(conversations.router)