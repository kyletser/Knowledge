from __future__ import annotations

from claude_blog_sync.models import Article
from claude_blog_sync.sync import render_markdown, render_standalone_html


def sample_article() -> Article:
    return Article(
        source_url="https://claude.com/blog/example",
        canonical_url="https://claude.com/blog/example",
        title="Example: agents",
        description="A short summary",
        published_at="2026-06-10",
        modified_at="2026-07-10",
        cover_image_url="https://cdn.example.test/cover.png",
        categories=["Agents"],
        products=["Claude Platform"],
        use_cases=[],
        authors=[],
        details={"Category": ["Agents"]},
        body_html="<p>Body</p>",
    )


def test_render_markdown_has_machine_readable_metadata() -> None:
    rendered = render_markdown(sample_article(), "Body\n", "2026-07-15T00:00:00+00:00", "abc123")

    assert rendered.startswith("---\n")
    assert 'title: "Example: agents"' in rendered
    assert 'categories: ["Agents"]' in rendered
    assert "# Example: agents" in rendered
    assert "content_hash: \"abc123\"" in rendered


def test_render_html_is_standalone() -> None:
    rendered = render_standalone_html(sample_article(), "<p>Body</p>")

    assert rendered.startswith("<!doctype html>")
    assert '<link rel="canonical" href="https://claude.com/blog/example">' in rendered
    assert "<article>" in rendered
    assert "<p>Body</p>" in rendered
