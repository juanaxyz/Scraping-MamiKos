import json
import os


class ProgressiveSaver:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tmp_path = filepath + ".tmp"
        self._data: list = self._load_existing()

    def _load_existing(self) -> list:
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
                return existing if isinstance(existing, list) else []
        except (json.JSONDecodeError, OSError) as e:
            print(f"[Saver] Gagal membaca file existing: {e}. Mulai dari kosong.")
            return []

    def append_and_save(self, item: dict):
        self._data.append(item)
        self._flush()

    def update_by_url(self, url_detail: str, updates: dict):
        for item in self._data:
            if item.get("url_detail") == url_detail:
                item.update(updates)
                self._flush()
                return
        print(f"    [Saver] update_by_url: url_detail tidak ditemukan: {url_detail}")

    def _flush(self):
        try:
            with open(self.tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(self.tmp_path, self.filepath)
        except OSError as e:
            print(f"    [Saver] Gagal flush ke disk: {e}")

    @property
    def count(self) -> int:
        return len(self._data)


class FailedPoiLogger:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tmp_path = filepath + ".tmp"
        self._data: list = self._load()

    def _load(self) -> list:
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def log(self, url_detail: str, lat, lon, failed_cats: list):
        if not failed_cats:
            return
        for entry in self._data:
            if entry.get("url_detail") == url_detail:
                entry["failed_categories"] = failed_cats
                self._flush()
                return
        self._data.append(
            {
                "url_detail": url_detail,
                "latitude": lat,
                "longitude": lon,
                "failed_categories": failed_cats,
            }
        )
        self._flush()

    def remove(self, url_detail: str):
        self._data = [e for e in self._data if e.get("url_detail") != url_detail]
        self._flush()

    def _flush(self):
        try:
            with open(self.tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(self.tmp_path, self.filepath)
        except OSError as e:
            print(f"    [FailedPoiLogger] Gagal flush: {e}")

    @property
    def count(self) -> int:
        return len(self._data)

    def all(self) -> list:
        return list(self._data)
