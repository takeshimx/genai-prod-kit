import json
from dataclasses import asdict

from ..gateway import InvocationRecord


class JsonlSink:
    def __init__(self, path: str):
        self._path = path
    
    def write(self, record: InvocationRecord) -> None:
        row = asdict(record)
        row["created_at"] = record.created_at.isoformat()
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")