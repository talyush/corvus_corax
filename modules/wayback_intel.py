import json
import urllib.request
import urllib.parse
import urllib.error

from core.module_base import BaseModule
from core.config import load_rules


class WaybackIntelModule(BaseModule):
    """
    v0.9 — Wayback Machine Intelligence Module.

    Wayback Machine (Internet Archive) üzerinden web geçmişi analizi:
    - URL snapshot geçmişi (hangi tarihlerde kaydedilmiş)
    - Son snapshot zaman çizelgesi
    - Domain geçmişi korelasyonu (web_history_correlation — possible)
    """
    name = "wayback"

    def _fetch_json(self, url, timeout=12):
        """Internet Archive API'den JSON verisi çeker."""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "CorvusCorax/0.9 (+https://github.com/corvus-corax/project)",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _get_snapshots(self, url, timeout=12):
        """Bir URL için Wayback snapshot geçmişini çeker."""
        api_url = f"http://archive.org/wayback/available?url={urllib.parse.quote(url)}"
        data = self._fetch_json(api_url, timeout)
        if not data or "archived_snapshots" not in data:
            return None
        snap = data["archived_snapshots"]
        if "closest" not in snap:
            return None
        closest = snap["closest"]
        return {
            "available": closest.get("available", False),
            "url": closest.get("url"),
            "timestamp": closest.get("timestamp"),
            "status": closest.get("status", ""),
        }

    def _get_cdx(self, url, limit=10, timeout=12):
        """CDX API ile URL'nin tarihsel kayıtlarını çeker."""
        cdx_url = (f"https://web.archive.org/cdx/search/cdx?url={urllib.parse.quote(url)}"
                   f"&output=json&limit={limit}&fl=timestamp,statuscode,digest")
        data = self._fetch_json(cdx_url, timeout)
        if not data or not isinstance(data, list) or len(data) < 2:
            return []
        # İlk satır başlık, kalan satırlar kayıtlar
        return data[1:]

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: wayback <url>")

        url = args[0].strip()
        if "://" not in url:
            url = "https://" + url

        self.begin_investigation(
            goal=f"Wayback Machine Intelligence — {url}",
            phases=[
                (1, "SNAPSHOT DISCOVERY"),
                (2, "TIMELINE ANALYSIS"),
                (3, "CORRELATION MAPPING"),
            ],
        )

        # 1. Son snapshot
        def run_snapshot():
            return self._get_snapshots(url)

        self.status_step("Querying nearest snapshot", work=run_snapshot)
        snapshot = self._get_snapshots(url)

        # 2. CDX tarihsel kayıtlar
        if snapshot and snapshot.get("available"):
            self.status_step("Fetching historical CDX records")
            cdx_records = self._get_cdx(url)
        else:
            self.status_step("No snapshot available or URL not archived")
            cdx_records = []

        # --- Varlık Kayıtları ---
        domain = url.split("//")[1].split("/")[0] if "//" in url else url
        self.add_entity("domain", domain)

        # Wayback snapshot varlığı
        if snapshot and snapshot.get("available"):
            self.add_entity("web_snapshot", snapshot.get("url", url), {
                "original_url": url,
                "timestamp": snapshot.get("timestamp"),
                "status": snapshot.get("status"),
            })

        # --- Temporal Olaylar ---
        if snapshot and snapshot.get("available"):
            self.log_event("web_snapshot_found", entity=f"domain:{domain}",
                           metadata={"url": snapshot.get("url"), "timestamp": snapshot.get("timestamp")})

        if cdx_records:
            for record in cdx_records[:5]:
                ts = record[0] if len(record) > 0 else ""
                status = record[1] if len(record) > 1 else ""
                self.log_event("web_history_record", entity=f"domain:{domain}",
                               metadata={"timestamp": ts, "statuscode": status})

        # --- İlişkiler ---
        if snapshot and snapshot.get("available"):
            self.add_relation(
                "domain", domain, "has_web_history", "web_snapshot", snapshot.get("url", ""),
                evidence=f"Wayback Machine has archived {url} at {snapshot.get('timestamp')}",
                confidence=1.0,
            )

            self.add_relation(
                "domain", domain, "web_history_correlation", "web_snapshot", snapshot.get("url", ""),
                evidence=f"Web history preserved — {len(cdx_records)} CDX records found",
                confidence=0.4,  # web_history_correlation politikası — possible
            )

        self.add_note(
            f"Wayback: {url} — {'archived at ' + str(snapshot.get('timestamp')) if snapshot and snapshot.get('available') else 'not found'} "
            f"({len(cdx_records)} historical records)",
            severity="info", confidence=0.8,
        )

        data = {
            "url": url,
            "snapshot": snapshot,
            "historical_records": cdx_records,
            "record_count": len(cdx_records),
        }
        return self.success(target=url, data=data)