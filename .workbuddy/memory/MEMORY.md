# Knowledge 项目长期记忆

## 项目定位
个人 AI 与 Agent 技术知识库（github.com/kyletser/Knowledge），以 Agent / Harness 工程为统一主题。五个模块：
- `AI/` — 公众号技术文章归档（19 篇，人工抓取格式化，脚本 `AI/.tools/wechat_archive.py`）
- `Anthropic第一手/` — Claude Blog 人工校译精选集 37 篇（2026-08-17 从 claude-blog-sync 迁出，独立成集）
- `ai-agent-book/` — AI Agent 中文书稿（10 章+引言+后记，开源 bojieli）
- `claude-blog-sync/` — 纯抓取+机翻工具链（src/、tests/、pyproject，成品译文已迁走）
- `learn-claude-code-main/` — Harness 工程 20 章渐进式教程（shareAI-lab）

## claude-blog-sync 精选规则（2026-08-17 确立）
中文译文库定位为**架构判断与工程经验精选**，不收录：
- 产品发布与功能介绍（"今天我们推出 X""现在可用"）
- 平台集成与合作动态（"X 现已支持 Claude"）
- 营销系列与个人化风格文章
- 厂商自家数据栈宣传（信息密度低、客户案例色彩重）

保留标准：讲设计原则、最佳实践、工程经验、架构判断——穿越模型与产品迭代周期。
原始 62 篇 → 精选 37 篇。机翻备份 `_backup_20260817/` 已于 2026-08-17 **删除**（无回滚需求）。

## Kyle 在本项目的归档纪律
- 格式：`###` 小节提升、长行软断行 ≤200 字符、剥离互动句与推广残留、图片全本地化
- **保存门槛铁律**：必须有文章内部配图才保存（限流残缺/零图直接跳过或删已存）
- **公众号归档工具现状（2026-09-05 核实订正）**：`wechat-to-md` **并未安装成 Skill**，`~/.workbuddy/skills/` 下只有 aihot / github-pr-workflow / pptx-build-windows。现存的是裸脚本 `AI/.tools/wechat_archive.py`（requests+bs4+markdownify，含图片本地化与推广话术剥离），依赖已装入 `~/.workbuddy/binaries/python/envs/default`；`AI/.tools/wechat2md/`（Go 版）是**空目录**。

## 公众号订阅个人网站集成（2026-09-05 决断 + 落地）
**已加进现有 kyletser/peronalsite**（FastAPI + React，腾讯云 150.158.89.70 已部署）。拒绝另起站——现有站 24h 在线 + 持久卷 + 密码登录 + 路由框架，「不依赖我也能自动跑」全部前提已满足。

**已部署模块**（commit 7841aa3）：
- 后端：`app/wechat_parser.py`（移植自 `AI/.tools/wechat_archive.py` + `sync.py` 软断行零图门槛限流不重试）、`wechat_detector.py`（RSS 2.0/Atom 兼容 we-mp-rss/WeWe-RSS/RSSHub + URL 归一化）、`scheduler.py`（APScheduler AsyncIOScheduler + 固定 UTC 偏移，不依赖系统 tzdata）、`wechat_sync.py`（检测→去重→抓取→入库 + 并发锁 + 限流停手）、`routers/wechat.py`（RESTful）。
- 前端：`pages/WeChat.tsx`（状态卡 + 账号侧栏 + 全部/未读/已收藏筛选 + 搜索 + 抽屉式阅读器 react-markdown）+ `services/api.ts` 加 8 个方法 + 6 个类型。
- 部署：`.env.example` 加 8 个 WECHAT_* 开关；`README.md` 加订阅使用说明。

**部署链路（已跑通）**：本机 build → git push → git bundle → paramiko 上传 → 跑 `scripts/deploy-server.sh`（沿用项目原 deploy.cmd 路径）。服务器端 deploy.cmd 依赖的 `.agents/ssh-askpass.local.cmd` 不在 GitHub 仓库里，本机走 paramiko 注入密码。

**线上已验证**：
- `http://150.158.89.70/api/wechat/status` → `next_run_at: 2026-09-06T07:30:00+08:00` ✓
- `/api/wechat/inbox` 拿假链接优雅返回结构化错误而非 500 ✓
- 容器 studybuddy 自动同步启动，明早 07:30 北京时间首跑。

**默认行为**：
- 检测源留空 = 仅手动投喂（兜底，不依赖任何外部服务）。
- 保存门槛默认 1 张图（沿用 Knowledge 仓库铁律）。放行纯文字：`WECHAT_MIN_IMAGES=0` 后重启容器。

**全链路已打通（2026-09-06 凌晨验证）**：微信读书 Cookie 方式授权成功 → by_article 解析「腾讯技术工程」（mp_id=MP_WXS_2398602260）→ weread collect 采集 → RSS `/rss/MP_WXS_2398602260?ext=xml`（studybuddy 容器内 200）→ 研途助手账号接入（POST /api/wechat/accounts，仅必填 name）→ sync 成功入库 1 篇（markdown 全文 3.5 万字符，格式对齐归档规范）。定时同步 next_run=07:30 北京时间。细节坑：`GET /mps` 恒空且 `POST /mps` 报 50001 但不影响链路；inbox 只支持 POST，读列表用 `GET /api/wechat/articles`，全文只在详情接口 `markdown` 字段。遗留：root/admin 弱密码待改，Cookie 过期（-2012/-2041）需重新投喂。

**部署踩坑（教训，已修复）**：
- lucide-react 0.562.0 偶发不带 d.ts（package.json typings 字段写了但文件不在 dist/）→ `npm install lucide-react@0.562.0` 单独装一下恢复。
- `DATA_ROOT = os.path.join(DATA_DIR, "wechat")` 返回 str，被 `cleanup_article(data_root: Path)` 拒绝 → 改 `pathlib.Path(DATA_DIR) / "wechat"`。
- paramiko 5.x `get_pty=True` 时 stdout.readline 返回 str 而非 bytes，要 print 而不是 decode。

## 本地公众号管线 sync.py 的两个死配置（2026-09-06 核实）
`AI/.tools/subscriptions.json` 里这两个字段**代码从不读取，改了没用**：
- `detector.base_url`（localhost:8001）——`discover_from_rss()` 是直接用每个 account 的 `rss` 字段**完整 URL** 去 `requests.get`，不做任何拼接。
- `settings.检测范围_天`（3）——只在 DEFAULT_SETTINGS 定义，从未被读。

**连带后果**：RSS 检测**无日期过滤**，`discover_from_rss()` 只筛「链接含 mp.weixin.qq.com」。给账号填真实 RSS 并开 `detector.enabled` 后，**首轮会把 feed 全部历史文章灌进来**并易触发限流。开启前务必先 `--dry-run`，必要时给该函数补日期过滤。

**其他既定行为**：inbox 通道归档的文章，`archive_state.json` 里 account 恒为 `inbox`（sync.py:442 `acc or "inbox"`），但 md 正文 blockquote 是 `wechat_archive.py` 提取的真实号名 → 两者不一致，需手工改 state 再 `--index-only` 重建索引。

**两套系统不连通**（最易误解）：Kyle 扫码授权的是个人站 peronalsite（150.158.89.70，微信读书 Cookie），其 weread RSS 路由 `/api/wechat/rss/<mp_id>?ext=xml` 实测 **401 未登录**，本机无法直接消费。本地 Knowledge 管线与个人站无共享状态 → 扫了码也不会让本地自动拉。

完整交接说明见仓库根 `公众号订阅项目交接文档.md`。

## learn-claude-code 多语言 README 清理（2026-09-06 已完成）
按 Kyle「只保留中文的」指示，删除非中文 README 42 个 + 配套 `.en/.ja` 插图 58 个（共 100 个，全部进回收站，0 失败）。保留：根 `README-zh.md` + s01–s20 各 1 个中文 `README.md`（21 个）。

**判定语言的正确方法**：用 **H1 标题行**（有假名→ja，有汉字→zh，否则 en）。
**不要**用「CJK 字符数 vs 拉丁字符数」比例——`s04_hooks/README.md` 有 1248 个汉字却因代码块多被误判为 en，险些删掉该章唯一中文版。

**两个禁区**：
- `web/public/course-assets/`（87 个文件）与 `sXX_*/images/` 是「源码 + 网站发布副本」关系，**不是冗余**，删了站点图片全挂。
- `web/README.md` 是 Next.js 脚手架英文说明，**无中文对应版**，属"子项目唯一文档"而非"多语言变体"，未删（待 Kyle 定夺）。

删除清单留存于 `.workbuddy/scan_del.txt`，回收站可还原。

## AI 归档图片共享图池（2026-09-06 建立）
重复装饰图统一放 `AI/assets/_shared/<md5><ext>`，16 篇 md 的重复图链接改指该池。去重 41 个文件，`AI/` 从 138.2 MB → 69.0 MB（净省 69.2 MB），229 条图片引用零断链。

**解析 md 图片链接的正确正则**（务必照抄）：
```python
re.compile(r'!\[([^\]]*)\]\(\s*<?([^)>]+?)>?\s*\)')   # 允许路径含空格
```
**不要用** `[^)\s>]+` 匹配路径——公众号标题常含空格（如「AI Coding的下一站」），会把这些文章的链接**全部漏解析**，改链接+删原文件后直接造成 20+ 条断链。本次就踩了这个坑，靠两招救回：① 改动前先备份 md（现存 `.workbuddy/md_backup`），用「备份 vs 已改写」对照还原 原文件名→共享文件名 映射；② 剩余靠解析回收站 `$I`/`$R`（`$I` 的 28 字节后是 UTF-16 原路径）算 MD5 确证——因为共享文件本就以 md5 命名，能对上。

**其他实情**：
- 16 个 `original.html` 的 217 处本地图片引用**本来 100% 断链**（html 存在 `assets/<标题>/` 里，却按 `AI/` 根写相对路径）。删除孤立图不会让它更糟。
- 孤立图（无任何 md 引用）已清理：全仓库 632 个文本文件扫描确认零可解析引用后删除 6 个（0.75 MB）。**注意**：早前用坏正则曾误判为「153 个 / 44.7 MB」，用正确正则重算后实际只有 6 个——绝大多数图片本来就在被引用，勿再信旧数字。
- 部分 md 里有 `![]()` 空占位符（微信转换遗留，无 src），无害，非本次引入。

## 与求职目标的关系
四线并进为 Agent 岗位（OpsPilot 旗舰项目）构建知识底盘：理论体系（书稿）+ 一手厂商实践（Blog 译文）+ 国内落地案例（AI 归档）+ 可跑的 harness 代码（教程）。C++ 方向由底层实现视角补足。

## 个人站公众号自动检测全面接通（2026-09-06 晚，全自动通道上线）
**Kyle 需求定版**：网站自动检测订阅号的更新（每日 07:30 即可，不需要实时），保留原文链接点击跳转，不手动投喂。本地 Knowledge 管线维持 inbox 手动归档轨道不变。

**授权**：Kyle 重新提供微信读书 Cookie（浏览器全串，含 wr_vid=300739622/wr_skey），经 `POST /api/v1/wx/weread/cookie` 写入 we-mp-rss（存数据卷，容器 env 无 WEREAD_COOKIE），`POST /api/v1/wx/weread/mp/test` 验证凭据有效。管理 token 经 `POST /api/v1/wx/auth/login`（OAuth2 表单 admin/admin@123）获取。

**订阅**：we-mp-rss 现有 2 个 feed——腾讯技术工程 `MP_WXS_2398602260`、阿里技术 `MP_WXS_3885737868`。阿里技术经 `POST /api/v1/wx/mps/by_article?url=<文章链接>`（需 90s 超时）反查 + `POST /api/v1/wx/mps`（mp_id 传 biz 的 base64，如 `Mzg4NTczNzg2OA==`）添加。

**定时采集**：创建消息任务「公众号每小时采集」（id `a9ccbc1f-9539-4896-903a-005536d7a25b`，cron `17 * * * *`，status=1，mps_id 为 JSON 数组 `[{"id":"..."}]` 格式）。⚠️ we-mp-rss 只按消息任务的 cron 自动刷新，无任务=永不追更；status≠1 不调度；webhook 失败不影响采集（采集在前、通知在后）。

**网站侧**：新增账号「阿里技术」（feed_url=`http://172.17.0.1:8001/rss/MP_WXS_3885737868?ext=xml`）；端到端验证手动 sync 成功入库《Spec-Driven Development》一文，source_url 正确。`.env`（/opt/studybuddy-docker-staging/）原本**没有任何 WECHAT_* 行**（全走代码默认），已追加 `WECHAT_MIN_IMAGES=0` 并 `docker compose up -d --force-recreate studybuddy`（restart 不重读 env_file！）。SECRET_KEY 在 .env 中已设置，重建后登录态不变。文章 account 字段来自文章页自身的号名（非 feed 名），如 DeepSeek 文记为「腾讯程序员」——展示层细节，非 bug。

**we-mp-rss '~' bug 与容器补丁**：weread 返回 token 含 `~`（如 `ph4PRUDZvMnfrGn~0CfT5g`），微信真实短链用 `_`——原样保留会被微信判「参数错误」页（与源码注释作者声称的相反，实测 `~` bad / `_` OK / `-` bad）。已修补容器内 `/app/core/wx/model/weread_mp.py` 的 `build_mp_url`（含 `~` 时逐候选 `_`/`-`/原样实测验证取能出 `#js_content` 者；无 `~` 零开销）并修正 db.db 已存的坏 url（1 条）。⚠️ **补丁在容器层，镜像更新/重建即丢失**——补丁脚本留存于 `Knowledge/.workbuddy/patch_werss.py`。

**待办安全项**：网站登录密码仍是默认 `studybuddy2026`（且登录无限流、CORS=*）；we-mp-rss admin 仍是默认 `admin@123`；服务器 SSH 密码已经对话明文传输。建议 Kyle 尽快全部更换。

**运维手册（Cookie 再过期，征兆=列表停止更新/-2012/-2041）**：浏览器登录 weread.qq.com → F12 网络 → 复制任意请求的整串 Cookie → SSH 服务器 → 内部 curl `POST /api/v1/wx/weread/cookie`（JSON `{"cookie":"..."}`，先登录拿 token）。we-mp-rss 管理 UI 需 SSH 隧道：`ssh -N -L 18001:172.17.0.1:8001 root@150.158.89.70` → 浏览器开 localhost:18001。SSH 执行工具：`Knowledge/.workbuddy/sshrun.py`（密码走 WECHAT_SSH_PW 环境变量）。

## peronalsite 显示/渲染修复（2026-09-06 晚，commit f45da16 已部署）
Kyle 反馈「有显示 bug、文章渲染很差」，浏览器实测+源码审查后定位 6 处并全部修复部署：
1. **正文排版裸奔**：`prose` 类一直没生效——`@tailwindcss/typography` 根本没装。已装插件+注册 tailwind.config，阅读器加 `prose prose-slate` + 青色引用块样式。
2. **横向溢出**：原文链接长 URL 不可断行撑破抽屉。修：`break-words` + `prose-a:break-all` + 滚动容器 `overflow-x-hidden`。
3. **软断行碎行**：归档时 ≤200 字符折的行，react-markdown 会把换行渲染成空格（中文段落全是断口感）。修：渲染前 `prepareMarkdown()` 还原软断行（CJK 行直接拼接、西文补空格、跳过代码块/列表/表格/引用/标题），顺带去重复首行标题、清空 `![]()` 占位。
4. **「今天 07:30」日历错**：formatNextRun 用「<24h 就叫今天」，明早 07:30 也显示今天。修：按日历日判断 今天/明天/M-D；副标题改用 dailyRunTime（纯时刻）。
5. **「未知时间」**：微信页服务端渲染抓不到 #publish_time，但 feed 里有 pubDate。修：后端 `archive_url` 加 `fallback_publish_time`（检测项 published 转 UTC+8），前端空值不显示占位。
6. **侧栏账号筛选失配**：文章 account 存的是页面抓的作者/号名（如「王砚舒（彦纾）」），与订阅账号名对不上 → 按号筛选恒空。修：`account=account_name or parsed["account"]`（订阅账号优先），存量 2 篇已在服务器 sqlite 手工修正（附 pubDate 回填：Spec-Driven=2026-09-06 18:15、DeepSeek=2026-09-06 00:24）。

**部署链路（本次全链路跑通，可复用）**：仓库本地副本在 `Desktop/peronalsite`（gh clone）→ 改码 → `frontend && npm run build` 本地验证 → commit+push → `git bundle create /tmp/xxx.bundle main` → paramiko SFTP 上传 bundle+scripts/deploy-server.sh → `bash /tmp/deploy-server.sh <40位SHA> /tmp/xxx.bundle`（服务器端构建候选镜像→健康检查→原子切换→失败自动回滚，输出 DEPLOYMENT_OK 即成功）→ 前端强刷（浏览器会缓存旧 index.html，验证时注意 JS 文件名 hash 变化）。
**排障备忘**：IAB 截图通道偶发卡死（"previous screenshot still completing"），换新标签页可恢复；列表页卡片点击自动化常常点不中（布局位移），用 `evaluate(() => document.querySelectorAll('button[title="打开"]')[0].click())` 程序化点击最可靠——「抽屉打不开」曾误判为网站 bug，实际是自动化点击没点准。

## 订阅扩容至 7 号 + '~' 补丁补全（2026-09-06 晚二）
**Kyle 提供文章链接新增 5 号**（by_article 反查 + POST /mps 添加，全部成功）：美团技术团队 `MP_WXS_2396491298`、得物技术 `MP_WXS_3915178544`、携程技术 `MP_WXS_2390272091`、字节跳动技术团队 `MP_WXS_3253632141`、小红书技术REDtech `MP_WXS_3889763736`（Kyle 说「小红书」，实际号名以反查为准）。网站侧 5 账号已建、sync 成功入库各 1 篇最新文章。**微信读书单账号订阅 7/10，接近风控建议上限，再加号要谨慎。**

**'~' bug 第二处补丁**：cover 采集路径用的是 `build_mp_link_from_review_id()`（reviewId 推导链接），与之前补的 `build_mp_url()` 是两个函数——首次扩容后 3 个号 RSS 又出 `~` 链接。已对第二处打同款验证式补丁（`~`→`_`→`-` 候选实测取能出 `#js_content` 者）+ 修 3 条存量 url。**验证方式**：RSS `<link>` 应与 Kyle 提供的原始链接一致（`_` 版本）。⚠️ 教训：`docker exec we-mp-rss python3 - <<PY` 必须 **`-i`**，否则 stdin 不进容器、脚本静默空跑还返回 0。
**发布时间注意**：weread cover 渠道的 pubDate 实际是**采集时间**（文章真实发布时间拿不到），网站里显示的「发布时间」对新采集文章是这个近似值。

**添加新号的完整操作脚本**（后续复用）：SSH → host python3（注意登录要 form 编码 `application/x-www-form-urlencoded`，其余接口 JSON）→ `POST /api/v1/wx/mps/by_article?url=` 反查（timeout≥110s）→ `POST /api/v1/wx/mps {mp_name, mp_id: mp_info.biz(base64), mp_cover: logo, avatar: logo}` → **PUT /api/v1/wx/message_tasks/{id} 要传完整对象**（schema 是 Create，部分字段 422），mps_id=全量 feed 的 JSON 数组 → job/fresh 重载 → run 一次 → 网站 POST /api/wechat/accounts 挂 feed_url → POST /api/wechat/sync。

## 质量巡检与解析器加固（2026-09-06 深夜，commit 8a05ddd + 2792630）
**美团订阅疑点已澄清**：链接 gZKWR… 的页面 js_name=美团技术团队（发布号），js_author_name=图灵Agent评测（原作者，转发/合作）——Kyle 标注正确；本地知识库当年 md 里「公众号：图灵Agent评测」抓的其实是作者字段（wechat_archive 选择器 js_author_name 优先），订阅无问题。

**发现「残页」问题**：微信会偶发（对服务器 IP 持续数小时）下发「有壳无内容」降级页——有 #js_content 但 0 字 + 1 图，**无风控特征词**，绕过原有限流判断被静默入库（得物首篇即中招：实际页面有 5533 字 + 17 图）。已上线两层修复（commit 8a05ddd + 2792630）：
1. **残页守卫**（wechat_parser，在最终 markdown 上判断）：`文本<30字 且 图<2张` → RuntimeError 拒绝入库，上层记 error 等下轮重试。⚠️ v1 教训：守卫放在解析前用「页面 img 数」判断会漏判（markdownify 会丢图，页面 2 图成文 1 图）——必须在最终 markdown 上用 count_images 判断。
2. **var ct 真实发布时间**：服务端渲染无 #publish_time，但页面脚本 `var ct = "秒级时间戳"` 是真实发布时间，已提取（UTC+8 格式化）。weread feed 的 pubDate 只是采集时间，此后文章显示的发布时间恢复可信。

**得物文章现状**：守卫两次正确拒绝残页入库（微信当晚一直对该 IP 降级此页面；本地家宽 IP 拿到的是全文——按 IP 差异化服务）。**自愈路径**：文章 URL 不在库中，每天 07:30 网站同步会自动重试，页面恢复后自动全文入库，无需人工。手动验证法：订阅管理「手动投喂」贴该链接。
**其余巡检结论**：7 feed 身份全部正确（按 cover 采集内容核对）；每小时 cron 正常触发（日志「失败 N 个」是 tracker 口径：无新文章即记失败，非真失败）；磁盘 26G 余量健康；6 篇存量文章字数/图数健康（27804~4260 字）。存量 6 篇的发布时间仍是采集时间近似值（早于 var ct 补丁），新文章起为真值。

## 功能优化第三轮（2026-09-06 深夜，commit 62df7b6）
1. **手动投喂可指定归属账号**：`POST /api/wechat/inbox` 加可选 `account` 字段（订阅账号名），订阅管理投喂表单加账号下拉（默认「自动识别」）。修复投喂文章 account 落到页面作者名、侧栏筛选失位的问题。
2. **采集间隔加密**：we-mp-rss 消息任务 cron `17 * * * *` → `13,43 * * * *`（每半小时）。原因：weread cover 渠道每次只吐最新一篇，账号半小时内连发两篇会永久漏掉中间篇，加密缩窄窗口。风控影响可忽略（每轮每号 1 次 cover 调用）。
3. **存量发布时间回填**：6 篇文章的 publish_time 全部按 var ct 真值回填（此前全是采集时间），现在列表正确显示 08-28 ~ 09-04 分布。降级页也带 var ct，回填不受影响。
4. **得物文章**：降级持续（微信对该 IP 此 URL 已 >4 小时只出空壳），守卫持续正确拦截；重录用新 inbox 账号归属功能，页面恢复后一次成功。**兜底发现**：we-mp-rss 库里存有该文 weread 渠道全文（84,677 字符 HTML）——若降级持续数天，可做「weread 内容回退」功能（从 we-mp-rss 取 content 走站点解析管线），当前未实现，先靠每日 07:30 自愈重试。
