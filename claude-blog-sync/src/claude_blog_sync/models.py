from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Article:
    source_url: str
    canonical_url: str
    title: str
    description: str | None
    published_at: str | None
    modified_at: str | None
    cover_image_url: str | None
    categories: list[str]
    products: list[str]
    use_cases: list[str]
    authors: list[str]
    details: dict[str, list[str]]
    body_html: str


@dataclass(slots=True)
class SyncConfig:
    output_dir: Path
    explicit_urls: tuple[str, ...] = ()
    year: int | None = None
    limit: int | None = None
    delay: float = 1.0
    timeout: float = 30.0
    retries: int = 3
    refresh_existing: bool = False
    download_images: bool = True


@dataclass(slots=True)
class SyncResult:
    discovered: int = 0
    queued: int = 0
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    skipped: int = 0
    filtered: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def successful(self) -> int:
        return self.created + self.updated + self.unchanged
