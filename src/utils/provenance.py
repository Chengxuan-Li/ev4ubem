"""Download helpers that record provenance manifests (URL/query, retrieval time, size, sha256)."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import time
from pathlib import Path

import requests

from .paths import MANIFESTS, ROOT, ensure

UA = {"User-Agent": "Mozilla/5.0 (ev4ubem research; public data acquisition)"}


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def record(manifest: str, entry: dict) -> None:
    """Append/replace an entry (keyed by 'local_path') in metadata/manifests/<manifest>.json."""
    ensure(MANIFESTS)
    mpath = MANIFESTS / f"{manifest}.json"
    data = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else []
    data = [e for e in data if e.get("local_path") != entry.get("local_path")]
    data.append(entry)
    data.sort(key=lambda e: e.get("local_path", ""))
    mpath.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT).as_posix()


def download(url: str, dest: Path, manifest: str, params: dict | None = None,
             overwrite: bool = False, note: str = "", retries: int = 3, timeout: int = 600) -> Path:
    """Stream a URL to dest and record provenance. Skips download if dest exists (unless overwrite)."""
    dest = Path(dest)
    ensure(dest.parent)
    if dest.exists() and not overwrite:
        print(f"[skip] {rel(dest)} exists")
    else:
        tmp = dest.with_suffix(dest.suffix + ".part")
        for attempt in range(1, retries + 1):
            try:
                with requests.get(url, params=params, headers=UA, stream=True, timeout=timeout) as r:
                    r.raise_for_status()
                    with open(tmp, "wb") as f:
                        for b in r.iter_content(1 << 20):
                            f.write(b)
                tmp.replace(dest)
                break
            except Exception as exc:  # noqa: BLE001
                print(f"[retry {attempt}/{retries}] {url}: {exc}")
                if attempt == retries:
                    raise
                time.sleep(5 * attempt)
        print(f"[ok] {rel(dest)}")
    record(manifest, {
        "local_path": rel(dest),
        "url": url,
        "params": params or {},
        "retrieved_utc": _dt.datetime.fromtimestamp(dest.stat().st_mtime, _dt.timezone.utc).isoformat(timespec="seconds"),
        "bytes": dest.stat().st_size,
        "sha256": sha256(dest),
        "note": note,
    })
    return dest
