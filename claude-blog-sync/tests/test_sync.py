from __future__ import annotations

import json
from pathlib import Path

import claude_blog_sync.sync as sync_module
import pytest
from claude_blog_sync.models import Article, SyncConfig


URL = "https://claude.com/blog/example"


def article_page(date_published: str = "Jun 10, 2026") -> str:
    body = (
        "Production agents need reliable infrastructure, observable sessions, explicit permissions, "
        "and an execution loop that can recover cleanly from temporary failures. "
    ) * 5
    return f"""<!doctype html><html><head>
    <link rel="canonical" href="{URL}">
    <script type="application/ld+json">{{
      "@type":"BlogPosting","headline":"Example","datePublished":"{date_published}"
    }}</script></head><body><main id="main"><section class="blog_post_section_wrap">
    <div class="u-rich-text-blog w-richtext"><p>{body}</p></div>
    </section></main></body></html>"""


class FakeSession:
    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class AllowAllRobots:
    def can_fetch(self, _user_agent: str, _url: str) -> bool:
        return True


class FakeImageResponse:
    def __init__(self, content_type: str, chunks: list[bytes]) -> None:
        self.headers = {"Content-Type": content_type}
        self.chunks = chunks

    def __enter__(self) -> "FakeImageResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int):
        assert chunk_size == 64 * 1024
        yield from self.chunks


class FakeImageSession:
    def __init__(self, response: FakeImageResponse) -> None:
        self.response = response
        self.stream_values: list[bool] = []

    def get(self, _url: str, *, timeout: float, stream: bool):
        assert timeout == 10
        self.stream_values.append(stream)
        return self.response


def write_state(output: Path, *, with_files: bool) -> None:
    article_dir = output / "articles" / "2026-06-10-example"
    if with_files:
        article_dir.mkdir(parents=True)
        (article_dir / "index.md").write_text("# Existing\n", encoding="utf-8")
        (article_dir / "content.html").write_text("<p>Existing</p>\n", encoding="utf-8")
    state = {
        "version": 1,
        "articles": {
            URL: {
                "path": "articles/2026-06-10-example/index.md",
                "content_hash": "old",
                "http_last_modified": "Wed, 01 Jul 2026 00:00:00 GMT",
                "fetched_at": "2026-07-01T00:00:00+00:00",
            }
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "state.json").write_text(json.dumps(state), encoding="utf-8")


def test_missing_artifacts_disable_conditional_request(monkeypatch, tmp_path: Path) -> None:
    output = tmp_path / "output"
    write_state(output, with_files=False)
    conditional_values: list[str | None] = []

    monkeypatch.setattr(sync_module, "build_session", lambda _retries: FakeSession())
    monkeypatch.setattr(sync_module, "_check_robots", lambda *_args: AllowAllRobots())

    def fake_fetch(_session, _url, _timeout, last_modified):
        conditional_values.append(last_modified)
        return article_page(), "Thu, 02 Jul 2026 00:00:00 GMT"

    monkeypatch.setattr(sync_module, "_fetch_article", fake_fetch)
    result = sync_module.sync_blog(
        SyncConfig(
            output_dir=output,
            explicit_urls=(URL,),
            refresh_existing=True,
            download_images=False,
            delay=0,
        ),
        log=lambda _message: None,
    )

    assert conditional_values == [None]
    assert result.updated == 1
    assert (output / "articles" / "2026-06-10-example" / "index.md").is_file()
    assert (output / "articles" / "2026-06-10-example" / "content.html").is_file()


def test_complete_artifacts_use_conditional_request(monkeypatch, tmp_path: Path) -> None:
    output = tmp_path / "output"
    write_state(output, with_files=True)
    conditional_values: list[str | None] = []

    monkeypatch.setattr(sync_module, "build_session", lambda _retries: FakeSession())
    monkeypatch.setattr(sync_module, "_check_robots", lambda *_args: AllowAllRobots())

    def fake_fetch(_session, _url, _timeout, last_modified):
        conditional_values.append(last_modified)
        return None, last_modified

    monkeypatch.setattr(sync_module, "_fetch_article", fake_fetch)
    result = sync_module.sync_blog(
        SyncConfig(
            output_dir=output,
            explicit_urls=(URL,),
            refresh_existing=True,
            download_images=False,
            delay=0,
        ),
        log=lambda _message: None,
    )

    assert conditional_values == ["Wed, 01 Jul 2026 00:00:00 GMT"]
    assert result.unchanged == 1


def test_untrusted_date_cannot_escape_output(tmp_path: Path) -> None:
    article = Article(
        source_url=URL,
        canonical_url=URL,
        title="Example",
        description=None,
        published_at="../../escape",
        modified_at=None,
        cover_image_url=None,
        categories=[],
        products=[],
        use_cases=[],
        authors=[],
        details={},
        body_html="<p>Body</p>",
    )

    target = sync_module._article_directory(tmp_path / "output", article, None)

    assert target.parent == (tmp_path / "output" / "articles").resolve()
    assert target.name == "undated-example"


def test_image_store_streams_and_validates_type(tmp_path: Path) -> None:
    response = FakeImageResponse("image/png", [b"\x89PNG\r\n\x1a\n", b"payload"])
    session = FakeImageSession(response)
    warnings: list[str] = []
    store = sync_module.ImageStore(session, tmp_path / "article", 10, warnings)

    relative_path = store._download("https://cdn.example.test/image.png", 1)

    assert session.stream_values == [True]
    assert relative_path.startswith("images/")
    assert (tmp_path / "article" / relative_path).read_bytes().startswith(b"\x89PNG")

    bad_store = sync_module.ImageStore(
        FakeImageSession(FakeImageResponse("text/html", [b"<html>error</html>"])),
        tmp_path / "bad",
        10,
        [],
    )
    with pytest.raises(ValueError, match="图片响应类型"):
        bad_store._download("https://cdn.example.test/error.png", 1)


def test_artifact_check_detects_missing_local_image(tmp_path: Path) -> None:
    output = tmp_path / "output"
    article_dir = output / "articles" / "example"
    article_dir.mkdir(parents=True)
    (article_dir / "index.md").write_text("![](images/picture.png)\n", encoding="utf-8")
    (article_dir / "content.html").write_text("<img src=\"images/picture.png\">\n", encoding="utf-8")
    entry = {"path": "articles/example/index.md"}

    assert not sync_module._artifacts_complete(output, entry)
    (article_dir / "images").mkdir()
    (article_dir / "images" / "picture.png").write_bytes(b"image")
    assert sync_module._artifacts_complete(output, entry)


def test_year_filter_caches_out_of_scope_article(monkeypatch, tmp_path: Path) -> None:
    output = tmp_path / "output"
    fetch_count = 0

    monkeypatch.setattr(sync_module, "build_session", lambda _retries: FakeSession())
    monkeypatch.setattr(sync_module, "_check_robots", lambda *_args: AllowAllRobots())

    def fake_fetch(_session, _url, _timeout, _last_modified):
        nonlocal fetch_count
        fetch_count += 1
        return article_page("Dec 31, 2025"), "Thu, 02 Jul 2026 00:00:00 GMT"

    monkeypatch.setattr(sync_module, "_fetch_article", fake_fetch)
    config = SyncConfig(
        output_dir=output,
        explicit_urls=(URL,),
        year=2026,
        download_images=False,
        delay=0,
    )

    first = sync_module.sync_blog(config, log=lambda _message: None)
    second = sync_module.sync_blog(config, log=lambda _message: None)

    assert first.filtered == 1
    assert second.filtered == 1
    assert fetch_count == 1
    state = json.loads((output / "state.json").read_text(encoding="utf-8"))
    assert state["observed"][URL]["published_at"] == "2025-12-31"
    assert not (output / "articles").exists()


def test_year_archive_index_is_sorted_and_filtered(tmp_path: Path) -> None:
    output = tmp_path / "output"
    paths = [
        "articles/2026-01-02-two/index.md",
        "articles/2026-03-04-four/index.md",
        "articles/2025-12-31-old/index.md",
    ]
    for relative_path in paths:
        target = output / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Article\n", encoding="utf-8")
    state = {
        "articles": {
            "two": {"published_at": "2026-01-02", "title": "Two", "path": paths[0]},
            "four": {"published_at": "2026-03-04", "title": "Four", "path": paths[1]},
            "old": {"published_at": "2025-12-31", "title": "Old", "path": paths[2]},
        }
    }

    sync_module._write_archive_index(output, state, 2026, "2026-07-15T00:00:00+00:00")
    rendered = (output / "2026-index.md").read_text(encoding="utf-8")

    assert "文章数：2" in rendered
    assert rendered.index("Four") < rendered.index("Two")
    assert "Old" not in rendered
