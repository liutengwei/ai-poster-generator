from fastapi import APIRouter, HTTPException
from .models import HistoryItem, HistoryCreate, HistoryListResponse
from . import service

router = APIRouter(prefix="/history", tags=["历史记录"])


@router.get("", response_model=HistoryListResponse)
def list_history():
    items = service.get_all_history()
    return HistoryListResponse(items=items, total=len(items))


@router.post("", response_model=HistoryItem)
def add_history(data: HistoryCreate):
    return service.create_history(data)


@router.delete("/{record_id}")
def remove_history(record_id: str):
    deleted = service.delete_history(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"ok": True}


@router.get("/{record_id}", response_model=HistoryItem)
def get_history_record(record_id: str):
    item = service.get_history(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="记录不存在")
    return item