from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

from claude_blog_sync.extract import html_to_markdown


TRANSLATE_URL = "https://clients5.google.com/translate_a/t"
TRANSLATION_ENGINE = "Google Translate public web endpoint"
TRANSLATION_VERSION = 5
SEPARATOR = "ZXQSEPARATOR9F3A2C0DQXZ"
SKIP_TAGS = {"code", "pre", "kbd", "samp", "script", "style", "noscript", "template"}
TRANSLATABLE_METADATA = {"title", "description", "categories", "products", "use_cases", "details"}

TECHNICAL_TITLE_PATTERN = re.compile(
    r"claude code|\bagents?\b|agentic|subagents?|\bmcp\b|\bapi\b|\bsdk\b|connector|"
    r"engineering|source code|codebases?|security|cybersecurity|threat detection|zero trust|"
    r"workload identity|prompt caching|\bprompts?\b|\bskills?\b|\bhooks?\b|\bcontext\b|"
    r"web search|cobol|foundation models framework|apps gateway|loop engineering|dynamic workflows|"
    r"computer and browser use|data analytics|field guide to claude|software gets built",
    re.IGNORECASE,
)
NONTECHNICAL_TITLE_PATTERN = re.compile(
    r"working at the frontier|marketing|\bseller\b|sales leader|finance team|financial services|"
    r"legal industry|non-technical|hackathon|code w/ claude|founder['’]s playbook|"
    r"product (?:management|development)|government|admins?|\bspend\b|cowork product guide|"
    r"everyday life|customers discovered|retailers|team updates|finance with|"
    r"deploying .*enterprise|partners are putting|claude security is now|"
    r"security and compliance tools",
    re.IGNORECASE,
)

TECHNICAL_MODULES: tuple[str, ...] = (
    "01-Claude Code 开发实践",
    "02-智能体与多智能体系统",
    "03-Skills、MCP 与工具生态",
    "04-模型能力、上下文与提示工程",
    "05-安全、身份与合规",
    "06-工程方法与技术案例",
)
MODULE_DESCRIPTIONS: dict[str, str] = {
    TECHNICAL_MODULES[0]: "Claude Code 的开发流程、代码审查、工作流和大型代码库实践。",
    TECHNICAL_MODULES[1]: "智能体设计、子智能体、多智能体协作与 Claude Managed Agents。",
    TECHNICAL_MODULES[2]: "Skills、MCP、连接器、API 与 Claude 工具生态。",
    TECHNICAL_MODULES[3]: "模型选择、上下文窗口、提示词与计算机和搜索能力。",
    TECHNICAL_MODULES[4]: "安全工程、身份鉴权、零信任、合规与代码安全。",
    TECHNICAL_MODULES[5]: "AI 原生工程方法、组织实践、现代化与技术案例。",
}


GLOSSARY: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bfinancial diligence\b", re.IGNORECASE), "财务尽调"),
    (re.compile(r"\bdue diligence\b", re.IGNORECASE), "尽职调查"),
    (re.compile(r"\bClaude Managed Agents\b", re.IGNORECASE), "Claude Managed Agents"),
    (re.compile(r"\bClaude Agent SDK\b", re.IGNORECASE), "Claude Agent SDK"),
    (re.compile(r"\bClaude Code\b", re.IGNORECASE), "Claude Code"),
    (re.compile(r"\bClaude Cowork\b", re.IGNORECASE), "Claude Cowork"),
    (re.compile(r"\bClaude Platform\b", re.IGNORECASE), "Claude Platform"),
    (re.compile(r"\bAmazon Bedrock\b", re.IGNORECASE), "Amazon Bedrock"),
    (re.compile(r"\bGoogle Cloud\b", re.IGNORECASE), "Google Cloud"),
    (re.compile(r"\bMicrosoft Foundry\b", re.IGNORECASE), "Microsoft Foundry"),
    (re.compile(r"\bAnthropic\b", re.IGNORECASE), "Anthropic"),
    (re.compile(r"\bHebbia\b", re.IGNORECASE), "Hebbia"),
    (re.compile(r"\bClaude\b", re.IGNORECASE), "Claude"),
    (re.compile(r"\bGitHub\b", re.IGNORECASE), "GitHub"),
    (re.compile(r"\bPowerPoint\b", re.IGNORECASE), "PowerPoint"),
    (re.compile(r"\bMicrosoft\b", re.IGNORECASE), "Microsoft"),
    (re.compile(r"\bExcel\b", re.IGNORECASE), "Excel"),
    (re.compile(r"\bOutlook\b", re.IGNORECASE), "Outlook"),
    (re.compile(r"\bSlack\b", re.IGNORECASE), "Slack"),
    (re.compile(r"\bOpus\b", re.IGNORECASE), "Opus"),
    (re.compile(r"\bSonnet\b", re.IGNORECASE), "Sonnet"),
    (re.compile(r"\bHaiku\b", re.IGNORECASE), "Haiku"),
    (re.compile(r"\bFable\b", re.IGNORECASE), "Fable"),
    (re.compile(r"\bMythos\b", re.IGNORECASE), "Mythos"),
    (re.compile(r"\bMCP\b"), "MCP"),
    (re.compile(r"\bLLMs\b", re.IGNORECASE), "LLM"),
    (re.compile(r"\bLLM\b", re.IGNORECASE), "LLM"),
    (re.compile(r"\bRAG\b"), "RAG"),
    (re.compile(r"\bCRM\b"), "CRM"),
    (re.compile(r"\bCLI\b"), "CLI"),
    (re.compile(r"\bIDE\b"), "IDE"),
    (re.compile(r"\bAPI\b"), "API"),
    (re.compile(r"\bSDK\b"), "SDK"),
    (re.compile(r"\bAI\b"), "AI"),
    (re.compile(r"\bslide decks\b", re.IGNORECASE), "演示文稿"),
    (re.compile(r"\bslide deck\b", re.IGNORECASE), "演示文稿"),
    (re.compile(r"\bdecks\b", re.IGNORECASE), "演示文稿"),
    (re.compile(r"\bdeck\b", re.IGNORECASE), "演示文稿"),
    (re.compile(r"\bmodels\b", re.IGNORECASE), "模型"),
    (re.compile(r"\bmodel\b", re.IGNORECASE), "模型"),
    (re.compile(r"\bagents['’]", re.IGNORECASE), "智能体的"),
    (re.compile(r"\bagent['’]s\b", re.IGNORECASE), "智能体的"),
    (re.compile(r"\bagentic\b", re.IGNORECASE), "智能体式"),
    (re.compile(r"\bagents\b", re.IGNORECASE), "智能体"),
    (re.compile(r"\bagent\b", re.IGNORECASE), "智能体"),
    (re.compile(r"\bprompt caching\b", re.IGNORECASE), "提示词缓存"),
    (re.compile(r"\bprompts\b", re.IGNORECASE), "提示词"),
    (re.compile(r"\bprompt\b", re.IGNORECASE), "提示词"),
]
TOKEN_TARGETS = {f"ZXQTERM{index:04d}QXZ": target for index, (_pattern, target) in enumerate(GLOSSARY)}


class TranslatorProtocol(Protocol):
    cache: dict[str, str]

    def translate_one(self, text: str) -> str: ...

    def translate_many(self, texts: list[str]) -> dict[str, str]: ...


@dataclass(slots=True)
class TranslationResult:
    discovered: int = 0
    queued: int = 0
    translated: int = 0
    skipped: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)


def is_technical_article(entry: dict[str, Any]) -> bool:
    title = html.unescape(str(entry.get("title") or ""))
    return bool(TECHNICAL_TITLE_PATTERN.search(title)) and not bool(NONTECHNICAL_TITLE_PATTERN.search(title))


def technical_module(entry: dict[str, Any]) -> str:
    text = html.unescape(f"{entry.get('source_url') or ''} {entry.get('title') or ''}").casefold()
    if re.search(
        r"security|cybersecurity|secure-source-code|zero-trust|workload-identity|"
        r"compliance-api|managed-auth|agent-identity-access",
        text,
    ):
        return TECHNICAL_MODULES[4]
    if re.search(r"building-agents-with-skills|skill|mcp|connector|apps-gateway|foundation-models|artifacts", text):
        return TECHNICAL_MODULES[2]
    if re.search(
        r"1m-context|model-and-effort|field-guide|web-search|computer-and-browser|"
        r"prompt-caching|best-practices-for-using-claude-opus",
        text,
    ):
        return TECHNICAL_MODULES[3]
    if re.search(
        r"managed-agent|multi-agent|subagents|harness|advisor|building-ai-agents|"
        r"human-agent|orchestration-system|common-workflow-patterns-for-ai-agents",
        text,
    ):
        return TECHNICAL_MODULES[1]
    if re.search(
        r"claude-code|code-review|preview-review|auto-mode|contribution-metrics|routines|"
        r"dynamic-workflows|seeing-like-an-agent|agent-view",
        text,
    ):
        return TECHNICAL_MODULES[0]
    if "interactive-tools-in-claude" in text:
        return TECHNICAL_MODULES[2]
    return TECHNICAL_MODULES[5]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, value: Any) -> None:
    _atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _should_translate(text: str) -> bool:
    stripped = text.strip()
    if not stripped or not re.search(r"[A-Za-z]", stripped):
        return False
    if re.fullmatch(r"(?:https?://|mailto:)[^\s]+", stripped, re.IGNORECASE):
        return False
    return True


def _protect_glossary(text: str) -> str:
    protected = text
    for index, (pattern, _target) in enumerate(GLOSSARY):
        protected = pattern.sub(f"ZXQTERM{index:04d}QXZ", protected)
    return protected


def _restore_glossary(text: str) -> str:
    restored = text
    for token, target in TOKEN_TARGETS.items():
        restored = restored.replace(token, target)
        if re.search(r"[\u3400-\u9fff]", target):
            restored = re.sub(rf"\s*{re.escape(target)}\s*", target, restored)
    return restored


def _needs_individual_retry(source: str, translated: str) -> bool:
    """Detect batching artifacts that leave most of a sentence in English."""
    if len(re.findall(r"[A-Za-z]{2,}", source)) < 4:
        return False
    candidate = translated
    for target in TOKEN_TARGETS.values():
        if re.fullmatch(r"[A-Za-z0-9 .+&'’-]+", target):
            candidate = re.sub(re.escape(target), "", candidate, flags=re.IGNORECASE)
    english_letters = len(re.findall(r"[A-Za-z]", candidate))
    chinese_chars = len(re.findall(r"[\u3400-\u9fff]", candidate))
    english_words = len(re.findall(r"[A-Za-z]{2,}", candidate))
    return english_words >= 4 and english_letters > max(12, chinese_chars)


def _split_long_text(text: str, maximum: int) -> list[str]:
    chunks: list[str] = []
    remaining = text
    while len(remaining) > maximum:
        cut = remaining.rfind(" ", 0, maximum + 1)
        if cut < maximum // 2:
            cut = maximum
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks or [text]


class GoogleWebTranslator:
    def __init__(
        self,
        cache: dict[str, str] | None = None,
        delay: float = 0.25,
        retries: int = 5,
        timeout: float = 30.0,
        maximum_batch_chars: int = 3000,
    ) -> None:
        self.cache = cache if cache is not None else {}
        self.delay = max(0.0, delay)
        self.retries = max(0, retries)
        self.timeout = timeout
        self.maximum_batch_chars = maximum_batch_chars
        self.last_request_at = 0.0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Knowledge-ClaudeBlogTranslator/0.1"})

    def close(self) -> None:
        self.session.close()

    def _request(self, text: str) -> str:
        for attempt in range(self.retries + 1):
            elapsed = time.monotonic() - self.last_request_at
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
            try:
                response = self.session.post(
                    TRANSLATE_URL,
                    params={"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t"},
                    data={"q": text},
                    timeout=self.timeout,
                )
                self.last_request_at = time.monotonic()
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, list) and payload and isinstance(payload[0], str):
                    return "".join(item for item in payload if isinstance(item, str))
                segments = payload[0] if isinstance(payload, list) and payload else None
                if not isinstance(segments, list):
                    raise ValueError("翻译服务返回了未知格式")
                return "".join(
                    str(segment[0])
                    for segment in segments
                    if isinstance(segment, list) and segment and segment[0] is not None
                )
            except (requests.RequestException, ValueError, json.JSONDecodeError):
                if attempt >= self.retries:
                    raise
                time.sleep(min(30.0, 2.0**attempt))
        raise RuntimeError("翻译请求未执行")

    def _translate_batch(self, texts: list[str]) -> list[str]:
        if not texts:
            return []
        if len(texts) == 1:
            return [_restore_glossary(self._request(texts[0]).strip())]
        payload = f"\n{SEPARATOR}\n".join(texts)
        translated = self._request(payload)
        parts = re.split(rf"\s*{re.escape(SEPARATOR)}\s*", translated.strip())
        if len(parts) != len(texts):
            return [_restore_glossary(self._request(text).strip()) for text in texts]
        return [_restore_glossary(part.strip()) for part in parts]

    def translate_many(self, texts: list[str]) -> dict[str, str]:
        ordered_unique = list(dict.fromkeys(texts))
        result: dict[str, str] = {}
        units: list[tuple[str, int, str]] = []
        parts_by_source: dict[str, list[str | None]] = {}

        for source in ordered_unique:
            cache_key = f"v{TRANSLATION_VERSION}:{source}"
            if cache_key in self.cache:
                result[source] = self.cache[cache_key]
                continue
            if not _should_translate(source):
                self.cache[cache_key] = source
                result[source] = source
                continue
            protected = _protect_glossary(source)
            chunks = _split_long_text(protected, self.maximum_batch_chars)
            parts_by_source[source] = [None] * len(chunks)
            units.extend((source, index, chunk) for index, chunk in enumerate(chunks))

        batch: list[tuple[str, int, str]] = []
        batch_chars = 0

        def flush() -> None:
            nonlocal batch, batch_chars
            if not batch:
                return
            translated_parts = self._translate_batch([item[2] for item in batch])
            for (source, part_index, _chunk), translated_part in zip(batch, translated_parts, strict=True):
                parts_by_source[source][part_index] = translated_part
            batch = []
            batch_chars = 0

        for unit in units:
            added = len(unit[2]) + (len(SEPARATOR) + 2 if batch else 0)
            if batch and batch_chars + added > self.maximum_batch_chars:
                flush()
            batch.append(unit)
            batch_chars += added
        flush()

        for source, translated_parts in parts_by_source.items():
            translated = " ".join(str(part or "") for part in translated_parts).strip()
            if _needs_individual_retry(source, translated):
                translated = _restore_glossary(self._request(_protect_glossary(source)).strip())
            self.cache[f"v{TRANSLATION_VERSION}:{source}"] = translated
            result[source] = translated
        return result

    def translate_one(self, text: str) -> str:
        return self.translate_many([text])[text]


def _translate_json_value(value: Any, translator: TranslatorProtocol) -> Any:
    if isinstance(value, str):
        return translator.translate_one(value)
    if isinstance(value, list):
        strings = [item for item in value if isinstance(item, str)]
        translated_strings = translator.translate_many(strings) if strings else {}
        return [translated_strings[item] if isinstance(item, str) else _translate_json_value(item, translator) for item in value]
    if isinstance(value, dict):
        return {key: _translate_json_value(item, translator) for key, item in value.items()}
    return value


def _split_frontmatter(markdown: str) -> tuple[list[str], str]:
    lines = markdown.replace("\r\n", "\n").split("\n")
    if not lines or lines[0] != "---":
        raise ValueError("源 Markdown 缺少 YAML frontmatter")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("源 Markdown frontmatter 未闭合") from exc
    return lines[1:closing], "\n".join(lines[closing + 1 :])


def _metadata_values(lines: list[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for line in lines:
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        try:
            values[key.strip()] = json.loads(raw.strip())
        except json.JSONDecodeError:
            values[key.strip()] = raw.strip()
    return values


def _replace_html_text(soup: BeautifulSoup, translator: TranslatorProtocol) -> None:
    nodes: list[tuple[NavigableString, str, str, str]] = []
    cores: list[str] = []
    for node in list(soup.find_all(string=True)):
        parent = node.parent
        if not isinstance(parent, Tag) or parent.name in SKIP_TAGS or any(
            isinstance(ancestor, Tag) and ancestor.name in SKIP_TAGS for ancestor in parent.parents
        ):
            continue
        text = str(node)
        match = re.fullmatch(r"(\s*)(.*?)(\s*)", text, flags=re.DOTALL)
        if match is None:
            continue
        prefix, core, suffix = match.groups()
        if not _should_translate(core):
            continue
        nodes.append((node, prefix, core, suffix))
        cores.append(core)
    translations = translator.translate_many(cores)
    for node, prefix, core, suffix in nodes:
        node.replace_with(prefix + translations[core] + suffix)
    _translate_remaining_english_sentences(soup, translator)


def _translate_remaining_english_sentences(soup: BeautifulSoup, translator: TranslatorProtocol) -> None:
    pattern = re.compile(r"(?<![A-Za-z])([A-Z][A-Za-z0-9& ,;:'’\"()\-–—/]{18,}[.!?])")
    pending: list[tuple[NavigableString, list[str]]] = []
    spans: list[str] = []
    for node in list(soup.find_all(string=True)):
        parent = node.parent
        if not isinstance(parent, Tag) or parent.name in SKIP_TAGS or any(
            isinstance(ancestor, Tag) and ancestor.name in SKIP_TAGS for ancestor in parent.parents
        ):
            continue
        matches = [
            match.group(1)
            for match in pattern.finditer(str(node))
            if len(re.findall(r"[A-Za-z]{2,}", match.group(1))) >= 4
        ]
        if matches:
            pending.append((node, matches))
            spans.extend(matches)
    translations = translator.translate_many(spans)
    for node, matches in pending:
        replaced = str(node)
        for source in matches:
            replaced = replaced.replace(source, translations[source])
        node.replace_with(replaced)


def _sanitize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(metadata)
    placeholders = {"No items found.", "No items found", "No item found."}
    products = cleaned.get("products")
    if isinstance(products, list):
        cleaned["products"] = [item for item in products if item not in placeholders]
    details = cleaned.get("details")
    if isinstance(details, dict):
        cleaned_details = dict(details)
        for key in list(cleaned_details):
            value = cleaned_details[key]
            if key.casefold() == "share" or (
                isinstance(value, list) and value and all(item in placeholders for item in value if isinstance(item, str))
            ):
                cleaned_details.pop(key, None)
        cleaned["details"] = cleaned_details
    return cleaned


def translated_article_path(published_at: Any, translated_title: str, module: str | None = None) -> Path:
    date = str(published_at or "undated")[:10]
    replacements = str.maketrans(
        {
            ":": "：",
            "/": "／",
            "\\": "＼",
            "?": "？",
            "*": "＊",
            '"': "”",
            "<": "《",
            ">": "》",
            "|": "｜",
        }
    )
    folder_title = html.unescape(translated_title).translate(replacements)
    folder_title = re.sub(r"[\x00-\x1f]+", "", folder_title)
    folder_title = re.sub(r"\s+", " ", folder_title).strip(" .")
    if not folder_title:
        folder_title = "未命名文章"
    if len(folder_title) > 80:
        folder_title = folder_title[:80].rstrip(" .")
    return Path("文章") / (module or TECHNICAL_MODULES[-1]) / f"{date}-{folder_title}" / f"{folder_title}.md"


def translate_document(
    source_html: str,
    source_markdown: str,
    translator: TranslatorProtocol,
    translated_at: str,
) -> tuple[str, str, str, str]:
    frontmatter_lines, _source_body = _split_frontmatter(source_markdown)
    original_metadata = _sanitize_metadata(_metadata_values(frontmatter_lines))

    soup = BeautifulSoup(source_html, "html.parser")
    _replace_html_text(soup, translator)
    html_tag = soup.find("html")
    if isinstance(html_tag, Tag):
        html_tag["lang"] = "zh-CN"

    translated_metadata: dict[str, Any] = {}
    for key, value in original_metadata.items():
        translated_metadata[key] = _translate_json_value(value, translator) if key in TRANSLATABLE_METADATA else value
    translated_title = str(translated_metadata.get("title") or "")
    translated_description = translated_metadata.get("description")

    if soup.title and translated_title:
        soup.title.string = translated_title
    description_node = soup.select_one("meta[name='description']")
    if isinstance(description_node, Tag) and isinstance(translated_description, str):
        description_node["content"] = translated_description
    head = soup.find("head")
    if isinstance(head, Tag):
        machine_meta = soup.new_tag("meta")
        machine_meta["name"] = "translation"
        machine_meta["content"] = "machine-translated zh-CN"
        head.append(machine_meta)

    article = soup.find("article")
    if not isinstance(article, Tag):
        raise ValueError("源 HTML 中未找到 article")
    body_markdown = html_to_markdown(str(article)).replace("\r\n", "\n")
    body_markdown = re.sub(r"\A\s*# [^\n]+\n+", "", body_markdown, count=1)
    body_markdown = re.sub(
        r"\A[^\n]*\]\(https://claude\.com/blog/[^)]+\)\s*\n+",
        "",
        body_markdown,
        count=1,
    )
    source_url = str(original_metadata.get("source_url") or original_metadata.get("canonical_url") or "")
    published_at = str(original_metadata.get("published_at") or "")
    source_link = f"[原文链接]({source_url})" if source_url else "原文链接未记录"
    translated_markdown = (
        f"# {translated_title}\n\n"
        f"> 发布日期：{published_at} · {source_link} · 机器翻译，仅供学习。\n\n"
        f"{body_markdown.lstrip()}"
    )
    translation_hash = hashlib.sha256(translated_markdown.encode("utf-8")).hexdigest()
    return str(soup), translated_markdown, translated_title, translation_hash


def _copy_images(source_article_dir: Path, target_article_dir: Path) -> None:
    source_images = source_article_dir / "images"
    if not source_images.is_dir():
        return
    target_images = target_article_dir / "images"
    for source_file in source_images.rglob("*"):
        if not source_file.is_file():
            continue
        relative = source_file.relative_to(source_images)
        target_file = target_images / relative
        if target_file.is_file() and target_file.stat().st_size == source_file.stat().st_size:
            continue
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)


def _write_catalog(
    output_dir: Path,
    state: dict[str, Any],
    year: int,
    generated_at: str,
    technical_only: bool = False,
) -> None:
    entries = [
        entry
        for entry in state.get("articles", {}).values()
        if str(entry.get("published_at") or "").startswith(f"{year:04d}-")
        and isinstance(entry.get("path"), str)
        and (output_dir / entry["path"]).is_file()
    ]
    for entry in entries:
        if not entry.get("module"):
            entry["module"] = technical_module(entry)
    entries.sort(key=lambda entry: (str(entry.get("published_at")), str(entry.get("title")).casefold()), reverse=True)
    lines = [
        f"# Claude Blog {year} 年{'技术文章' if technical_only else ''}中文学习库",
        "",
        f"共 {len(entries)} 篇。建议按下面的模块顺序学习；每篇均保留原文链接。",
        "",
        "## 学习路径",
        "",
    ]
    for module in TECHNICAL_MODULES:
        module_entries = [entry for entry in entries if entry.get("module") == module]
        if module_entries:
            lines.append(
                f"- [{module}](<文章/{module}/README.md>)：{MODULE_DESCRIPTIONS[module]}（{len(module_entries)} 篇）"
            )
    for module in TECHNICAL_MODULES:
        module_entries = [entry for entry in entries if entry.get("module") == module]
        if not module_entries:
            continue
        lines.extend(["", f"## {module}", "", "| 发布日期 | 中文标题 | 原文 |", "|---|---|---|"])
        module_lines = [
            f"# {module}",
            "",
            MODULE_DESCRIPTIONS[module],
            "",
            f"共 {len(module_entries)} 篇。建议按发布日期从早到晚学习。",
            "",
            "[返回总学习目录](../../2026-index.md)",
            "",
            "| 发布日期 | 中文标题 | 原文 |",
            "|---|---|---|",
        ]
        for entry in reversed(module_entries):
            title = str(entry.get("title") or "").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
            source_url = str(entry.get("source_url") or "")
            original_link = f"[查看原文]({source_url})" if source_url else ""
            full_path = Path(entry["path"]).as_posix()
            lines.append(f"| {entry.get('published_at')} | [{title}](<{full_path}>) | {original_link} |")
            relative_path = Path(full_path).relative_to(Path("文章") / module).as_posix()
            module_lines.append(
                f"| {entry.get('published_at')} | [{title}](<{relative_path}>) | {original_link} |"
            )
        module_lines.append("")
        _atomic_write_text(output_dir / "文章" / module / "README.md", "\n".join(module_lines))
    lines.append("")
    _atomic_write_text(output_dir / f"{year}-index.md", "\n".join(lines))


def _write_report(output_dir: Path, result: TranslationResult, started_at: str, finished_at: str) -> None:
    lines = [
        "# 中文翻译报告",
        "",
        f"- 开始时间（UTC）：{started_at}",
        f"- 完成时间（UTC）：{finished_at}",
        f"- 发现：{result.discovered}",
        f"- 本次排队：{result.queued}",
        f"- 新翻译：{result.translated}",
        f"- 已跳过：{result.skipped}",
        f"- 失败：{len(result.failures)}",
        f"- 翻译引擎：{TRANSLATION_ENGINE}",
        "",
    ]
    if result.failures:
        lines.extend(["## 失败", ""])
        lines.extend(f"- {url} — {message}" for url, message in result.failures)
        lines.append("")
    _atomic_write_text(output_dir / "translation_report.md", "\n".join(lines))


def translate_archive(
    source_dir: Path,
    output_dir: Path,
    year: int = 2026,
    limit: int | None = None,
    force: bool = False,
    delay: float = 0.25,
    retries: int = 5,
    timeout: float = 30.0,
    technical_only: bool = False,
    log=print,
) -> TranslationResult:
    if not 2000 <= year <= 2100:
        raise ValueError("year 必须在 2000 到 2100 之间")
    if limit is not None and limit < 0:
        raise ValueError("limit 不能小于 0")
    source_dir = source_dir.resolve()
    output_dir = output_dir.resolve()
    if source_dir == output_dir:
        raise ValueError("中文输出目录必须与英文源目录不同")

    source_state = _load_json(source_dir / "state.json", None)
    if not isinstance(source_state, dict) or not isinstance(source_state.get("articles"), dict):
        raise ValueError(f"无效的英文归档状态文件: {source_dir / 'state.json'}")
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "translation_state.json"
    cache_path = output_dir / ".translation_cache.json"
    translation_state = _load_json(state_path, {"version": 1, "articles": {}})
    cache = _load_json(cache_path, {})
    if not isinstance(translation_state.get("articles"), dict) or not isinstance(cache, dict):
        raise ValueError("中文翻译状态文件格式无效")

    entries = [
        (url, entry)
        for url, entry in source_state["articles"].items()
        if str(entry.get("published_at") or "").startswith(f"{year:04d}-")
        and (not technical_only or is_technical_article(entry))
    ]
    entries.sort(key=lambda item: (str(item[1].get("published_at")), str(item[1].get("title")).casefold()), reverse=True)
    result = TranslationResult(discovered=len(entries))
    candidates: list[tuple[str, dict[str, Any]]] = []
    for url, entry in entries:
        source_relative_index = entry.get("path")
        translated_entry = translation_state["articles"].get(url)
        translated_relative_index = translated_entry.get("path") if isinstance(translated_entry, dict) else None
        complete = (
            isinstance(source_relative_index, str)
            and isinstance(translated_relative_index, str)
            and (output_dir / translated_relative_index).is_file()
            and translated_entry is not None
            and translated_entry.get("source_content_hash") == entry.get("content_hash")
            and translated_entry.get("translation_version") == TRANSLATION_VERSION
        )
        if force or not complete:
            candidates.append((url, entry))
        else:
            _copy_images(
                (source_dir / source_relative_index).parent,
                (output_dir / translated_relative_index).parent,
            )
            result.skipped += 1
    if limit is not None:
        candidates = candidates[:limit]
    result.queued = len(candidates)
    started_at = utc_now()
    translator = GoogleWebTranslator(cache=cache, delay=delay, retries=retries, timeout=timeout)
    log(f"发现 {result.discovered} 篇；本次翻译 {result.queued} 篇；跳过 {result.skipped} 篇")

    try:
        for position, (url, entry) in enumerate(candidates, start=1):
            log(f"[{position}/{len(candidates)}] {entry.get('title') or url}")
            try:
                relative_index = entry.get("path")
                if not isinstance(relative_index, str):
                    raise ValueError("英文状态中缺少文章路径")
                source_index = source_dir / relative_index
                source_html = source_index.with_name("content.html")
                if not source_index.is_file() or not source_html.is_file():
                    raise FileNotFoundError(f"英文文章文件不完整: {source_index}")
                translated_at = utc_now()
                _translated_html, translated_markdown, translated_title, translation_hash = translate_document(
                    source_html.read_text(encoding="utf-8"),
                    source_index.read_text(encoding="utf-8"),
                    translator,
                    translated_at,
                )
                module = technical_module(entry)
                target_relative_index = translated_article_path(entry.get("published_at"), translated_title, module)
                target_index = output_dir / target_relative_index
                target_article_dir = target_index.parent
                _copy_images(source_index.parent, target_article_dir)
                _atomic_write_text(target_index, translated_markdown)
                translation_state["articles"][url] = {
                    "title": translated_title,
                    "published_at": entry.get("published_at"),
                    "source_url": entry.get("source_url") or url,
                    "module": module,
                    "path": target_relative_index.as_posix(),
                    "source_path": relative_index,
                    "source_content_hash": entry.get("content_hash"),
                    "translation_hash": translation_hash,
                    "translation_version": TRANSLATION_VERSION,
                    "translated_at": translated_at,
                }
                _save_json(state_path, translation_state)
                _save_json(cache_path, translator.cache)
                result.translated += 1
                log(f"  已保存 {target_index}")
            except Exception as exc:  # noqa: BLE001
                message = f"{type(exc).__name__}: {exc}"
                result.failures.append((url, message[:500]))
                log(f"  失败：{message}")
    finally:
        translator.close()

    finished_at = utc_now()
    translation_state["last_run"] = {
        "started_at": started_at,
        "finished_at": finished_at,
        "discovered": result.discovered,
        "queued": result.queued,
        "translated": result.translated,
        "skipped": result.skipped,
        "failures": len(result.failures),
        "technical_only": technical_only,
    }
    _save_json(state_path, translation_state)
    _save_json(cache_path, translator.cache)
    _write_catalog(output_dir, translation_state, year, finished_at, technical_only=technical_only)
    _write_report(output_dir, result, started_at, finished_at)
    failed_path = output_dir / "translation_failed.txt"
    if result.failures:
        _atomic_write_text(failed_path, "\n".join(url for url, _message in result.failures) + "\n")
    elif failed_path.exists():
        failed_path.unlink()
    return result
