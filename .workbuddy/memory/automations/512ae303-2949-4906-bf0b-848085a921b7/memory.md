# 公众号订阅同步管线 — 执行记录

## 2026-09-06 09:53（首次执行）
- 结果：**本轮无更新**，新增 0 篇。已归档存量 15 篇。
- 原因：两条入口都是空的——`inbox.txt` 无任何待归档链接（仅注释行），`subscriptions.json` 的 `detector.enabled` 为 false，未启用 RSS 检测。
- 索引照常重建：`AI/阅读.html`、`AI/阅读索引.md`（sync.py 第 418-421 行确认 0 篇时仍走 build_index，不提前 return）。
- 无报错、无限流、无失败。

## 2026-09-06 10:12（Kyle 手动追加订阅）
- Kyle 手动加入订阅号「阿里技术」，并投递一篇待归档文章（mp 链接 `5Tvv8g20CybjbT0a7iUfHw`）。
- 动作：链接写入 `inbox.txt`；`阿里技术` 加入 `subscriptions.json` accounts（enabled, rss 空）；跑 sync 归档。
- 结果：**新增 1 篇** ——《AI Agent 应用精细化评测：评测体系设计与工程实践》（23 图，正文已正确标注「公众号：阿里技术」）。
- 修正：`archive_state.json` 中该条 `account` 原为 `inbox`（inbox 通道设计如此），手工改为 `阿里技术` 对齐 md 与索引；随后 `--index-only` 重建索引，已校验索引含「阿里技术」。
- 存量归档 16 篇。

### 关键事实（后续轮次复用）
- 脚本路径：`AI/.tools/sync.py`，解释器固定用 `C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe`（已装 requests/bs4/markdownify）。
- 去重状态：`AI/.tools/archive_state.json`，含 `archived` 与 `skipped` 两个桶。
- 归档门槛：`settings.min_images = 1`（零图会删掉已下载产物），软断行 200。
- 当前订阅清单：`腾讯程序员`（示例）、`阿里技术`（2026-09-06 由 Kyle 手动加入，rss 仍留空 → 仅走 inbox 手动通道）。
  **要让自动检测真正生效，需给各号补真实 RSS 地址并打开 detector，否则每轮都会是 0 新增。**
- 支持 `--index-only` 单独重建索引。
