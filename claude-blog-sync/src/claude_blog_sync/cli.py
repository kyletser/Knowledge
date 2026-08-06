from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from claude_blog_sync.models import SyncConfig
from claude_blog_sync.sync import sync_blog
from claude_blog_sync.translate import translate_archive


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-blog-sync",
        description="将 claude.com/blog 增量归档为 Markdown 和干净 HTML",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync_parser = subparsers.add_parser("sync", help="发现并同步文章")
    sync_parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="输出目录（默认：./output）",
    )
    sync_parser.add_argument(
        "--url",
        action="append",
        default=[],
        help="只同步指定文章 URL；可重复使用",
    )
    sync_parser.add_argument(
        "--year",
        type=int,
        help="只归档指定发布年份的文章，例如：2026",
    )
    sync_parser.add_argument("--limit", type=int, help="本次最多处理多少篇")
    sync_parser.add_argument("--delay", type=float, default=1.0, help="文章之间的礼貌等待秒数（默认：1）")
    sync_parser.add_argument("--timeout", type=float, default=30.0, help="单次请求超时秒数（默认：30）")
    sync_parser.add_argument("--retries", type=int, default=3, help="网络重试次数（默认：3）")
    sync_parser.add_argument(
        "--refresh-existing",
        action="store_true",
        help="用 If-Modified-Since 条件请求检查已归档文章",
    )
    sync_parser.add_argument(
        "--no-images",
        action="store_true",
        help="不下载正文图片，保留绝对远程地址",
    )

    translate_parser = subparsers.add_parser("translate", help="把英文归档批量翻译为中文")
    translate_parser.add_argument(
        "--source",
        type=Path,
        default=Path("output"),
        help="英文归档目录（默认：./output）",
    )
    translate_parser.add_argument(
        "--output",
        type=Path,
        default=Path("Claude博客-中文"),
        help="中文归档目录（默认：./Claude博客-中文）",
    )
    translate_parser.add_argument("--year", type=int, default=2026, help="翻译指定发布年份（默认：2026）")
    translate_parser.add_argument("--limit", type=int, help="本次最多翻译多少篇")
    translate_parser.add_argument("--delay", type=float, default=0.25, help="翻译请求之间的秒数（默认：0.25）")
    translate_parser.add_argument("--timeout", type=float, default=30.0, help="翻译请求超时秒数（默认：30）")
    translate_parser.add_argument("--retries", type=int, default=5, help="翻译请求重试次数（默认：5）")
    translate_parser.add_argument("--force", action="store_true", help="忽略断点状态并重新翻译")
    translate_parser.add_argument(
        "--technical-only",
        action="store_true",
        help="只翻译开发、工程、智能体、API、MCP、模型使用与安全技术文章",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "sync":
            result = sync_blog(
                SyncConfig(
                    output_dir=args.output,
                    explicit_urls=tuple(args.url),
                    year=args.year,
                    limit=args.limit,
                    delay=args.delay,
                    timeout=args.timeout,
                    retries=args.retries,
                    refresh_existing=args.refresh_existing,
                    download_images=not args.no_images,
                )
            )
            print(
                "完成："
                f"新建 {result.created}，更新 {result.updated}，"
                f"未变化 {result.unchanged}，按年份过滤 {result.filtered}，"
                f"失败 {len(result.failures)}"
            )
            return 1 if result.failures else 0
        if args.command == "translate":
            translation = translate_archive(
                source_dir=args.source,
                output_dir=args.output,
                year=args.year,
                limit=args.limit,
                force=args.force,
                delay=args.delay,
                retries=args.retries,
                timeout=args.timeout,
                technical_only=args.technical_only,
            )
            print(
                "完成："
                f"新翻译 {translation.translated}，跳过 {translation.skipped}，"
                f"失败 {len(translation.failures)}"
            )
            return 1 if translation.failures else 0
        parser.error("未知命令")
    except (ValueError, PermissionError, OSError) as exc:
        parser.exit(2, f"错误：{exc}\n")
    return 2
