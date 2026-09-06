#!/usr/bin/env python3
"""公众号订阅 → 检测更新 → 去重 → 归档 → 生成阅读索引 的一体化管线。

设计原则
--------
1. **复用不重写**：抓取、图片本地化、推广剥离全部调用现成的 wechat_archive.py。
2. **补齐三条铁律**（wechat_archive.py 未实现，实测确认）：
   - 软断行 ≤200 字符
   - 保存门槛：正文图片数不足则**不保存**，删掉已下载产物
   - 限流不重试：被微信限流时单次请求即止，留待下一轮，不反复请求
3. **去重靠状态库**：archive_state.json 记录已处理 URL，保证不漏不重。

用法
----
    python sync.py                 # 完整跑一轮（检测 + 归档 + 索引）
    python sync.py --dry-run       # 只列出会归档什么，不真正抓取
    python sync.py --index-only    # 只重建阅读索引
    python sync.py --inbox-only    # 跳过 RSS 检测，只消费 inbox.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wechat_archive  # noqa: E402  复用现成抓取逻辑

# ---------------------------------------------------------------- 路径常量

ROOT = Path(__file__).resolve().parent.parent.parent  # Knowledge/
TOOLS = ROOT / "AI" / ".tools"
STATE_FILE = TOOLS / "archive_state.json"
SUBS_FILE = TOOLS / "subscriptions.json"
INBOX_FILE = TOOLS / "inbox.txt"

DEFAULT_SETTINGS = {
    "output_dir": "AI",
    "soft_wrap_width": 200,
    "min_images": 1,
    "fetch_timeout": 30,
    "检测范围_天": 3,
}

# 限流/风控特征词（与 wechat_archive.fetch_article 保持一致）
RATE_LIMIT_MARKERS = ("访问过于频繁", "环境异常", "验证码")


# ---------------------------------------------------------------- 基础 IO

def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"警告：读取 {path.name} 失败（{exc}），按默认值继续", file=sys.stderr)
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_inbox() -> list[str]:
    """读 inbox.txt，返回去重后的 URL 列表（忽略空行与 # 注释）。"""
    if not INBOX_FILE.exists():
        return []
    seen, urls = set(), []
    for raw in INBOX_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line not in seen:
            seen.add(line)
            urls.append(line)
    return urls


def write_inbox(urls: list[str]) -> None:
    """回写 inbox：保留未消费的链接 + 注释行。"""
    header = [
        "# 把要归档的公众号文章链接丢到这里，每行一个",
        "# 跑完 sync.py 后，成功归档的链接会被自动移除；失败的会保留等下轮重试",
        "",
    ]
    body = list(urls)
    INBOX_FILE.write_text("\n".join(header + body) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- RSS 检测

def parse_feed(xml_text: str) -> list[tuple[str, str]]:
    """解析 RSS 2.0 / Atom，返回 [(标题, 链接)]。兼容 we-mp-rss / WeWe-RSS / RSSHub。"""
    items: list[tuple[str, str]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    for item in root.iter("item"):  # RSS 2.0
        link = (item.findtext("link") or "").strip()
        title = (item.findtext("title") or "").strip()
        if link:
            items.append((title, link))

    atom = "{http://www.w3.org/2005/Atom}"
    for entry in root.iter(atom + "entry"):  # Atom
        title = (entry.findtext(atom + "title") or "").strip()
        for link_el in entry.findall(atom + "link"):
            href = (link_el.get("href") or "").strip()
            if href and link_el.get("rel") in (None, "alternate"):
                items.append((title, href))
                break
    return items


def discover_from_rss(accounts: list[dict], timeout: int) -> list[tuple[str, str]]:
    """从各账号的 RSS 抓最新文章链接。返回 [(url, 账号名)]。"""
    found: list[tuple[str, str]] = []
    for acc in accounts:
        if not acc.get("enabled", True):
            continue
        rss = (acc.get("rss") or "").strip()
        if not rss:
            continue
        name = acc.get("name", "未命名")
        try:
            resp = requests.get(rss, timeout=timeout,
                                headers={"User-Agent": wechat_archive.USER_AGENT})
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"  RSS 拉取失败 [{name}]：{exc}", file=sys.stderr)
            continue
        for _title, link in parse_feed(resp.text):
            if "mp.weixin.qq.com" in link:
                found.append((link, name))
    return found


# ---------------------------------------------------------------- 格式后处理

def soft_wrap_line(line: str, width: int) -> list[str]:
    """把超长行软断行。优先在空格处断开，纯 CJK 无空格则硬断。"""
    if len(line) <= width:
        return [line]
    out, cur = [], line
    while len(cur) > width:
        cut = cur.rfind(" ", max(0, width - 40), width + 1)
        if cut == -1:
            cut = width
        out.append(cur[:cut].rstrip())
        cur = cur[cut:].lstrip()
    if cur:
        out.append(cur)
    return out


def apply_soft_wrap(md: str, width: int) -> str:
    """软断行正文：跳过头部、代码块、图片、标题、表格、列表、原始 HTML。

    引用行（> 开头）不整体跳过，而是**保留 > 前缀、只断行内容**，
    使其同样受 ≤width 约束（实测微信长导语常就是超长引用行）。
    """
    parts = re.split(r"\n---\n", md, maxsplit=1)
    if len(parts) < 2:
        return md
    header, body = parts[0], parts[1]

    out: list[str] = []
    in_fence = False
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence or not stripped:
            out.append(line)
            continue

        # 引用行：保留 "> " 前缀，逐段续行仍带前缀（markdown 会渲染为同一段引用）
        quote = re.match(r"^(\s*>+\s?)(.+)$", line)
        if quote:
            prefix, content = quote.group(1), quote.group(2)
            if len(line) <= width:
                out.append(line)
                continue
            inner = max(20, width - len(prefix))
            out.extend(prefix + piece for piece in soft_wrap_line(content, inner))
            continue

        # 图片 / 标题 / 表格 / 列表 / 数字列表 / 原始 HTML：原样保留
        if stripped[0] in "!#|`-<" or re.match(r"^\d+[.)]\s", stripped):
            out.append(line)
            continue

        out.extend(soft_wrap_line(line, width))

    return header + "\n---\n" + "\n".join(out).rstrip() + "\n"


def count_images(md: str) -> int:
    return len(re.findall(r"!\[[^\]]*\]\(", md))


# ---------------------------------------------------------------- 归档单篇

def archive_one(
    session: requests.Session,
    url: str,
    output_dir: Path,
    account: str,
    cfg: dict,
) -> tuple[str, str, Path | None]:
    """归档一篇。返回 (状态, 说明, 产物路径)。

    状态：ok / exists / rate_limited / zero_image / failed
    非 ok 时产物路径为 None（零图的会顺带清理掉已下载产物）。
    """
    try:
        path = wechat_archive.archive_one(session, url, output_dir, overwrite=False)
    except FileExistsError as exc:
        return "exists", str(exc), None
    except RuntimeError as exc:
        msg = str(exc)
        if any(m in msg for m in RATE_LIMIT_MARKERS):
            return "rate_limited", "微信限流/验证码，本轮不重试，留待下轮", None
        return "failed", msg, None
    except Exception as exc:  # noqa: BLE001
        return "failed", f"{type(exc).__name__}: {exc}", None

    # 保存门槛：正文图片不足 → 删掉产物，不保存
    md = path.read_text(encoding="utf-8")
    images = count_images(md)
    if images < int(cfg.get("min_images", 1)):
        asset_dir = output_dir / "assets" / path.stem
        try:
            path.unlink(missing_ok=True)
            if asset_dir.exists():
                for f in asset_dir.iterdir():
                    f.unlink()
                asset_dir.rmdir()
        except OSError as exc:
            return "failed", f"清理零图产物失败：{exc}", None
        return "zero_image", f"正文图片 {images} 张，低于门槛 {cfg.get('min_images')}，已放弃保存", None

    # 软断行
    wrapped = apply_soft_wrap(md, int(cfg.get("soft_wrap_width", 200)))
    if wrapped != md:
        path.write_text(wrapped, encoding="utf-8")

    return "ok", f"{path.name}（图片 {images} 张）", path


# ---------------------------------------------------------------- 阅读索引

def build_index(state: dict, output_dir: Path) -> Path:
    """生成 markdown 索引 + 本地 HTML 阅读页。"""
    archived = state.get("archived", {})
    rows = []
    for url, meta in archived.items():
        rows.append({
            "title": meta.get("title", "(无标题)"),
            "account": meta.get("account", "未标注"),
            "date": (meta.get("archived_at") or "")[:10],
            "images": meta.get("images", 0),
            "file": meta.get("file", ""),
            "url": url,
        })
    rows.sort(key=lambda r: (r["date"], r["account"]), reverse=True)

    # --- markdown 索引
    md_lines = ["# 公众号归档 · 阅读索引", "", f"> 共 {len(rows)} 篇，按归档日期倒序　更新时间：{datetime.now():%Y-%m-%d %H:%M}", ""]
    for row in rows:
        md_lines.append(
            f"- **{row['date']}** ｜ {row['account']} ｜ "
            f"[{row['title']}](./{row['file']}) 　（图 {row['images']}）"
        )
    md_path = output_dir / "阅读索引.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # --- HTML 阅读页（浅色主题，带搜索与按号筛选）
    accounts = sorted({r["account"] for r in rows})
    items_html = "\n".join(
        f'<li class="item" data-account="{_esc(r["account"])}" data-title="{_esc(r["title"].lower())}">'
        f'<span class="date">{_esc(r["date"])}</span>'
        f'<span class="acct">{_esc(r["account"])}</span>'
        f'<a href="./{_esc(r["file"])}" target="_blank">{_esc(r["title"])}</a>'
        f'<span class="imgs">图 {r["images"]}</span></li>'
        for r in rows
    )
    options = "\n".join(f'<option value="{_esc(a)}">{_esc(a)}</option>' for a in accounts)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>公众号归档 · 阅读</title>
<style>
  :root{{--bg:#ffffff;--fg:#1f2328;--muted:#656d76;--line:#d8dee4;--accent:#0969da;--chip:#f6f8fa;}}
  *{{box-sizing:border-box}}
  body{{margin:0;padding:32px 24px;background:var(--bg);color:var(--fg);
       font:15px/1.7 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}}
  .wrap{{max-width:900px;margin:0 auto}}
  h1{{font-size:22px;margin:0 0 4px}}
  .sub{{color:var(--muted);font-size:13px;margin-bottom:20px}}
  .bar{{display:flex;gap:10px;margin-bottom:18px;flex-wrap:wrap}}
  input,select{{padding:8px 10px;border:1px solid var(--line);border-radius:6px;
       background:var(--bg);color:var(--fg);font-size:14px}}
  input{{flex:1;min-width:200px}}
  ul{{list-style:none;padding:0;margin:0}}
  .item{{display:flex;gap:12px;align-items:baseline;padding:11px 0;border-bottom:1px solid var(--line)}}
  .item:hover{{background:var(--chip)}}
  .date{{color:var(--muted);font-size:12px;font-variant-numeric:tabular-nums;min-width:82px}}
  .acct{{background:var(--chip);border:1px solid var(--line);border-radius:999px;
        padding:1px 9px;font-size:12px;color:var(--muted);white-space:nowrap}}
  .item a{{color:var(--accent);text-decoration:none;flex:1}}
  .item a:hover{{text-decoration:underline}}
  .imgs{{color:var(--muted);font-size:12px;white-space:nowrap}}
  .empty{{color:var(--muted);padding:24px 0}}
</style></head><body><div class="wrap">
<h1>公众号归档 · 阅读</h1>
<div class="sub">共 {len(rows)} 篇 · 更新于 {datetime.now():%Y-%m-%d %H:%M}</div>
<div class="bar">
  <input id="q" type="search" placeholder="搜索标题…">
  <select id="acct"><option value="">全部公众号</option>{options}</select>
</div>
<ul id="list">{items_html}</ul>
<div class="empty" id="empty" style="display:none">没有匹配的文章</div>
</div>
<script>
const q=document.getElementById('q'),sel=document.getElementById('acct'),
      items=[...document.querySelectorAll('.item')],empty=document.getElementById('empty');
function filter(){{
  const kw=q.value.trim().toLowerCase(),acc=sel.value;
  let n=0;
  for(const it of items){{
    const ok=(!kw||it.dataset.title.includes(kw))&&(!acc||it.dataset.account===acc);
    it.style.display=ok?'':'none'; if(ok)n++;
  }}
  empty.style.display=n?'none':'';
}}
q.addEventListener('input',filter); sel.addEventListener('change',filter);
</script></body></html>"""
    html_path = output_dir / "阅读.html"
    html_path.write_text(html, encoding="utf-8")
    return html_path


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# ---------------------------------------------------------------- 主流程

def main() -> int:
    ap = argparse.ArgumentParser(description="公众号订阅同步管线")
    ap.add_argument("--dry-run", action="store_true", help="只列出待归档，不真正抓取")
    ap.add_argument("--index-only", action="store_true", help="只重建阅读索引")
    ap.add_argument("--inbox-only", action="store_true", help="跳过 RSS，只消费 inbox")
    args = ap.parse_args()

    subs = load_json(SUBS_FILE, {})
    if not subs:
        print(f"错误：找不到或无法解析 {SUBS_FILE}", file=sys.stderr)
        return 1

    cfg = {**DEFAULT_SETTINGS, **(subs.get("settings") or {})}
    output_dir = (ROOT / cfg["output_dir"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    state = load_json(STATE_FILE, {"archived": {}, "skipped": {}})
    state.setdefault("archived", {})
    state.setdefault("skipped", {})

    if args.index_only:
        p = build_index(state, output_dir)
        print(f"索引已重建：{p}")
        return 0

    # 1) 收集候选链接
    candidates: list[tuple[str, str]] = []
    inbox_urls = read_inbox()
    candidates.extend((u, "") for u in inbox_urls)

    if not args.inbox_only:
        det = subs.get("detector") or {}
        if det.get("enabled"):
            found = discover_from_rss(subs.get("accounts", []), int(cfg["fetch_timeout"]))
            candidates.extend(found)
            print(f"RSS 检测：发现 {len(found)} 条链接")
        else:
            print("RSS 检测：未启用（detector.enabled=false），仅消费 inbox")

    # 2) 去重
    todo: list[tuple[str, str]] = []
    seen: set[str] = set()
    for url, acc in candidates:
        if url in state["archived"] or url in state["skipped"] or url in seen:
            continue
        seen.add(url)
        todo.append((url, acc))
    print(f"去重后待归档：{len(todo)} 篇（已归档 {len(state['archived'])} 篇）")

    if args.dry_run:
        for url, acc in todo:
            print(f"  将归档 [{acc or 'inbox'}] {url}")
        return 0

    if not todo:
        print("没有新文章")
        build_index(state, output_dir)
        return 0

    # 3) 逐篇归档
    session = requests.Session()
    session.headers.update({
        "User-Agent": wechat_archive.USER_AGENT,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://mp.weixin.qq.com/",
    })

    tally = {"ok": 0, "exists": 0, "rate_limited": 0, "zero_image": 0, "failed": 0}
    keep_in_inbox: list[str] = []          # 下轮仍需重试的

    for url, acc in todo:
        status, detail, path = archive_one(session, url, output_dir, acc, cfg)
        tally[status] = tally.get(status, 0) + 1
        now = datetime.now().isoformat(timespec="seconds")

        if status == "ok" and path is not None:
            state["archived"][url] = {
                "title": path.stem,
                "account": acc or "inbox",
                "archived_at": now,
                "images": count_images(path.read_text(encoding="utf-8")),
                "file": path.name,
            }
            print(f"  ✔ 已归档 [{acc or 'inbox'}] {detail}")
        elif status in ("exists", "zero_image"):
            state["skipped"][url] = {"reason": status, "detail": detail, "at": now}
            print(f"  － 跳过 [{acc or 'inbox'}] {detail}")
        elif status == "rate_limited":
            if url in inbox_urls:
                keep_in_inbox.append(url)
            print(f"  ⏳ 限流，下轮重试 [{acc or 'inbox'}] {url}")
        else:
            if url in inbox_urls:
                keep_in_inbox.append(url)
            print(f"  ✘ 失败 [{acc or 'inbox'}] {url}\n     {detail}", file=sys.stderr)

    # 4) 落盘：状态 + inbox + 索引
    save_json(STATE_FILE, state)
    write_inbox([u for u in inbox_urls if u in keep_in_inbox])
    html_path = build_index(state, output_dir)

    print("\n──────── 本轮汇总 ────────")
    print(f"  已归档 {tally['ok']} ｜ 已存在 {tally['exists']} ｜ 零图放弃 {tally['zero_image']} "
          f"｜ 限流 {tally['rate_limited']} ｜ 失败 {tally['failed']}")
    print(f"  阅读索引：{html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
