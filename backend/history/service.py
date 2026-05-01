import os
import json
from datetime import datetime
from typing import Optional
from .models import HistoryItem, HistoryCreate

HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "history")
MAX_HISTORY = 50


def _ensure_history_dir():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)


def _get_history_file_path(record_id: str) -> str:
    return os.path.join(HISTORY_DIR, f"{record_id}.json")


def _list_history_files() -> list[str]:
    _ensure_history_dir()
    files = []
    for f in os.listdir(HISTORY_DIR):
        if f.endswith(".json"):
            files.append(f)
    return sorted(files, reverse=True)


def _load_record(record_id: str) -> Optional[HistoryItem]:
    path = _get_history_file_path(record_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return HistoryItem(**data)


def _save_record(item: HistoryItem) -> None:
    _ensure_history_dir()
    path = _get_history_file_path(item.id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(item.model_dump(), f, ensure_ascii=False, indent=2)


def get_all_history() -> list[HistoryItem]:
    files = _list_history_files()
    items = []
    for fname in files:
        record_id = fname[:-5]  # remove .json
        item = _load_record(record_id)
        if item:
            items.append(item)
    return items


def get_history(record_id: str) -> Optional[HistoryItem]:
    return _load_record(record_id)


def create_history(data: HistoryCreate) -> HistoryItem:
    item = HistoryItem(
        id=datetime.now().strftime("%Y%m%d_%H%M%S_%f"),
        type=data.type,
        title=data.title,
        content=data.content,
        images=data.images,
        layout=data.layout,
        reasoning=data.reasoning,
        createdAt=datetime.now().isoformat(),
    )
    _save_record(item)
    _trim_history()
    return item


def delete_history(record_id: str) -> bool:
    path = _get_history_file_path(record_id)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def _trim_history():
    files = _list_history_files()
    if len(files) > MAX_HISTORY:
        files_to_delete = files[MAX_HISTORY:]
        for fname in files_to_delete:
            record_id = fname[:-5]
            delete_history(record_id)