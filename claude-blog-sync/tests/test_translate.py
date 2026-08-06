from __future__ import annotations

from claude_blog_sync.translate import (
    _protect_glossary,
    _restore_glossary,
    is_technical_article,
    technical_module,
    translate_document,
    translated_article_path,
)


class FakeTranslator:
    def __init__(self) -> None:
        self.cache: dict[str, str] = {}

    def translate_many(self, texts: list[str]) -> dict[str, str]:
        result = {}
        for text in texts:
            translated = self.cache.setdefault(text, f"中译：{text}")
            result[text] = translated
        return result

    def translate_one(self, text: str) -> str:
        return self.translate_many([text])[text]


def test_translate_document_preserves_code_links_and_images() -> None:
    source_html = """<!doctype html><html lang="en"><head>
    <title>Build reliable agents with Claude</title>
    <meta name="description" content="A practical guide">
    </head><body><article>
    <h1>Build reliable agents with Claude</h1>
    <p>Source: <a href="https://claude.com/blog/example">Claude Blog</a></p>
    <p>Run <code>print(&quot;hello&quot;)</code> before deployment.</p>
    <img src="images/diagram.png" alt="Architecture diagram">
    </article></body></html>"""
    source_markdown = """---
title: "Build reliable agents with Claude"
source_url: "https://claude.com/blog/example"
canonical_url: "https://claude.com/blog/example"
description: "A practical guide"
published_at: "2026-01-02"
categories: ["Agents"]
content_hash: "source123"
---

# Build reliable agents with Claude
"""

    translated_html, translated_markdown, translated_title, translation_hash = translate_document(
        source_html,
        source_markdown,
        FakeTranslator(),
        "2026-07-15T00:00:00+00:00",
    )

    assert 'lang="zh-CN"' in translated_html
    assert 'href="https://claude.com/blog/example"' in translated_html
    assert 'src="images/diagram.png"' in translated_html
    assert 'print("hello")' in translated_html
    assert "中译：Run" in translated_html
    assert translated_title == "中译：Build reliable agents with Claude"
    assert translated_markdown.startswith("# 中译：Build reliable agents with Claude")
    assert "发布日期：2026-01-02" in translated_markdown
    assert "[原文链接](https://claude.com/blog/example)" in translated_markdown
    assert not translated_markdown.startswith("---")
    assert "images/diagram.png" in translated_markdown
    assert len(translation_hash) == 64


def test_glossary_protects_brand_and_ai_agent_terms() -> None:
    protected = _protect_glossary("Anthropic builds agentic systems with Claude Code agents and MCP APIs.")

    assert "Anthropic" not in protected
    assert "Claude Code" not in protected
    restored = _restore_glossary(protected)
    assert "Anthropic" in restored
    assert "Claude Code" in restored
    assert "智能体式" in restored
    assert "智能体" in restored
    assert "MCP" in restored


def test_technical_article_filter() -> None:
    assert is_technical_article({"title": "The evolution of agentic surfaces: building with Claude Managed Agents"})
    assert is_technical_article({"title": "Steering Claude Code: skills, hooks, and subagents"})
    assert is_technical_article({"title": "Building agents that reach production systems with MCP"})
    assert not is_technical_article({"title": "How Anthropic's Growth Marketing team uses Claude Code"})
    assert not is_technical_article({"title": "Working at the frontier: How Cognition trusts Claude Fable 5"})


def test_translated_article_path_uses_safe_chinese_title() -> None:
    path = translated_article_path("2026-06-10", '构建智能体：API/SDK 的“方法”？', "02-智能体与多智能体系统")

    assert path.as_posix() == "文章/02-智能体与多智能体系统/2026-06-10-构建智能体：API／SDK 的“方法”？/构建智能体：API／SDK 的“方法”？.md"


def test_technical_module_classification() -> None:
    assert technical_module({"source_url": "https://claude.com/blog/subagents-in-claude-code"}) == "02-智能体与多智能体系统"
    assert technical_module({"source_url": "https://claude.com/blog/skills-explained"}) == "03-Skills、MCP 与工具生态"
    assert technical_module({"source_url": "https://claude.com/blog/zero-trust-for-ai-agents"}) == "05-安全、身份与合规"
