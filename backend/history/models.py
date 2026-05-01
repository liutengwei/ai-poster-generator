from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HistoryItem(BaseModel):
    id: str
    type: str  # "poster" | "article" | "brief"
    title: str
    content: str
    images: list[str]  # base64 encoded images
    layout: list
    reasoning: str
    createdAt: str


class HistoryCreate(BaseModel):
    type: str
    title: str
    content: str
    images: list[str]
    layout: list
    reasoning: str


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]
    total: int