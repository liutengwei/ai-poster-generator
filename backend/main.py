from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import generate
from history.router import router as history_router
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI 宣传助手 后端", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api", tags=["生成"])
app.include_router(history_router, prefix="/api", tags=["历史记录"])


@app.get("/")
async def root():
    return {"message": "AI 宣传助手 API", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}