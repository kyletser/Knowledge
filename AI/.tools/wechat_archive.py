#!/usr/bin/env python3
"""Archive WeChat Official Account articles as Markdown with embedded HTML."""

from __future__ import annotations

import argparse
import hashlib
import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag, NavigableString
from markdownify import markdownify


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
CSS_URL = re.compile(r"url\((['\"]?)(https?://[^)'\"\s]+)\1\)", re.IGNORECASE)
PROMO_RE = re.compile(
    r"扫码|二维码|长按识别|关注我们|关注公众号|在看|点赞本文|分享到|阅读原文|"
    r"后台回复|转载请|版权声明|精彩推荐|往期回顾|点击上方蓝字|订阅|更多精彩|推荐阅读",
    re.I,
)
WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def safe_filename(title: str) -> str:
    name = INVALID_FILENAME.sub("：", title).strip().rstrip(". ")
    name = re.sub(r"\s+", " ", name)
    if not name:
        name = "未命名文章"
    if name.upper() in WINDOWS_RESERVED:
        name = f"_{name}"
    return name[:180].rstrip(". ")


def first_text(soup: BeautifulSoup, selectors: tuple[str, ...]) -> str:
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            value = node.get("content", "") if node.name == "meta" else node.get_text(" ", strip=True)
            if value:
                return str(value).strip()
    return ""


def image_extension(response: requests.Response, url: str) -> str:
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    extension = mimetypes.guess_extension(content_type) if content_type else None
    if extension == ".jpe":
        extension = ".jpg"
    if extension:
        return extension
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if re.fullmatch(r"\.[a-z0-9]{1,5}", suffix) else ".img"


def download_asset(session: requests.Session, url: str, asset_dir: Path) -> Path:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    digest = hashlib.md5(url.encode("utf-8")).hexdigest()
    target = asset_dir / f"{digest}{image_extension(response, url)}"
    if not target.exists():
        target.write_bytes(response.content)
    return target


def localize_url(
    session: requests.Session,
    url: str,
    asset_dir: Path,
    output_dir: Path,
    cache: dict[str, str],
) -> str:
    absolute_url = urljoin("https://mp.weixin.qq.com/", url)
    if not absolute_url.startswith(("http://", "https://")):
        return url
    if absolute_url in cache:
        return cache[absolute_url]
    try:
        target = download_asset(session, absolute_url, asset_dir)
        relative = target.relative_to(output_dir).as_posix()
        cache[absolute_url] = f"./{relative}"
    except requests.RequestException as exc:
        print(f"警告：资源下载失败，保留远程链接：{absolute_url}（{exc}）", file=sys.stderr)
        cache[absolute_url] = absolute_url
    return cache[absolute_url]


def localize_content(
    content: Tag,
    session: requests.Session,
    asset_dir: Path,
    output_dir: Path,
) -> None:
    cache: dict[str, str] = {}
    for image in content.select("img"):
        source = image.get("data-src") or image.get("src")
        if source:
            image["src"] = localize_url(session, str(source), asset_dir, output_dir, cache)
            image["data-src"] = image["src"]
        image.attrs.pop("srcset", None)

    for node in content.find_all(style=True):
        style = str(node.get("style", ""))

        def replace_css_url(match: re.Match[str]) -> str:
            localized = localize_url(session, match.group(2), asset_dir, output_dir, cache)
            return f"url('{localized}')"

        node["style"] = CSS_URL.sub(replace_css_url, style)

    for node in content.find_all(True):
        for attr in ("data-lazy-bgimg", "data-bgurl"):
            value = node.get(attr)
            if value:
                localized = localize_url(session, str(value), asset_dir, output_dir, cache)
                node[attr] = localized
                style = str(node.get("style", "")).rstrip(";")
                node["style"] = f"{style};background-image:url('{localized}')"


def strip_promo(content: Tag) -> int:
    """删除 #js_content 末尾的推广/二维码区域。

    策略：只在正文「末尾若干块」里查找最后一个命中 PROMO_RE 的块，然后从该块起
    一直删到末尾（推广永远在文末，其后通常是空壳 section / 隐藏 <p> 等 footer）。
    只有命中推广词才判定为推广，避免误删正文中偶发的「关注/点赞」等词或尾部配图。
    返回删除节点数。
    """
    children = [c for c in content.children if isinstance(c, Tag)]
    if not children:
        return 0
    # 仅在末尾最多 10 个块中查找，降低正文内偶现推广词的误判
    tail = children[-10:]
    promo_idx = -1
    for offset, child in enumerate(tail):
        text = child.get_text(" ", strip=True)
        if text and PROMO_RE.search(text):
            promo_idx = len(children) - len(tail) + offset
            break
    if promo_idx == -1:
        return 0
    for child in children[promo_idx:]:
        child.decompose()
    return len(children) - promo_idx


def fetch_article(session: requests.Session, url: str) -> tuple[BeautifulSoup, str]:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    text = response.content.decode("utf-8", errors="replace")
    if any(marker in text for marker in ("访问过于频繁", "环境异常", "验证码")):
        raise RuntimeError("微信返回了访问限制或验证码页面，请稍后重试")
    return BeautifulSoup(text, "html.parser"), response.url


def add_daoyu_label(md: str) -> str:
    """把开头「导语引文 + 目录列表」整体包进一个 > **导语**：blockquote，对齐旧文样式。

    - 起点：--- 之后跳过首图，第一个 > 块（导语引文）或目录块（**目录** / 一、二、… / N.）
    - 终点：连续的导语/目录条目末行
    - 已存在 > **导语**： 时幂等跳过
    """
    if "> **导语**：" in md:
        return md
    lines = md.split("\n")
    try:
        dash = next(i for i, ln in enumerate(lines) if ln.strip() == "---")
    except StopIteration:
        return md
    # 跳过 --- 之后的空行与首图
    i = dash + 1
    while i < len(lines) and (lines[i].strip() == "" or lines[i].startswith("![")):
        i += 1
    if i >= len(lines):
        return md
    start = i
    toc_re = re.compile(r"^[一二三四五六七八九十百]+、|^\d+\.\s|^\*\*目录\*\*|^> ")
    end = start
    j = start
    if lines[start].startswith("> "):
        # 导语引文块：吃下连续 > 行（含空 > 行）
        while j < len(lines) and (lines[j].startswith("> ") or lines[j].strip() in ("", ">")):
            end = j
            j += 1
        # 其后若紧跟目录列表，一并并入
        while j < len(lines) and toc_re.match(lines[j]):
            end = j
            j += 1
    else:
        # 非 > 块：吃下连续的目录条目（含 **目录** 行）
        while j < len(lines) and toc_re.match(lines[j]):
            end = j
            j += 1
    if end < start:
        return md

    block = ["> **导语**："]
    for k in range(start, end + 1):
        ln = lines[k]
        if ln.strip() in ("", ">"):
            block.append(">")
        elif ln.startswith("> "):
            block.append(ln)
        else:
            block.append("> " + ln)
    return "\n".join(lines[:start] + block + lines[end + 1:])


def polish_markdown(md: str) -> str:
    """后处理：对齐现有 md 约定（# 标题 + ### 小节），清理转换噪声。

    - 删除空标题行（微信偶发空 <h1>）
    - 正文内 h1 降级为 h3（对齐现有 ### 小节风格）
    - 把独立的「N. 问题」段落提升为 ### 标题（跳过连续的目录列表）
    - 提升独立的中文章节词（结语/总结/等）为 ### 标题
    - 清除 <br> 硬换行留下的行尾空格、折叠多余空行
    """
    parts = re.split(r"\n---\n", md, maxsplit=1)
    header = parts[0]
    body = parts[1] if len(parts) > 1 else ""

    lines = body.split("\n")
    # 1) 删除空标题行
    lines = [ln for ln in lines if not re.match(r"^#{1,6}[ \t]*$", ln)]
    # 2) 正文内 h1 -> h3（标题 # 在 header 中，不受影响）
    lines = [re.sub(r"^# ", "### ", ln, count=1) if re.match(r"^# ", ln) else ln for ln in lines]

    # 3) 提升独立的「N. 问题」为 ### 标题；连续 >=3 行的视为目录列表，跳过
    is_q = [bool(re.match(r"^\d+\.\s", ln)) for ln in lines]
    n = len(lines)
    skip = [False] * n
    i = 0
    while i < n:
        if is_q[i]:
            j = i
            while j < n and is_q[j]:
                j += 1
            if (j - i) >= 3:
                for k in range(i, j):
                    skip[k] = True
            i = j
        else:
            i += 1
    out = []
    for idx, ln in enumerate(lines):
        if is_q[idx] and not skip[idx]:
            out.append(re.sub(r"^(\d+\.\s)", r"### \1", ln, count=1))
        else:
            out.append(ln)
    lines = out

    # 4) 提升独立的中文章节词为 ### 标题
    section_kw = re.compile(r"^(结语|总结|后记|尾声|番外|附录|参考资料?|References)$")
    lines = [("### " + ln) if section_kw.match(ln) else ln for ln in lines]

    # 5) 清理行尾空格（含 <br> 硬换行）并折叠空行
    body = "\n".join(lines)
    body = re.sub(r"[ \t]+\n", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    md = (header + "\n---\n\n" + body + "\n") if body else (header + "\n")
    return add_daoyu_label(md)


def archive_one(
    session: requests.Session,
    url: str,
    output_dir: Path,
    overwrite: bool,
) -> Path:
    soup, final_url = fetch_article(session, url)
    content = soup.select_one("#js_content")
    if not content:
        raise RuntimeError("页面中没有找到公众号正文（#js_content）")
    strip_promo(content)
    original_text = content.get_text()

    title = first_text(soup, ("#activity-name", 'meta[property="og:title"]', "title"))
    filename = safe_filename(title)
    output_path = output_dir / f"{filename}.md"
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"文件已存在：{output_path.name}；如需替换请使用 --overwrite")

    author = first_text(soup, ("#js_author_name", "#js_name", 'meta[name="author"]'))
    publish_time = first_text(soup, ("#publish_time", "#js_publish_time"))
    asset_dir = output_dir / "assets" / filename
    asset_dir.mkdir(parents=True, exist_ok=True)
    localize_content(content, session, asset_dir, output_dir)
    if content.get_text() != original_text:
        raise RuntimeError("本地化资源时正文发生变化，已停止写入以避免内容丢失")

    metadata = [f"# {title or filename}", ""]
    if author:
        metadata.append(f"> 公众号：{author}")
    if publish_time:
        metadata.append(f"> 发布时间：{publish_time}")
    metadata.extend((f"> 原文链接：[{final_url}]({final_url})", "", "---", ""))

    article_html = content.decode_contents(formatter="minimal").strip()
    (asset_dir / "original.html").write_text(article_html, encoding="utf-8")
    article_markdown = markdownify(
        article_html,
        heading_style="ATX",
        bullets="-",
        strip=["svg", "mp-style-type"],
    )
    article_markdown = re.sub(r"\n{3,}", "\n\n", article_markdown).strip()
    markdown = "\n".join(metadata) + "\n\n" + article_markdown + "\n"
    markdown = polish_markdown(markdown)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="批量把微信公众号文章保存为保留原始 HTML 排版的 Markdown 文件"
    )
    parser.add_argument("urls", nargs="+", help="一个或多个 mp.weixin.qq.com 文章链接")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path.cwd(), help="输出目录")
    parser.add_argument("--overwrite", action="store_true", help="覆盖同名 Markdown 文件")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://mp.weixin.qq.com/",
        }
    )

    failed = 0
    for url in args.urls:
        try:
            path = archive_one(session, url, output_dir, args.overwrite)
            print(f"已保存：{path}")
        except Exception as exc:
            failed += 1
            print(f"失败：{url}\n  {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
