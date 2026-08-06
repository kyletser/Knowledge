from __future__ import annotations

import hashlib
import html as html_module
import json
import os
import re
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from urllib import robotparser
from urllib.parse import unquote, urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from claude_blog_sync.extract import (
    extract_article,
    html_to_markdown,
    parse_sitemap,
    prepare_body_html,
)
from claude_blog_sync.models import Article, SyncConfig, SyncResult


BLOG_ROOT = "https://claude.com/blog/"
ROBOTS_URL = "https://claude.com/robots.txt"
SITEMAP_URL = "https://claude.com/sitemap.xml"
USER_AGENT = "Knowledge-ClaudeBlogSync/0.1 (personal research archiver)"
STATE_VERSION = 1
MAX_IMAGE_BYTES = 25 * 1024 * 1024
IMAGE_SUFFIXES = {
    "image/avif": ".avif",
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/svg+xml": ".svg",
    "image/webp": ".webp",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_session(retries: int) -> requests.Session:
    retry = Retry(
        total=max(0, retries),
        connect=max(0, retries),
        read=max(0, retries),
        status=max(0, retries),
        backoff_factor=1.0,
        status_forcelist=(403, 408, 429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return session


def _check_robots(
    session: requests.Session,
    timeout: float,
    targets: list[str],
) -> robotparser.RobotFileParser:
    response = session.get(ROBOTS_URL, timeout=timeout)
    response.raise_for_status()
    parser = robotparser.RobotFileParser()
    parser.set_url(ROBOTS_URL)
    parser.parse(response.text.splitlines())
    denied = [url for url in targets if not parser.can_fetch(USER_AGENT, url)]
    if denied:
        raise PermissionError(f"robots.txt 不允许抓取: {', '.join(denied)}")
    return parser


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def _atomic_write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(value)
    os.replace(temporary, path)


def _has_expected_image_signature(content_type: str, content: bytes) -> bool:
    if content_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if content_type == "image/gif":
        return content.startswith((b"GIF87a", b"GIF89a"))
    if content_type == "image/webp":
        return len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    if content_type == "image/avif":
        return len(content) >= 12 and content[4:12] in {b"ftypavif", b"ftypavis"}
    if content_type == "image/svg+xml":
        start = content[:2048].lstrip(b"\xef\xbb\xbf\x00\t\r\n ").lower()
        return start.startswith(b"<svg") or (start.startswith(b"<?xml") and b"<svg" in start)
    return False


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"version": STATE_VERSION, "articles": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"无法读取状态文件 {path}: {exc}") from exc
    if state.get("version") != STATE_VERSION or not isinstance(state.get("articles"), dict):
        raise ValueError(f"不支持的状态文件格式: {path}")
    return state


def save_state(path: Path, state: dict) -> None:
    _atomic_write_text(path, json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _safe_existing_index(output_dir: Path, entry: dict | None) -> Path | None:
    if not entry or not isinstance(entry.get("path"), str):
        return None
    candidate = (output_dir / entry["path"]).resolve()
    try:
        candidate.relative_to(output_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"state.json 中存在越界路径: {entry['path']}") from exc
    return candidate


def _artifacts_complete(output_dir: Path, entry: dict | None) -> bool:
    if not entry or entry.get("incomplete") is True:
        return False
    index_path = _safe_existing_index(output_dir, entry)
    if index_path is None or not index_path.is_file():
        return False
    if not index_path.with_name("content.html").is_file():
        return False
    try:
        markdown = index_path.read_text(encoding="utf-8")
    except OSError:
        return False
    local_images = re.findall(r"!\[[^\]]*\]\((images/[^)\s]+)", markdown)
    for relative_image in local_images:
        image_path = (index_path.parent / relative_image).resolve()
        try:
            image_path.relative_to(index_path.parent.resolve())
        except ValueError:
            return False
        if not image_path.is_file():
            return False
    return True


def _slugify(value: str, fallback: str = "article") -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return (clean or fallback)[:100]


def _article_directory(output_dir: Path, article: Article, entry: dict | None) -> Path:
    existing_index = _safe_existing_index(output_dir, entry)
    if existing_index is not None:
        return existing_index.parent
    path_slug = unquote(urlsplit(article.canonical_url).path.rstrip("/").split("/")[-1])
    slug = _slugify(path_slug)
    date_prefix = article.published_at if re.fullmatch(r"\d{4}-\d{2}-\d{2}", article.published_at or "") else "undated"
    articles_root = (output_dir / "articles").resolve()
    target = (articles_root / f"{date_prefix}-{slug}").resolve()
    try:
        target.relative_to(articles_root)
    except ValueError as exc:
        raise ValueError(f"拒绝输出到 articles 目录之外: {target}") from exc
    return target


def _yaml_value(value: object) -> str:
    if value is None:
        return "null"
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _fingerprint(article: Article, body_markdown: str) -> str:
    stable = {
        "canonical_url": article.canonical_url,
        "title": article.title,
        "description": article.description,
        "published_at": article.published_at,
        "modified_at": article.modified_at,
        "cover_image_url": article.cover_image_url,
        "categories": article.categories,
        "products": article.products,
        "use_cases": article.use_cases,
        "authors": article.authors,
        "details": article.details,
        "body_markdown": body_markdown,
    }
    encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def render_markdown(article: Article, body_markdown: str, fetched_at: str, content_hash: str) -> str:
    metadata = (
        ("title", article.title),
        ("source_url", article.source_url),
        ("canonical_url", article.canonical_url),
        ("description", article.description),
        ("published_at", article.published_at),
        ("modified_at", article.modified_at),
        ("cover_image_url", article.cover_image_url),
        ("categories", article.categories),
        ("products", article.products),
        ("use_cases", article.use_cases),
        ("authors", article.authors),
        ("details", article.details),
        ("fetched_at", fetched_at),
        ("content_hash", content_hash),
    )
    lines = ["---", *(f"{key}: {_yaml_value(value)}" for key, value in metadata), "---", ""]
    lines.extend(
        [
            f"# {article.title}",
            "",
            f"> 来源：[Claude Blog]({article.canonical_url})",
            "",
            body_markdown.rstrip(),
            "",
        ]
    )
    return "\n".join(lines)


def render_standalone_html(article: Article, body_html: str) -> str:
    title = html_module.escape(article.title)
    canonical = html_module.escape(article.canonical_url, quote=True)
    description_meta = ""
    if article.description:
        description_meta = f'  <meta name="description" content="{html_module.escape(article.description, quote=True)}">\n'
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{title}</title>\n"
        f'{description_meta}'
        f'  <link rel="canonical" href="{canonical}">\n'
        "</head>\n"
        "<body>\n"
        "<article>\n"
        f"  <h1>{title}</h1>\n"
        f'  <p>Source: <a href="{canonical}">Claude Blog</a></p>\n'
        f"{body_html}\n"
        "</article>\n"
        "</body>\n"
        "</html>\n"
    )


class ImageStore:
    def __init__(
        self,
        session: requests.Session,
        article_dir: Path,
        timeout: float,
        warnings: list[str],
    ) -> None:
        self.session = session
        self.images_dir = article_dir / "images"
        self.timeout = timeout
        self.warnings = warnings

    def __call__(self, url: str, index: int) -> str:
        try:
            return self._download(url, index)
        except Exception as exc:  # noqa: BLE001
            self.warnings.append(f"图片保留远程地址 {url}: {type(exc).__name__}: {exc}")
            return url

    def _download(self, url: str, index: int) -> str:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"}:
            return url
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        existing = next(iter(self.images_dir.glob(f"{digest}-*")), None) if self.images_dir.exists() else None
        if existing is not None and existing.is_file() and existing.stat().st_size > 0:
            return f"images/{existing.name}"

        with self.session.get(url, timeout=self.timeout, stream=True) as response:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type not in IMAGE_SUFFIXES:
                raise ValueError(f"不支持的图片响应类型: {content_type or 'unknown'}")
            try:
                declared_length = int(response.headers.get("Content-Length", "0") or 0)
            except ValueError:
                declared_length = 0
            if declared_length > MAX_IMAGE_BYTES:
                raise ValueError(f"图片超过 {MAX_IMAGE_BYTES // (1024 * 1024)} MiB")
            buffer = bytearray()
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                buffer.extend(chunk)
                if len(buffer) > MAX_IMAGE_BYTES:
                    raise ValueError(f"图片超过 {MAX_IMAGE_BYTES // (1024 * 1024)} MiB")
            content = bytes(buffer)

        if not _has_expected_image_signature(content_type, content):
            raise ValueError(f"图片签名与响应类型不匹配: {content_type}")
        suffix = IMAGE_SUFFIXES[content_type]

        original_stem = Path(unquote(parsed.path)).stem
        stem = _slugify(original_stem, fallback=f"image-{index:02d}")[:50]
        filename = f"{digest}-{stem}{suffix}"
        target = self.images_dir / filename
        _atomic_write_bytes(target, content)
        return f"images/{filename}"


def _fetch_article(
    session: requests.Session,
    url: str,
    timeout: float,
    last_modified: str | None,
) -> tuple[str | None, str | None]:
    headers = {"If-Modified-Since": last_modified} if last_modified else {}
    response = session.get(url, headers=headers, timeout=timeout)
    if response.status_code == 304:
        return None, last_modified
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "")
    if "html" not in content_type.casefold():
        raise ValueError(f"文章响应不是 HTML: {content_type or 'unknown'}")
    return response.text, response.headers.get("Last-Modified")


def _normalize_explicit_urls(urls: tuple[str, ...]) -> list[str]:
    normalized: set[str] = set()
    for url in urls:
        parsed = urlsplit(url.strip())
        parts = [part for part in parsed.path.split("/") if part]
        if parsed.scheme != "https" or parsed.hostname != "claude.com" or len(parts) != 2 or parts[0] != "blog":
            raise ValueError(f"不是受支持的 Claude Blog 文章 URL: {url}")
        normalized.add(f"https://claude.com/blog/{parts[1]}")
    return sorted(normalized)


def _write_report(output_dir: Path, result: SyncResult, state: dict, started_at: str, finished_at: str) -> None:
    lines = [
        "# Claude Blog 同步报告",
        "",
        f"- 开始时间（UTC）：{started_at}",
        f"- 完成时间（UTC）：{finished_at}",
        f"- 发现：{result.discovered}",
        f"- 本次排队：{result.queued}",
        f"- 新建：{result.created}",
        f"- 更新：{result.updated}",
        f"- 未变化：{result.unchanged}",
        f"- 已跳过：{result.skipped}",
        f"- 按年份过滤：{result.filtered}",
        f"- 失败：{len(result.failures)}",
        f"- 状态库文章数：{len(state.get('articles', {}))}",
        "",
    ]
    if result.failures:
        lines.extend(["## 失败", ""])
        lines.extend(f"- {url} — {message}" for url, message in result.failures)
        lines.append("")
    if result.warnings:
        lines.extend(["## 警告", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
        lines.append("")
    _atomic_write_text(output_dir / "sync_report.md", "\n".join(lines))


def _write_archive_index(output_dir: Path, state: dict, year: int | None, generated_at: str) -> None:
    entries: list[tuple[str, str, str]] = []
    year_prefix = f"{year:04d}-" if year is not None else None
    for entry in state.get("articles", {}).values():
        published_at = str(entry.get("published_at") or "")
        relative_path = entry.get("path")
        if year_prefix and not published_at.startswith(year_prefix):
            continue
        if not isinstance(relative_path, str) or not (output_dir / relative_path).is_file():
            continue
        title = str(entry.get("title") or Path(relative_path).parent.name)
        entries.append((published_at or "undated", title, Path(relative_path).as_posix()))
    entries.sort(key=lambda item: (item[0], item[1].casefold()), reverse=True)

    heading = f"Claude Blog {year} 年文章" if year is not None else "Claude Blog 文章归档"
    lines = [
        f"# {heading}",
        "",
        f"- 文章数：{len(entries)}",
        f"- 生成时间（UTC）：{generated_at}",
        "",
        "| 发布日期 | 标题 |",
        "|---|---|",
    ]
    for published_at, title, relative_path in entries:
        safe_title = title.replace("\\", "\\\\").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        lines.append(f"| {published_at} | [{safe_title}]({relative_path}) |")
    lines.append("")
    filename = f"{year}-index.md" if year is not None else "archive_index.md"
    _atomic_write_text(output_dir / filename, "\n".join(lines))


def sync_blog(config: SyncConfig, log: Callable[[str], None] = print) -> SyncResult:
    if config.limit is not None and config.limit < 0:
        raise ValueError("limit 不能小于 0")
    if config.delay < 0 or config.timeout <= 0 or config.retries < 0:
        raise ValueError("delay、timeout 或 retries 参数无效")
    if config.year is not None and not 2000 <= config.year <= 2100:
        raise ValueError("year 必须在 2000 到 2100 之间")

    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "state.json"
    state = load_state(state_path)
    articles_state: dict[str, dict] = state["articles"]
    observed_state: dict[str, dict] = state.setdefault("observed", {})
    result = SyncResult()
    started_at = utc_now()

    with build_session(config.retries) as session:
        if config.explicit_urls:
            urls = _normalize_explicit_urls(config.explicit_urls)
        else:
            urls = []
        robots = _check_robots(session, config.timeout, [SITEMAP_URL, *(urls or [BLOG_ROOT])])
        if not urls:
            sitemap_response = session.get(SITEMAP_URL, timeout=config.timeout)
            sitemap_response.raise_for_status()
            urls = parse_sitemap(sitemap_response.text)
        denied_urls = [url for url in urls if not robots.can_fetch(USER_AGENT, url)]
        if denied_urls:
            preview = ", ".join(denied_urls[:3])
            suffix = " ..." if len(denied_urls) > 3 else ""
            raise PermissionError(f"robots.txt 不允许抓取 {len(denied_urls)} 篇文章: {preview}{suffix}")
        result.discovered = len(urls)

        candidates: list[str] = []
        year_prefix = f"{config.year:04d}-" if config.year is not None else None
        for url in urls:
            entry = articles_state.get(url)
            observed = observed_state.get(url)
            entry_date = entry.get("published_at") if entry else None
            observed_date = observed.get("published_at") if observed else None
            if year_prefix and entry_date and not str(entry_date).startswith(year_prefix):
                result.filtered += 1
                continue
            if (
                year_prefix
                and observed_date
                and not str(observed_date).startswith(year_prefix)
                and not config.refresh_existing
            ):
                result.filtered += 1
                continue
            year_unknown = bool(year_prefix and entry is not None and not entry_date)
            if config.refresh_existing or entry is None or year_unknown or not _artifacts_complete(output_dir, entry):
                candidates.append(url)
            else:
                result.skipped += 1
        if config.limit is not None:
            candidates = candidates[: config.limit]
        result.queued = len(candidates)

        log(
            f"发现 {result.discovered} 篇；本次处理 {result.queued} 篇；"
            f"跳过 {result.skipped} 篇；按年份过滤 {result.filtered} 篇"
        )
        for position, url in enumerate(candidates, start=1):
            entry = articles_state.get(url)
            artifacts_were_complete = _artifacts_complete(output_dir, entry)
            conditional_value = (
                entry.get("http_last_modified")
                if config.refresh_existing and entry and artifacts_were_complete
                else None
            )
            log(f"[{position}/{len(candidates)}] {url}")
            try:
                raw_html, http_last_modified = _fetch_article(
                    session,
                    url,
                    config.timeout,
                    conditional_value,
                )
                checked_at = utc_now()
                if raw_html is None:
                    if entry is None:
                        raise RuntimeError("服务器返回 304，但本地没有对应状态")
                    entry["checked_at"] = checked_at
                    result.unchanged += 1
                    save_state(state_path, state)
                    log("  未变化（304）")
                    continue

                article = extract_article(raw_html, url)
                if year_prefix:
                    if article.published_at is None:
                        raise ValueError("启用 --year 时无法确定文章发布日期")
                    if not article.published_at.startswith(year_prefix):
                        observed_state[url] = {
                            "title": article.title,
                            "published_at": article.published_at,
                            "checked_at": checked_at,
                        }
                        result.filtered += 1
                        save_state(state_path, state)
                        log(f"  过滤：发布日期 {article.published_at}")
                        continue
                    observed_state.pop(url, None)
                article_dir = _article_directory(output_dir, article, entry)
                image_localizer = None
                warning_start = len(result.warnings)
                if config.download_images:
                    image_localizer = ImageStore(session, article_dir, config.timeout, result.warnings)
                clean_html = prepare_body_html(article.body_html, article.canonical_url, image_localizer)
                body_markdown = html_to_markdown(clean_html)
                content_hash = _fingerprint(article, body_markdown)
                old_hash = entry.get("content_hash") if entry else None
                index_path = article_dir / "index.md"
                fetched_at = checked_at
                had_image_warnings = len(result.warnings) > warning_start

                if old_hash == content_hash and artifacts_were_complete and not had_image_warnings:
                    result.unchanged += 1
                    fetched_at = entry.get("fetched_at", checked_at) if entry else checked_at
                    log("  内容未变化")
                else:
                    article_dir.mkdir(parents=True, exist_ok=True)
                    _atomic_write_text(
                        index_path,
                        render_markdown(article, body_markdown, fetched_at, content_hash),
                    )
                    _atomic_write_text(
                        article_dir / "content.html",
                        render_standalone_html(article, clean_html),
                    )
                    if entry is None or old_hash is None:
                        result.created += 1
                        log(f"  新建 {index_path}")
                    else:
                        result.updated += 1
                        log(f"  更新 {index_path}")

                relative_index = index_path.relative_to(output_dir).as_posix()
                articles_state[url] = {
                    "canonical_url": article.canonical_url,
                    "title": article.title,
                    "published_at": article.published_at,
                    "modified_at": article.modified_at,
                    "content_hash": content_hash,
                    "http_last_modified": http_last_modified,
                    "path": relative_index,
                    "fetched_at": fetched_at,
                    "checked_at": checked_at,
                    "incomplete": had_image_warnings,
                }
                save_state(state_path, state)
            except Exception as exc:  # noqa: BLE001
                message = f"{type(exc).__name__}: {exc}"
                result.failures.append((url, message[:500]))
                log(f"  失败：{message}")
            finally:
                if position < len(candidates) and config.delay:
                    time.sleep(config.delay)

    finished_at = utc_now()
    state["last_run"] = {
        "started_at": started_at,
        "finished_at": finished_at,
        "discovered": result.discovered,
        "queued": result.queued,
        "created": result.created,
        "updated": result.updated,
        "unchanged": result.unchanged,
        "filtered": result.filtered,
        "failures": len(result.failures),
    }
    save_state(state_path, state)
    _write_archive_index(output_dir, state, config.year, finished_at)
    _write_report(output_dir, result, state, started_at, finished_at)

    failed_path = output_dir / "failed.txt"
    if result.failures:
        _atomic_write_text(failed_path, "\n".join(url for url, _ in result.failures) + "\n")
    elif failed_path.exists():
        failed_path.unlink()
    return result
