# Claude Managed Agents 中的新增功能：按计划运行智能体并将环境变量存储在保管库中

> 发布日期：2026-06-09 · [原文链接](https://claude.com/blog/whats-new-in-claude-managed-agents) · 机器翻译，仅供学习。

从今天开始， [Claude Managed Agents](https://claude.com/blog/claude-managed-agents) 可以按计划运行并安全地访问 CLI 工具和其他经过身份验证的服务。这两项功能现已在 Claude Platform 上提供公开测试版。

## **计划部署：按计划运行智能体**

智能体现在可以按计划运行，自动完成日常工作。一个 [预定部署](https://platform.claude.com/docs/en/managed-agents/scheduled-deployments) 按 cron 计划运行 Claude 托管智能体。每次调度触发时，智能体都会启动一个新会话并完成其任务，无需您构建或托管调度程序。

将其用于重复性工作，例如夜间数据同步、每周合规性扫描或每日摘要。部署上线后，您可以随时暂停、恢复或存档，或根据需要触发其他运行。

![](images/51d1564f783b-6a2704ab5b6bc1de3bb952fc-claude-console-scheduled-.png)

团队已经在使用计划部署来自动化重复工作：

- [乐天](https://claude.com/customers/rakuten-qa) 使用计划部署来分析电子表格数据并按每周或每月的计划生成报告和演示文稿。团队还监控生产日志和指标，使产品经理无需创建仪表板即可查看应用程序运行状况。
- [积极 AI](https://actively.ai/) 使用托管智能体为销售团队提供跨账户智能体式搜索。计划部署定期刷新答案，通过替换团队最初自己构建的计划基础设施来简化堆栈。[‍](https://ando.so)
- [安藤](https://ando.so) 使用计划部署来保持招聘和销售团队的运转。智能体自动观看频道建议的后续步骤，在到期时进行跟进，并发送会议提醒。

## **Vaults：存储环境变量以验证 CLI 和其他工具**

[避难所](https://platform.claude.com/docs/en/managed-agents/vaults) 安全地存储 Claude Managed Agents 的环境变量和凭据。在运行时，智能体访问 API 密钥等机密作为环境变量，因此它们可以对 CLI 工具和其他服务进行身份验证，而无需将凭据硬编码到提示词或代码中。

智能体 [连接到外部系统](https://claude.com/blog/building-agents-that-reach-production-systems-with-mcp) 通过直接 API 调用、CLI 和 MCP。 CLI 让智能体直接通过 shell 驱动现有的命令行工具，使其成为快速、轻量级的集成路径。使用环境变量名称及其可以到达的域注册 API 密钥，安装在智能体的沙箱中的 CLI 可以使用它来进行经过身份验证的 API 调用。

智能体永远不会看到您的密钥，因为沙箱仅包含一个占位符。真正的密钥附加在网络边界，并且仅针对您允许的域的请求，因此它只会发送到您批准的地方。要更改密钥，请在保管库中更新它，运行的会话将在下次调用时获取新值。大多数在 HTTP 请求中发送密钥的 CLI 都以这种方式工作，包括 Browserbase、KERNEL、Notion、Ramp 和 Sentry CLI。 [浏览器库](https://docs.browserbase.com/integrations/anthropic/managed-agents/quickstart) 和 [内核](https://www.kernel.sh/docs/integrations/claude-managed-agents) 首次提供托管智能体浏览器功能，因此智能体可以与其他工具一起导航并与网络交互。

![](images/36753ce90092-6a27074e40b19ba74e79b134-claude-managed-agents-cli.png)

团队正在使用保管库中的环境变量来为智能体提供对经过身份验证的工具的安全访问：

- [概念](https://claude.com/customers/notion-qa) 使用保管库中的环境变量来推出其 CLI 以及 MCP 工具，为其智能体添加文件上传功能，而无需将 API 代币交给模型。
- [浏览器库](https://www.browserbase.com/) 使用以下方法建立了浏览器技能的公共目录 [浏览CLI](https://www.npmjs.com/package/browse)，通过保险库进行身份验证。计划的部署会定期验证目录以保持其准确性。
- [内核](https://www.kernel.sh/docs/integrations/claude-managed-agents) 使用保管库中的环境变量将智能体安全连接到跟踪使用情况和客户对话的数据库。智能体会在发生使用量激增时进行标记，以便团队可以与客户确认该活动是否是有意为之。[‍](https://getmilana.ai/)
- [米兰娜](https://getmilana.ai/) 使用保管库中的环境变量将其 AI 产品工程师安全地连接到客户的代码库。智能体自动发现并修复错误，大规模数据分析运行速度比以前更快。
