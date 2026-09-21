"""HDFS repository for reading model artifacts in production."""

from typing import Any

from app.core.config import settings


class HDFSRepository:
    """Reads model files from HDFS when DATA_BACKEND=hdfs_hbase."""

    def __init__(self) -> None:
        try:
            from hdfs import InsecureClient
            self.client = InsecureClient(settings.HDFS_URL.replace("hdfs://", "http://"))
        except Exception:
            self.client = None

    @property
    def available(self) -> bool:
        return self.client is not None

    def read_json(self, hdfs_path: str) -> dict:
        if not self.client:
            return {}
        with self.client.read(hdfs_path) as f:
            import json
            return json.loads(f.read().decode())
