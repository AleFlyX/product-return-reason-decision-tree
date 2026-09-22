"""HBase repository for production environment."""

from typing import Any

from app.core.config import settings


class HBaseRepository:
    """Reads data from HBase tables when DATA_BACKEND=hdfs_hbase."""

    def __init__(self) -> None:
        try:
            from happybase import Connection
            self.conn = Connection(
                host=settings.HBASE_HOST,
                port=settings.HBASE_PORT,
                autoconnect=True,
            )
        except Exception:
            self.conn = None

    @property
    def available(self) -> bool:
        return self.conn is not None

    def _get(self, table_name: str, row_key: str) -> dict:
        table = self.conn.table(table_name)
        row = table.row(row_key)
        return {k.decode(): v.decode() for k, v in row.items()}

    def _scan_prefix(self, table_name: str, prefix: str) -> list[dict]:
        table = self.conn.table(table_name)
        results = []
        for key, data in table.scan(row_prefix=prefix.encode()):
            decoded = {k.decode(): v.decode() for k, v in data.items()}
            decoded["row_key"] = key.decode()
            results.append(decoded)
        return results

    def get_overview(self) -> dict:
        return self._get(settings.HBASE_STATS_TABLE, "overview")

    def get_by_category(self) -> dict:
        rows = self._scan_prefix(settings.HBASE_STATS_TABLE, "category#")
        return {"items": rows}

    def get_by_promotion(self) -> dict:
        rows = self._scan_prefix(settings.HBASE_STATS_TABLE, "promotion#")
        return {"items": rows}

    def get_by_price_range(self) -> dict:
        rows = self._scan_prefix(settings.HBASE_STATS_TABLE, "price_range#")
        return {"items": rows}

    def get_orders(self, page: int, page_size: int, category: str | None, returned: int | None) -> dict:
        table = self.conn.table(settings.HBASE_ORDERS_TABLE)
        items = []
        for key, data in table.scan():
            row = {k.decode(): v.decode() for k, v in data.items()}
            row["order_id"] = key.decode()
            if category and row.get("category") != category:
                continue
            if returned is not None and int(row.get("returned", 0)) != returned:
                continue
            items.append(row)
        total = len(items)
        start = (page - 1) * page_size
        return {"items": items[start:start+page_size], "page": page, "page_size": page_size, "total": total}

    def predict(self, payload: dict) -> dict:
        raise NotImplementedError("Prediction requires model file loaded from HDFS")

    def get_model_metrics(self) -> dict:
        raise NotImplementedError("Model metrics require HDFS access")

    def get_model_features(self) -> dict:
        raise NotImplementedError("Model features require HDFS access")

    def get_model_rules(self, limit: int = 20) -> dict:
        raise NotImplementedError("Model rules require HDFS access")

    def get_model_predictions(self, limit: int = 200) -> dict:
        raise NotImplementedError("Model predictions require HDFS access")
