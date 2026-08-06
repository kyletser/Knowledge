from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify

from claude_blog_sync.models import Article


ARTICLE_BODY_SELECTORS = (
    "main#main section.blog_post_section_wrap div.u-rich-text-blog.w-richtext",
    ".blog_post_content_wrap .u-rich-text-blog.w-richtext",
    "[itemprop='articleBody']",
)


def parse_sitemap(xml_text: str) -> list[str]:
    """Return canonical-looking English article URLs from Claude's sitemap."""
    root = ET.fromstring(xml_text)
    urls: set[str] = set()
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "loc" or not element.text:
            continue
        raw_url = element.text.strip()
        parsed = urlsplit(raw_url)
        path_parts = [part for part in parsed.path.split("/") if part]
        if (
            parsed.scheme == "https"
            and parsed.hostname == "claude.com"
            and len(path_parts) == 2
            and path_parts[0] == "blog"
        ):
            urls.add(urlunsplit(("https", "claude.com", parsed.path.rstrip("/"), "", "")))
    return sorted(urls)


def _walk_json_ld(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        graph = value.get("@graph")
        if graph is not None:
            yield from _walk_json_ld(graph)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_json_ld(item)


def _blog_posting_json_ld(soup: BeautifulSoup) -> dict[str, Any]:
    for script in soup.select("script[type='application/ld+json']"):
        raw = script.string or script.get_text()
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for item in _walk_json_ld(payload):
            item_type = item.get("@type")
            types = {item_type} if isinstance(item_type, str) else set(item_type or [])
            if types.intersection({"BlogPosting", "Article", "NewsArticle"}):
                return item
    return {}


def _meta_content(soup: BeautifulSoup, *, name: str | None = None, prop: str | None = None) -> str | None:
    selector = f"meta[name='{name}']" if name else f"meta[property='{prop}']"
    node = soup.select_one(selector)
    value = node.get("content") if node else None
    return str(value).strip() if value else None


def _iso_date(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        return candidate
    try:
        return datetime.fromisoformat(candidate.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass
    for date_format in ("%b %d, %Y", "%B %d, %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(candidate, date_format).date().isoformat()
        except ValueError:
            continue
    return None


def _unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = re.sub(r"\s+", " ", value).strip()
        if clean and clean.casefold() not in seen:
            result.append(clean)
            seen.add(clean.casefold())
    return result


def _extract_details(soup: BeautifulSoup) -> dict[str, list[str]]:
    details: dict[str, list[str]] = {}
    for item in soup.select(".hero_blog_post_details_item"):
        content = item.select_one(".hero_blog_post_details_content")
        if content is None:
            continue
        label_node = content.select_one(".u-text-style-caption")
        if label_node is None:
            continue
        label = re.sub(r"\s+", " ", label_node.get_text(" ", strip=True)).strip()
        strings = list(content.stripped_strings)
        if strings and strings[0].strip().casefold() == label.casefold():
            strings = strings[1:]
        values = _unique(strings)
        if label and values:
            details[label] = values
    return details


def _detail_values(details: dict[str, list[str]], *labels: str) -> list[str]:
    wanted = {label.casefold().replace(" ", "") for label in labels}
    for key, values in details.items():
        normalized = key.casefold().replace(" ", "")
        if normalized in wanted:
            return values
    return []


def _authors(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        name = value.get("name")
        return [str(name)] if name else []
    if isinstance(value, list):
        names: list[str] = []
        for item in value:
            names.extend(_authors(item))
        return _unique(names)
    return []


def _is_hidden(node: Tag) -> bool:
    current: Tag | None = node
    while isinstance(current, Tag):
        classes = current.get("class") or []
        if "w-condition-invisible" in classes or current.has_attr("hidden"):
            return True
        current = current.parent if isinstance(current.parent, Tag) else None
    return False


def _select_body(soup: BeautifulSoup) -> Tag:
    candidates: list[Tag] = []
    for selector in ARTICLE_BODY_SELECTORS:
        candidates.extend(
            node
            for node in soup.select(selector)
            if isinstance(node, Tag)
            and not _is_hidden(node)
            and len(node.get_text(" ", strip=True)) >= 200
        )
        if candidates:
            break
    if not candidates:
        raise ValueError("未找到非隐藏的 Claude Blog 正文容器，页面结构可能已经变化")
    return max(candidates, key=lambda node: len(node.get_text(" ", strip=True)))


def extract_article(html: str, source_url: str) -> Article:
    soup = BeautifulSoup(html, "html.parser")
    structured = _blog_posting_json_ld(soup)
    body = _select_body(soup)

    canonical_node = soup.select_one("link[rel='canonical']")
    canonical = str(canonical_node.get("href", "")).strip() if canonical_node else ""
    main_entity = structured.get("mainEntityOfPage")
    if not canonical and isinstance(main_entity, dict):
        canonical = str(main_entity.get("@id", "")).strip()
    canonical = urljoin(source_url, canonical or source_url)

    title = str(structured.get("headline", "")).strip()
    if not title:
        heading = soup.select_one("main#main h1")
        title = heading.get_text(" ", strip=True) if heading else ""
    if not title:
        title = _meta_content(soup, prop="og:title") or ""
        title = re.sub(r"\s*\|\s*Claude by Anthropic\s*$", "", title)
    if not title:
        raise ValueError("未能提取文章标题")

    details = _extract_details(soup)
    published_at = _iso_date(structured.get("datePublished"))
    if published_at is None:
        visible_dates = _detail_values(details, "Date", "Published", "Published date")
        published_at = _iso_date(visible_dates[0]) if visible_dates else None
    description = str(structured.get("description", "")).strip() or _meta_content(soup, name="description")
    image = structured.get("image") or _meta_content(soup, prop="og:image")
    if isinstance(image, list):
        image = image[0] if image else None
    if isinstance(image, dict):
        image = image.get("url")

    return Article(
        source_url=source_url,
        canonical_url=canonical,
        title=title,
        description=description or None,
        published_at=published_at,
        modified_at=_iso_date(structured.get("dateModified")),
        cover_image_url=str(image).strip() if image else None,
        categories=_detail_values(details, "Category", "Categories"),
        products=_detail_values(details, "Product", "Products"),
        use_cases=_detail_values(details, "Use case", "Usecase", "Use cases"),
        authors=_authors(structured.get("author")),
        details=details,
        body_html=str(body),
    )


def _clean_url(value: str, base_url: str) -> str:
    stripped = value.strip()
    lowered = stripped.casefold()
    if lowered.startswith("javascript:"):
        return ""
    if stripped.startswith("#") or lowered.startswith(("mailto:", "tel:")):
        return stripped
    return urljoin(base_url, stripped)


def prepare_body_html(
    body_html: str,
    base_url: str,
    localize_image: Callable[[str, int], str] | None = None,
) -> str:
    """Clean a body fragment, resolve URLs, and optionally localize images."""
    fragment = BeautifulSoup(body_html, "html.parser")
    container = fragment.select_one(".u-rich-text-blog.w-richtext") or fragment

    for unwanted in list(container.select("script, style, noscript, template, .w-condition-invisible")):
        unwanted.decompose()

    for iframe in list(container.find_all("iframe")):
        src = _clean_url(str(iframe.get("src", "")), base_url)
        title = str(iframe.get("title", "Video")).strip() or "Video"
        replacement = fragment.new_tag("p")
        if src:
            link = fragment.new_tag("a", href=src)
            link.string = f"Video: {title}"
            replacement.append(link)
        else:
            replacement.string = f"Video: {title}"
        figure = iframe.find_parent("figure")
        if figure is not None and figure in container.descendants:
            figure.replace_with(replacement)
        else:
            iframe.replace_with(replacement)

    for link in container.find_all("a", href=True):
        cleaned = _clean_url(str(link.get("href", "")), base_url)
        if cleaned:
            link["href"] = cleaned
        else:
            del link["href"]

    for index, image in enumerate(container.find_all("img"), start=1):
        source = image.get("src") or image.get("data-src")
        if source:
            absolute = _clean_url(str(source), base_url)
            image["src"] = localize_image(absolute, index) if localize_image else absolute
        image.attrs.pop("srcset", None)
        image.attrs.pop("sizes", None)
        image.attrs.pop("data-src", None)

    allowed_attributes: dict[str, set[str]] = {
        "a": {"href", "title"},
        "img": {"src", "alt", "title"},
        "code": {"class"},
        "pre": {"class"},
        "td": {"colspan", "rowspan"},
        "th": {"colspan", "rowspan"},
        "ol": {"start"},
    }
    for tag in container.find_all(True):
        allowed = allowed_attributes.get(tag.name, set())
        tag.attrs = {key: value for key, value in tag.attrs.items() if key in allowed}

    return container.decode_contents().strip()


def html_to_markdown(body_html: str) -> str:
    converted = markdownify(body_html, heading_style="ATX", bullets="-")
    converted = converted.replace("\xa0", " ").replace("\r\n", "\n")
    converted = re.sub(r"[ \t]+\n", "\n", converted)
    converted = re.sub(r"\n{3,}", "\n\n", converted)
    return converted.strip() + "\n"
