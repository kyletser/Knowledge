# Claude Blog 增量归档工具

> **精选译文已迁出**：从 2026 年技术文章中筛选、人工校译的 37 篇中文干货，已整理为独立的 [`../Anthropic第一手`](../Anthropic第一手/README.md) 精选集。本仓库现在只承载**抓取 + 机翻工具链**（英文归档 `output/` 与中文机翻 `Claude博客-2026年技术文章-中文/` 均为原料层，未做人工校译）。

把 [claude.com/blog](https://claude.com/blog/) 的文章发现并归档为 Markdown、干净 HTML 和本地图片。第一次同步站点地图里的文章，以后可只处理新增 URL；需要检查旧文更新时使用 HTTP 条件请求。

## 安装

需要 Python 3.11+ 和 [uv](https://docs.astral.sh/uv/)。

```powershell
cd "C:/Users/Administrator/Desktop/Knowledge/claude-blog-sync"
uv sync --extra dev
uv run pytest
```

## 先抓示例文章

```powershell
uv run claude-blog-sync sync `
  --url "https://claude.com/blog/building-with-claude-managed-agents" `
  --output "./output"
```

不想下载图片时加 `--no-images`。同一命令再次运行会根据 `state.json` 跳过已归档文章；加 `--refresh-existing` 时会发送 `If-Modified-Since`，未修改的页面由服务器返回 304。

## 同步整个 Blog

```powershell
uv run claude-blog-sync sync --output "./output"
```

第一次会处理站点地图中尚未归档的全部英文文章。后续运行只处理新 URL。程序默认顺序抓取，并在文章之间等待 1 秒。

只归档 2026 年发布的历史文章：

```powershell
uv run claude-blog-sync sync --year 2026 --output "./output"
```

年份筛选依据文章的发布日期；其他年份只在 `state.json` 的 `observed` 中记录，正文和图片不会落盘，因此同一年重复运行无需重新探测这些旧文章。

## 翻译今年的技术文章

先完成英文归档，再生成独立的中文技术文章归档：

```powershell
uv run claude-blog-sync translate `
  --source "./output" `
  --output "./Claude博客-2026年技术文章-中文" `
  --year 2026 `
  --technical-only `
  --delay 0.75
```

技术筛选覆盖 Claude Code、API/SDK、智能体、MCP、模型使用、提示词、工程实践、架构和安全技术；排除客户案例、营销、公司动态、行业推广和纯产品发布。翻译会保留原始链接、图片与代码块，并在每篇文章中标记机器翻译。中文文章只生成 Markdown，不重复生成 HTML。任务支持断点续传，不会改动英文归档。

中文归档使用中文目录名，例如：

```text
Claude博客-2026年技术文章-中文/
├─ 2026-index.md
└─ 文章/
   ├─ 01-Claude Code 开发实践/
   ├─ 02-智能体与多智能体系统/
   ├─ 03-Skills、MCP 与工具生态/
   ├─ 04-模型能力、上下文与提示工程/
   ├─ 05-安全、身份与合规/
   └─ 06-工程方法与技术案例/
```

输出结构：

```text
output/
├─ 2026-index.md
├─ articles/
│  └─ 2026-06-10-building-with-claude-managed-agents/
│     ├─ index.md
│     ├─ content.html
│     └─ images/
├─ state.json
├─ sync_report.md
└─ failed.txt
```

- `index.md`：YAML frontmatter、来源链接和正文 Markdown。
- `2026-index.md`：使用 `--year 2026` 时生成的按日期倒序总目录。
- `content.html`：仅保留文章正文的可独立打开 HTML，不含导航、CTA 和相关文章。
- `state.json`：URL、内容哈希、文件路径、抓取时间和 HTTP `Last-Modified`。
- `sync_report.md`：本次新建、更新、跳过、失败和图片警告。
- `failed.txt`：本次失败 URL；下一次全量发现时会自动重试未入库文章。

## 常用参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `--output` | `./output` | 输出根目录 |
| `--url` | 无 | 只抓指定文章；可重复 |
| `--year` | 无 | 只归档指定发布年份 |
| `--limit` | 无 | 限制本次处理数量，适合试跑 |
| `--delay` | `1.0` | 文章请求之间的秒数 |
| `--timeout` | `30` | 单次请求超时 |
| `--retries` | `3` | 403、429 和常见临时错误的退避重试次数 |
| `--refresh-existing` | 关 | 条件请求检查已归档文章 |
| `--no-images` | 关 | 保留远程图片 URL，不下载图片 |

## 抓取规则

- 发现入口固定使用官方 `https://claude.com/sitemap.xml`，严格筛选 `https://claude.com/blog/<slug>`。
- 每次运行先读取并检查 `https://claude.com/robots.txt`。
- 元数据优先读取 `BlogPosting` JSON-LD。
- 正文只选择 Blog 文章区域内非隐藏、非空的 `.u-rich-text-blog.w-richtext`，不会把整个 `main` 的导航和推荐内容混入正文。
- 相对链接转成绝对链接；视频 iframe 转成普通 Markdown 链接；正文图片按 URL 哈希保存并改写为本地相对路径。
- sitemap 当前没有文章级 `lastmod`，所以新增检测依赖 URL 差异；旧文更新检查依赖文章响应的 `Last-Modified`。

请保持低频、合理延迟，并仅按你的合法用途保存与使用文章内容。
