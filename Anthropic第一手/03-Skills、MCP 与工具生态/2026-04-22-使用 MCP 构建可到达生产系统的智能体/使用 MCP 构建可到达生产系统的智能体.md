# 使用 MCP 构建可触达生产系统的智能体

> 来源：Claude Blog · Anthropic
> 原文链接：[building-agents-that-reach-production-systems-with-mcp](https://claude.com/blog/building-agents-that-reach-production-systems-with-mcp)
> 发布日期：2026-04-22
> 译校：对照英文原文人工重译

---

智能体的有用程度，取决于它们能够触达的系统。团队在把智能体连接到外部系统时，往往收敛出三种方法：直接 API 调用、CLI 和 MCP。本文梳理了每种方法适用的场景、为什么生产级智能体往往会落到 MCP 上，以及有效构建这些集成的模式。

## 把智能体连接到外部系统

我们通常看到把智能体连接到外部系统的三条路径：直接 API 调用、CLI 和 MCP。具体用哪种，取决于你正在构建的东西，但每种在某些场景下都说得通。关键区别在于：智能体与服务之间是否存在一个公共层，以及这个公共层能延伸多远。

### 直接 API 调用

智能体直接调用你的 API——既可以通过在代码执行沙箱中编写发出 HTTP 请求的代码，也可以通过通用的函数调用工具。这是大多数团队起步的地方，对于"一个智能体对接一项服务"，或少数无需跨智能体平台复用的集成来说，效果不错。

挑战在规模化时开始显现。由于智能体与服务之间没有公共层，每一对"智能体—服务"都变成了需要各自处理鉴权、工具描述和边缘情况的定制集成——也就是 M×N 集成问题。

### 命令行界面（CLI）

智能体在 shell 中运行你的命令行工具。这种方式快速、轻量，并依赖既有的工具链。它非常适合本地环境和沙箱容器——任何有文件系统和 shell 的地方。这提供了一层公共层，只是很薄。

CLI 在触达那些不暴露容器的移动端、Web 端或云托管平台时会遇到硬性限制，而且鉴权由 CLI 自身的机制处理——通常是在磁盘上的凭证文件。它最适合本地环境中快速、宽松的集成。

### 模型上下文协议（MCP）

MCP 以协议的形式提供了公共层。智能体连接到一台服务器，由它对外暴露你系统的能力，并带有标准化的鉴权、发现和丰富的语义。一台远程服务器能在任何部署环境中触达任何兼容的客户端（Claude、ChatGPT、Cursor、VS Code 等）。

它需要多一点前期投入。回报是：集成是可移植的，并且提供了功能丰富的智能体集成所需的语义。

## 生产级智能体在云端运行

生产级智能体越来越多地在云端运行，以便能够持续扩展与运作。它们需要触达的系统同样托管在云端：你的数据所在之处、工作被跟踪之处、基础设施运行之处。通常这些系统是远程的，且处于鉴权之后，而 MCP 恰好提供了这一公共层。而当这些系统位于私有网络而非公共互联网时，[Claude Managed Agents 中的 MCP 隧道](https://claude.com/blog/claude-managed-agents-updates) 会通过一条仅出站（outbound-only）的连接把智能体连到它们——无需暴露端口或公共端点。

我们在采用态势中已经看到了这一点。[MCP SDK](https://modelcontextprotocol.io/docs/sdk) 近期的月下载量已突破 3 亿次，高于年初的 1 亿次，在企业和主流智能体式平台上都获得了广泛采用。每天有数百万人将 MCP 与 Claude 一起使用，该协议支撑了我们最近发布的许多功能，包括 [Claude Cowork](https://claude.com/product/cowork)、[Claude Managed Agents](https://claude.com/blog/claude-managed-agents)，以及 [Claude Code 中的频道](https://code.claude.com/docs/en/channels)。

随着 MCP 持续支撑生产级智能体式系统，我们在此分享构建这些集成的模式：从构建高级服务器，到构建上下文高效的客户端，再到技能对协议形成补充之处。

## 构建有效的 MCP 服务器

我们的 [连接器目录](https://claude.ai/directory/connectors) 中已有超过 200 台 MCP 服务器，每天有数百万人使用。通过与基于该协议构建的企业和开发者密切合作，我们发现了一些决定智能体能否可靠使用服务器的设计模式。

### 构建远程服务器以获得最大触达范围

远程服务器赋予你分发能力——它是唯一一种能在 Web、移动端和云托管智能体上运行的配置，也是每个主流客户端都针对其做了优化的配置。构建远程服务器，让你的系统无论智能体在哪里运行都能被使用。

### 围绕意图而非端点对工具分组

更少、描述清晰的工具，始终优于对 API 的逐一穷举式镜像。不要把你的 API 一对一地包进 MCP 服务器——要围绕意图对工具分组，这样智能体只需几次调用就能完成任务，而不是把许多原语拼凑起来。一个 `create_issue_from_thread` 工具，胜过 `get_thread` + `parse_messages` + `create_issue` + `link_attachment` 的组合。参见 [为智能体编写有效的工具](https://www.anthropic.com/engineering/writing-tools-for-agents) 了解完整模式的更多内容。

### 当工具面很大时，采用代码编排式设计

如果你的服务需要成百上千个不同的操作（例如 Cloudflare、AWS 或 Kubernetes），按意图分组的工具集很可能覆盖不全。此时，应暴露一个接受代码的轻量工具面：智能体写一段简短脚本，你的服务器针对你的 API 在沙箱中运行它，只返回结果。[Cloudflare 的 MCP 服务器](https://github.com/cloudflare/mcp) 就是参考范例——两个工具（search 和 execute）就覆盖了约 2,500 个端点，而所占 token 仅约 1K。

### 在需要的地方提供丰富的语义

[MCP Apps](https://modelcontextprotocol.io/extensions/apps/overview) 是首个官方协议扩展，它允许工具返回一个交互式界面，例如图表、表单或仪表盘，全部内联渲染在聊天界面中。搭载了 MCP Apps 的服务器，往往比只返回文本的服务器拥有明显更高的采用率与留存率。在紧要关头用它把你的产品 UI 推到智能体或最终用户面前——该扩展在 Claude.ai、Claude Cowork 以及许多其他顶级 AI 工具中都受支持。

[视频：Claude 中的 MCP Apps](https://www.youtube.com/embed/bluAmTHoEow)

[提问引导（elicitation）](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation) 允许你的服务器在工具调用中途暂停，向用户索要输入。[表单模式](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation#form-mode-elicitation-requests) 发送一个简单的 schema，由客户端渲染出一个原生表单——用它来请求缺失的参数、确认破坏性操作，或消除选项歧义。[URL 模式](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation#url-mode-elicitation-requests) 则把用户交给浏览器——用它来完成下游的 OAuth、收款，或收集任何不应流经 MCP 客户端的凭证。两者都让用户留在流程中，而不必把他们甩到设置页面。表单模式已被广泛支持；URL 模式在 Claude Code 中受支持，更多客户端正在开发中。

### 依靠标准化鉴权

标准化鉴权让 MCP 对云托管智能体而言非常实用。如果你的服务器需要 OAuth，最新的 [MCP 规范](https://modelcontextprotocol.io/specification/2025-11-25) 支持 [CIMD](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization#client-id-metadata-documents)（Client ID Metadata Documents，客户端 ID 元数据文档）用于客户端注册——它为用户提供快速的首登鉴权流程，并大幅减少意外的重新鉴权提示。这是我们推荐的鉴权方式，MCP SDK、Claude.ai 和 Claude Code 均支持该能力，并正在整个行业被广泛采用。

用户授权之后，下一个问题是云托管智能体如何在运行时保存并复用这些令牌。[Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) 中的 [Vaults（凭据库）](https://platform.claude.com/docs/en/managed-agents/vaults#mcp-oauth-credential) 解决了这一点：一次性注册用户的 OAuth 令牌，在会话创建时通过 ID 引用该 Vault，平台就会把正确的凭据注入每一次 MCP 连接，并代为刷新——无需自建密钥库，也无需在每次调用时传递令牌。

## 让 MCP 客户端更省上下文

MCP 标准化了 AI 智能体（[*客户端*](https://modelcontextprotocol.io/docs/develop/build-client#python)）连接并使用它们所需的工具与数据源（[*服务器*](https://modelcontextprotocol.io/docs/develop/build-server)）的方式。服务器安全地暴露一系列能力，而客户端负责编排它们并管理上下文。如果你正在构建 MCP 客户端，请借助渐进式披露模式让它更省上下文。

### 通过工具搜索按需加载工具定义

[工具搜索](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool) 推迟了把所有工具加载进上下文的操作，而不是预先全部加载。这让智能体能在运行时搜索目录，并在需要时拉入相关工具。在我们的 [测试](https://www.anthropic.com/engineering/advanced-tool-use) 中，工具搜索往往能削减 85% 以上的工具定义 token，同时保持较高的选择准确率。

![](images/85e823126853-69e920e636fbec575e46319c-context-usage.webp)

通过工具搜索减少上下文占用。来源：[高级工具使用](https://www.anthropic.com/engineering/advanced-tool-use)

### 通过编程式工具调用在代码中处理工具结果

[编程式工具调用](https://www.anthropic.com/engineering/code-execution-with-mcp) 在代码执行沙箱中处理工具结果，而不是把它们原样返回给模型。这让智能体能在代码中跨调用循环、过滤和聚合，只有最终输出才进入上下文。在我们的测试中，这在复杂的多步骤工作流上大约减少了 [37%](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling) 的 token 用量。

这些模式可以自然地跨多个服务器组合在一起：更精简的上下文、更少的往返、更快的响应。参见 [*高级工具使用*](https://www.anthropic.com/engineering/advanced-tool-use) 获取完整拆解。

## 将 MCP 服务器与技能配对

[技能与 MCP 是互补的](https://claude.com/blog/skills-explained)。MCP 让智能体能访问外部系统中的工具与数据，而技能则向智能体传授 *如何* 使用这些工具去完成实际工作的程序性知识。能力最强的智能体两者并用，而技能让 MCP 服务器的扩展能力超出了少数连接的范围。组合它们有两种常见模式：

### 把技能与 MCP 服务器打包为插件

Claude 的 [插件](https://code.claude.com/docs/en/plugins-reference#plugin-components-reference) 是一种有用的抽象，它允许开发者把技能、MCP 服务器、钩子、LSP 服务器和专门的子代理打包进一种易于消费的发布形式。采用这种方式，是以最小阻力统一多个上下文提供者的最佳途径。

将 MCP 服务器与技能结合，能让 Claude 的行为更像一个领域专家。通过 MCP 拿到你的工具，再给 Claude 提供端到端编排工作流的技能。以我们的 [数据插件](https://claude.ai/directory/plugins/data%40knowledge-work-plugins) 为例（用于 Cowork），它包含 10 项技能和 8 台 MCP 服务器，面向 Snowflake、Databricks、BigQuery、Hex 等应用。

![](images/e172dff2c337-6945b3dfa8f134d0104e4e23-how-skills-and-mcp-work-t.png)

技能与 MCP 的结合。来源：[通过技能与 MCP 服务器扩展 Claude 的能力](https://claude.com/blog/extending-claude-capabilities-with-skills-mcp-servers)

### 从 MCP 服务器分发技能

服务商随其 MCP 服务器一同发布技能已越来越普遍，这样智能体既获得了原始能力，也获得了把能力用好的、带有明确主张的"剧本"。[Canva](https://claude.com/connectors/atlassian)、[Notion](https://claude.com/connectors/notion)、[Sentry](https://claude.com/connectors/sentry) 以及更多服务商今天就在 Claude 中这样做，在我们的 [Web 目录](https://claude.com/connectors) 里把技能列在他们的连接器旁边。

为了让这种配对在每个客户端之间都可移植，MCP 社区正在积极开发一个 [扩展](https://github.com/modelcontextprotocol/experimental-ext-skills)，用于直接从服务器提供技能。这样一来，客户端会自动继承相关的专业知识，并与它所依赖的 API 一起进行版本管理。我们预计，随着该扩展趋于稳定，这种模式会得到广泛采用。

## 复合层

我们在开头给出了把智能体连接到外部系统的三条路径。在实践中，成熟的集成会同时提供全部三条：作为基础的 API、用于本地优先环境的 CLI，以及用于云上智能体的 MCP。

随着生产级智能体迁移到云端，MCP 成为关键层，也是那个会复利式增长（compound）的层。今天，一台远程服务器能通过协议处理鉴权、交互性和丰富的语义，触达任何部署环境中的每一个兼容客户端。随着更多客户端采用该规范、更多扩展落地其中，同一台服务器会变得更加能干，而你无需发布任何新东西。

在构建集成时，如果你的目标是让云端的生产级智能体触达你的系统，那就构建一个 MCP 服务器，并用上述模式把它打磨出色。每一个建立在 MCP 之上的集成，都会强化整个生态：需要单独解决的边缘情况更少，需要维护的定制集成也更少。

### 致谢

感谢 Den Delimarsky、David Soria Parra、Henry Shi、Felix Rieseberg、Conor Kelly、Molly Vorwerck、Andy Schumeister、Kevin Garcia、Amie Rotherham、Matt Samuels、Angela Jiang、Katelyn Lesse、AJ Rebeiro 和 Jess Yan 对本文的贡献。
