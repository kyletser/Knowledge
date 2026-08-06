from __future__ import annotations

from claude_blog_sync.extract import (
    extract_article,
    html_to_markdown,
    parse_sitemap,
    prepare_body_html,
)


def test_parse_sitemap_keeps_only_english_article_urls() -> None:
    sitemap = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://claude.com/blog/alpha</loc></url>
      <url><loc>https://claude.com/blog/beta/</loc></url>
      <url><loc>https://claude.com/blog/category/agents</loc></url>
      <url><loc>https://claude.com/de/blog/alpha</loc></url>
      <url><loc>https://claude.com/blog</loc></url>
    </urlset>"""

    assert parse_sitemap(sitemap) == [
        "https://claude.com/blog/alpha",
        "https://claude.com/blog/beta",
    ]


def test_extract_and_convert_article() -> None:
    repeated_text = (
        "Getting an agent into production requires reliable infrastructure, clear permissions, "
        "observable sessions, and a carefully designed execution loop. "
    ) * 5
    page = f"""<!doctype html>
    <html><head>
      <link rel="canonical" href="https://claude.com/blog/example-post">
      <script type="application/ld+json">{{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "Example post",
        "description": "Example summary",
        "image": "https://cdn.example.test/cover.png",
        "datePublished": "Jun 10, 2026",
        "dateModified": "2026-07-10"
      }}</script>
    </head><body>
      <main id="main">
        <div class="hero_blog_post_details_item">
          <div class="hero_blog_post_details_content">
            <div class="u-text-style-caption">Category</div><a>Agents</a>
          </div>
        </div>
        <section class="blog_post_section_wrap">
          <div class="u-rich-text-blog w-richtext w-condition-invisible">{repeated_text} hidden</div>
          <div class="u-rich-text-blog w-richtext">
            <p>{repeated_text}</p>
            <h2>Architecture</h2>
            <p><a href="/docs/example">Documentation</a></p>
            <figure><div><iframe src="https://video.example.test/embed/1" title="Demo"></iframe></div></figure>
            <figure><div><img src="/images/diagram.png" alt="Diagram"></div><figcaption>A diagram</figcaption></figure>
          </div>
        </section>
      </main>
    </body></html>"""

    article = extract_article(page, "https://claude.com/blog/example-post")

    assert article.title == "Example post"
    assert article.published_at == "2026-06-10"
    assert article.modified_at == "2026-07-10"
    assert article.categories == ["Agents"]
    assert "hidden" not in article.body_html

    localized: list[str] = []

    def localize(url: str, _index: int) -> str:
        localized.append(url)
        return "images/diagram.png"

    clean_html = prepare_body_html(article.body_html, article.canonical_url, localize)
    markdown = html_to_markdown(clean_html)

    assert 'href="https://claude.com/docs/example"' in clean_html
    assert localized == ["https://claude.com/images/diagram.png"]
    assert "[Video: Demo](https://video.example.test/embed/1)" in markdown
    assert "![Diagram](images/diagram.png)" in markdown
    assert "## Architecture" in markdown

