"""Flag regulator pages that changed since the matrices were last verified.

    python crawlers/watch_sources.py            report changes against snapshots.json
    python crawlers/watch_sources.py --update   also record the current pages as the new baseline

It does not edit the matrices. A changed or missing page means a person must re-read
it and update the matrix JSON; regulatory rules are never rewritten automatically.
Exit code 1 when any page changed, disappeared or could not be read.

Only the main content is compared (the <main> element when there is one), so menus
and footers don't raise false alarms. robots.txt is honoured and requests are spaced out.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
import zlib
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from matrix_models import MATRICES_DIR, SYLLABI_DIR, load_all, load_syllabus  # noqa: E402

SNAPSHOTS = Path(__file__).parent / "snapshots.json"
USER_AGENT = "CredentialNavigatorBot/0.1 (regulatory change monitor; low volume)"
DELAY_SECONDS = 2.0


class _MainText(HTMLParser):
    """Collects visible text, preferring what is inside <main>."""

    SKIP = {"script", "style", "noscript", "svg", "nav", "header", "footer"}

    def __init__(self) -> None:
        super().__init__()
        self.all: list[str] = []
        self.main: list[str] = []
        self.skip_depth = 0
        self.main_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip_depth += 1
        if tag == "main":
            self.main_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1
        if tag == "main" and self.main_depth:
            self.main_depth -= 1

    def handle_data(self, data):
        if self.skip_depth:
            return
        self.all.append(data)
        if self.main_depth:
            self.main.append(data)


# Text that changes without the rules changing: exchange-rate conversions such as
# NNAS's "$750 CAD ($525 USD)*" or "(approx. $525 USD)". The fee itself is still compared.
VOLATILE = re.compile(r"\(\s*approx\.?[^)]*\)|\(\s*\$\s?[\d,]+(?:\.\d+)?\s*(?:CAD|USD)\s*\)\s*\*?", re.I)


def page_text(html: str) -> str:
    parser = _MainText()
    parser.feed(html)
    text = " ".join(parser.main or parser.all)
    return re.sub(r"\s+", " ", VOLATILE.sub("", text)).strip()


def pdf_text(data: bytes) -> str:
    from pypdf import PdfReader
    text = " ".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)
    return re.sub(r"\s+", " ", text).strip()


def fingerprint(html: str) -> str:
    return hashlib.sha256(page_text(html).encode("utf-8")).hexdigest()


@dataclass
class Fetched:
    status: int
    body: str = ""
    raw: bytes = b""

    def fingerprint(self) -> str:
        """PDFs are compared by their text, so a re-saved file with the same words is unchanged."""
        if self.raw.startswith(b"%PDF-"):
            return hashlib.sha256(pdf_text(self.raw).encode("utf-8")).hexdigest()
        return fingerprint(self.body)


def decompress(raw: bytes, encoding: str) -> bytes:
    """Some servers (e.g. nnas.ca) compress responses even when not asked to."""
    encoding = encoding.lower().strip()
    if encoding == "br":
        import brotli
        return brotli.decompress(raw)
    if encoding == "gzip" or raw[:2] == b"\x1f\x8b":
        return gzip.decompress(raw)
    if encoding == "deflate":
        try:
            return zlib.decompress(raw)
        except zlib.error:
            return zlib.decompress(raw, -zlib.MAX_WBITS)
    return raw


def http_fetch(url: str) -> Fetched:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate, br"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = decompress(response.read(), response.headers.get("Content-Encoding", ""))
            return Fetched(response.status, raw.decode("utf-8", "replace"), raw)
    except urllib.error.HTTPError as error:
        return Fetched(error.code)
    except (urllib.error.URLError, TimeoutError) as error:
        return Fetched(0, str(error))


def robots_allows(url: str, fetch: Callable[[str], Fetched]) -> bool:
    parts = urlsplit(url)
    robots = fetch(f"{parts.scheme}://{parts.netloc}/robots.txt")
    if robots.status != 200:
        return True  # no robots.txt means no restrictions
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(robots.body.splitlines())
    return parser.can_fetch(USER_AGENT, url)


def check(sources: dict[str, str], snapshots: dict, fetch: Callable[[str], Fetched] = http_fetch,
          delay: float = DELAY_SECONDS, today: date | None = None) -> tuple[list[dict], dict]:
    """Compare each source URL with its snapshot.

    sources maps url -> label. Returns (findings, new_snapshots); a finding has
    url, label and status: unchanged, changed, new, missing, blocked or error.
    """
    today = today or date.today()
    # Pages no longer cited by any matrix drop out of the baseline.
    findings, updated = [], {url: snap for url, snap in snapshots.items() if url in sources}
    robots_cache: dict[str, bool] = {}
    for i, (url, label) in enumerate(sorted(sources.items())):
        if i and delay:
            time.sleep(delay)
        host = urlsplit(url).netloc
        if host not in robots_cache:
            robots_cache[host] = robots_allows(url, fetch)
        if not robots_cache[host]:
            findings.append({"url": url, "label": label, "status": "blocked"})
            continue
        page = fetch(url)
        if page.status in (404, 410):
            findings.append({"url": url, "label": label, "status": "missing", "http": page.status})
            continue
        if page.status != 200:
            findings.append({"url": url, "label": label, "status": "error", "http": page.status})
            continue
        digest = page.fingerprint()
        previous = snapshots.get(url, {}).get("hash")
        status = "new" if previous is None else "unchanged" if previous == digest else "changed"
        findings.append({"url": url, "label": label, "status": status})
        updated[url] = {"hash": digest, "checked_on": today.isoformat(), "label": label}
    return findings, updated


def matrix_sources(directory: Path = MATRICES_DIR, syllabi_dir: Path = SYLLABI_DIR) -> dict[str, str]:
    """Every page cited by a matrix or a syllabus."""
    sources = {str(s.url): f"{m.regulator.short_name}: {s.title}" for m in load_all(directory) for s in m.sources}
    for path in sorted(syllabi_dir.glob("*.json")) if syllabi_dir.exists() else []:
        syllabus = load_syllabus(path)
        sources.update({str(s.url): f"{syllabus.regulator_id.upper()}: {s.title}" for s in syllabus.sources})
    return sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--update", action="store_true", help="save the current pages as the baseline")
    args = parser.parse_args(argv)

    snapshots = json.loads(SNAPSHOTS.read_text()) if SNAPSHOTS.exists() else {}
    findings, updated = check(matrix_sources(), snapshots)
    for f in findings:
        extra = f" (HTTP {f['http']})" if "http" in f else ""
        print(f"{f['status']:9} {f['label']}{extra}\n          {f['url']}")
    if args.update:
        SNAPSHOTS.write_text(json.dumps(updated, indent=2, sort_keys=True) + "\n")
        print(f"Baseline saved to {SNAPSHOTS.name}.")
    attention = [f for f in findings if f["status"] in ("changed", "missing", "blocked", "error")]
    if attention:
        print(f"\n{len(attention)} page(s) need a person to re-check the matrix.")
    return 1 if attention else 0


if __name__ == "__main__":
    sys.exit(main())
