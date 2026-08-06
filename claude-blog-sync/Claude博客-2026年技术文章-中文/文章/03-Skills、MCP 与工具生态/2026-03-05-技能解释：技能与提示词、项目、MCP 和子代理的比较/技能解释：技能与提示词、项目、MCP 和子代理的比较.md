# 技能解释：技能与提示词、项目、MCP 和子代理的比较

> 发布日期：2026-03-05 · [原文链接](https://claude.com/blog/skills-explained) · 机器翻译，仅供学习。

自从推出以来 [技能](https://www.anthropic.com/news/skills)，人们有兴趣了解 Claude 的智能体式生态系统的各个组件如何协同工作。

无论您是在构建复杂的工作流程 [Claude Code](https://www.claude.com/product/claude-code)，使用 API 创建企业解决方案，或最大限度地提高您的工作效率 [Claude.ai](http://claude.ai)知道何时使用哪种工具可以改变您使用 Claude 的工作方式。

本指南分解了每个构建块，解释了何时使用什么，并向您展示如何将它们组合起来以获得强大的智能体式工作流程。

## **了解您的智能体式构建块**

### **什么是技能？**

[视频：智能体技能：您可以自定义的专业功能](https://www.youtube.com/embed/IoqpBKrNaZI)

技能是包含 Claude 在与任务相关时动态发现和加载的指令、脚本和资源的文件夹。将它们视为专门的培训手册，为 Claude 提供特定领域的专业知识 - 从使用 Excel 电子表格到遵循组织的品牌指南。

**技能如何发挥作用：** 当 Claude 遇到任务时，它会扫描可用的技能以查找相关匹配项。技能使用渐进式披露：首先加载元数据（约 100 个令牌），为 Claude 提供足够的信息来了解技能何时相关。完整指令在需要时加载（<5k 令牌），捆绑文件或脚本仅根据需要加载。

**何时使用技能：** 当您需要 Claude 一致且高效地执行专门任务时，请选择技能。它们非常适合：

- **组织工作流程**：品牌指南、合规程序、文件模板
- **领域专业知识：** Excel 公式、PDF 操作、数据分析
- **个人喜好：** 笔记系统、编码模式、研究方法

**示例：** 创建 [品牌准则 技能](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines) 其中包括您公司的调色板、排版规则和布局规范。当Claude创建演示文稿或文档时，它会自动应用这些标准，而无需您每次都进行解释。

[了解更多](https://support.claude.com/en/articles/12512176-what-are-skills) 关于技能并查看 [我们不断增长的技能库](https://github.com/anthropics/skills).

### **提示词是什么？**

[视频：视频](https://www.youtube.com/embed/ysPbXH0LpIE)

[提示词](https://docs.claude.com/en/prompt-library/library) 是您在对话期间以自然语言向 Claude 提供的说明。它们是短暂的、对话式的、反应性的——你在当下提供背景和方向。

**何时使用提示词：** 使用提示词用于：

- 一次性请求：“总结这篇文章”
- 对话细化：“让语气更专业”
- 直接上下文：“分析这些数据并确定趋势”
- 特别说明：“将其格式化为项目符号列表”

**示例：**

*请对此代码进行全面的安全审查。我正在寻找：*

*1. 常见漏洞包括：*

- *注入缺陷（SQL、命令、XSS 等）*
- *身份验证和授权问题*
- *敏感数据暴露*
- *安全配置错误*
- *访问控制损坏*
- *加密失败*
- *输入验证问题*
- *错误处理和日志记录问题*

*2. 对于您发现的每个问题，请提供：*

- *严重级别（严重/高/中/低）*
- *代码中的位置（行号或函数名称）*
- *解释为什么它是一个安全风险以及如何利用它*
- *尽可能提供代码示例的具体修复建议*
- *防止类似问题的最佳实践指南*

*3. 代码上下文：[描述代码的功能、语言/框架及其运行环境 - 例如，“这是处理用户身份验证和处理支付数据的 Node.js REST API”]*

*4. 其他注意事项：*

- *是否存在 OWASP Top 10 漏洞？*
- *代码是否遵循[特定框架/语言]的安全最佳实践？*
- *是否存在已知漏洞的依赖关系？*

*请按严重性和潜在影响对调查结果进行优先排序。*

**专业提示：** 提示词是您与 Claude 交互的主要方式，但它们不会在对话中持续存在。对于重复的工作流程或专业知识，请考虑捕获提示词作为技能或项目说明。

**何时使用技能：** 如果您发现自己在多个对话中重复输入相同的提示词，则需要创建一项技能。将重复出现的指令（例如“使用 OWASP 标准检查此代码是否存在安全漏洞”或“用执行摘要、关键发现和建议格式化此分析”）转换为技能。这使您无需每次都重新解释程序并确保执行的一致性。

看看我们的 [提示词库](https://docs.claude.com/en/prompt-library/library), [促进最佳实践](http://claude.com/blog/prompt-engineering-best-practices), 或 [我们的智能提示词创客](https://claude.ai/public/artifacts/3796db7e-4ef1-4cab-b70c-d045778f23ec) 开始吧。

### **什么是项目？**

[视频：Claude 中的可共享项目](https://www.youtube.com/embed/nbG2DO6Xsek)

适用于所有付费 Claude 计划， [项目](https://support.claude.com/en/articles/9517075-what-are-projects) 是独立的工作区，拥有自己的聊天历史和知识库。每个项目都包含一个 200K 上下文窗口，您可以在其中上传文档、提供上下文并设置适用于该项目内所有对话的自定义说明。

**项目如何运作：** 您上传到项目知识库的所有内容都可以在该项目内的所有聊天中使用。 Claude 自动使用此上下文来提供更明智、相关的响应。当您的项目知识接近上下文限制时，Claude 无缝启用检索增强生成 (RAG) 模式，将容量最多扩展 10 倍。

**何时使用项目：** 当您需要时选择项目：

- **持久上下文：** 每次对话都应包含背景知识
- **工作区组织：** 不同举措的不同背景
- **团队协作：** 共享知识和对话历史（关于团队和企业计划）
- **定制说明：** 项目特定的基调、观点或方法

**示例：** 创建一个“第四季度产品发布”项目，其中包含市场研究、竞争对手分析和产品规格。该项目中的每个聊天都可以访问这些知识，而无需重新上传或重新解释上下文。

**何时使用技能：** 项目为特定工作主体（您公司的代码库、研究计划、持续的客户参与）提供了 Claude 持久的上下文。技能教 Claude 如何做某事。项目可能包含产品发布的所有背景，而技能可以教授 Claude 您团队的编写标准或代码审查流程。如果您发现自己在多个项目中复制相同的说明，则表明您需要创建技能。

[学习](https://support.claude.com/en/articles/9517075-what-are-projects) 有关项目的更多信息。

### **什么是子代理？**

[子代理](https://docs.claude.com/en/docs/claude-code/sub-agents) 是专门的 AI 助手，具有自己的上下文窗口、自定义系统提示词和特定的工具权限。在 Claude Code 和 Claude Agent SDK 中可用，子代理独立处理离散任务并将结果返回到主智能体。

**子代理如何工作：** 每个子代理都使用自己的配置运行 - 您可以定义它的功能、它如何解决问题以及它可以访问哪些工具。 Claude 根据描述自动将任务委派给适当的子代理，或者您可以显式请求特定的子代理。

**何时使用子代理：** 使用子代理用于：

- **任务专业化：** 代码审查、测试生成、安全审核
- **上下文管理：** 保持主要对话的焦点，同时卸下专门的工作
- **并行处理：** 多个子代理可以同时处理不同方面
- **工具限制：** 限制特定子代理的安全操作（例如只读访问）

**示例：**

```
Create a code-reviewer subagent with access to Read, Grep, and Glob tools but not Write or Edit. When you modify code, Claude automatically delegates to this subagent for quality and security review without risking unintended code changes.
```

**何时使用技能：** 如果多个智能体或对话需要相同的专业知识（例如安全审查程序或数据分析方法），请创建一项技能，而不是将这些知识构建到各个子代理中。技能是可移植和可重用的，而子代理是专门为特定工作流程构建的。使用技能教授任何智能体都可以应用的专业知识；当您需要具有特定工具权限和上下文隔离的独立任务执行时，请使用子代理。

[了解更多](https://code.claude.com/docs/en/sub-agents) 关于子代理。

### **MCP是什么？**

![](images/614fd3c6cea1-69141f0993d68ff4c536f316-619a5262.png)

MCP 在 AI 应用程序与您现有的工具和数据源之间创建通用连接层。

模型上下文协议 (MCP) 是一种开放标准，用于将 AI 助手连接到数据所在的外部系统（内容存储库、业务工具、数据库和开发环境）。

**MCP 的工作原理：** MCP 提供了一种将 Claude 连接到您的工具和数据源的标准化方法。您无需为每个数据源构建自定义集成，而是针对单个协议进行构建。 MCP 服务器公开数据和功能； MCP 客户端（如 Claude）连接到这些服务器。

**何时使用 MCP：** 当您需要 Claude 时，请选择 MCP：

- 访问外部数据：Google Drive、Slack、GitHub、数据库
- 使用业务工具：CRM系统、项目管理平台
- 连接到开发环境：本地文件、IDE、版本控制
- 与自定义系统集成：您的专有工具和数据源

**示例：** 通过 MCP 将 Claude 连接到您公司的 Google 云端硬盘。现在Claude可以搜索文档、阅读文件和参考内部知识，无需手动上传——连接保持并自动更新。

**何时使用技能：** MCP将Claude连接到数据；技能教导 Claude 如何处理该数据。如果你在解释 *如何* 使用工具或遵循程序（例如“查询我们的数据库时，始终首先按日期范围进行过滤”或“使用这些特定公式格式化 Excel 报告”）是一项技能。如果您需要 Claude *访问* 首先是数据库或 Excel 文件，即 MCP。一起使用两者：MCP 用于连接，技能用于程序知识。

[了解更多](https://www.anthropic.com/news/model-context-protocol) 关于 MCP 并查看 [文档](https://modelcontextprotocol.io/docs/develop/build-server) 关于如何构建 MCP 服务器。

## **他们如何合作**

当您将这些构建块组合起来时，真正的力量就会显现出来。每个都有不同的目的，它们一起创建复杂的智能体式工作流程。

### **比较：选择正确的工具**

| 特点 | 技能 | 提示词 | 项目 | 子代理 | MCP |
| --- | --- | --- | --- | --- | --- |
| **它提供什么** | 程序性知识 | 即时指令 | 背景知识 | 任务委托 | 工具连接 |
| **坚持** | 跨对话 | 单一对话 | 项目内 | 跨会话 | 持续连接 |
| **包含** | 说明+代码+资产 | 自然语言 | 文档+上下文 | 完整的智能体逻辑 | 工具定义 |
| **当它加载时** | 根据需要动态地 | 每回合 | 始终在项目中 | 调用时 | 随时可用 |
| **可以包含代码** | 是的 | 否 | 否 | 是的 | 是的 |
| **最适合** | 专业知识 | 快速请求 | 集中式上下文 | 专门任务 | 数据存取 |

### **示例智能体式工作流程：研究智能体**

让我们构建一个结合了多个构建块的综合研究智能体。此示例展示如何组装和激活智能体以进行竞争分析。

**第 1 步：设置您的项目**

创建“竞争情报”项目并上传：

- 行业报告和市场分析
- 竞争对手产品文档
- 来自 CRM 的客户反馈
- 以往的研究总结

添加项目说明：

*通过我们的产品策略来分析竞争对手。关注差异化机会和新兴市场趋势。提出具有具体证据和可行建议的调查结果。*

**步骤2：通过MCP连接数据源**

启用 MCP 服务器：

- Google Drive（用于访问共享研究文档）
- GitHub（审查竞争对手的开源存储库）
- 网络搜索（实时市场信息）

**第三步：创造专业技能**

创建“竞争分析”技能：

```
# My Company GDrive Navigation Skill

## Overview
Optimized search and retrieval strategy for Meridian Tech's Google Drive structure. Use this skill to efficiently locate internal documents, research, and strategic materials.

## Drive Organization

**Top-level structure:**
- `/Strategy & Planning/` - OKRs, quarterly plans, board decks
- `/Product/` - PRDs, roadmaps, technical specs
- `/Research/` - Market research, competitive intel, user studies
- `/Sales & Marketing/` - Case studies, pitch decks, campaign materials
- `/Customer Success/` - Implementation guides, success metrics
- `/Company Ops/` - Policies, org charts, team directories

**Naming conventions:**
- Format: `YYYY-MM-DD_DocumentName_vX`
- Final versions marked with `_FINAL`
- Drafts include `_DRAFT` or `_WIP`

## Search Best Practices

1. **Start broad, then filter** - Use folder context + keywords
2. **Target document owners** - Sales materials from Sales/, not root
3. **Check recency** - Prioritize documents from last 6 months for current strategy
4. **Look for "source of truth"** - Files with `_FINAL`, `_APPROVED`, or in `/Archives/Official/`

## Research Agent Workflow

1. Identify topic category (product, market, customer)
2. Search relevant folder with targeted keywords
3. Retrieve 3-5 most recent/relevant documents
4. Cross-reference with `/Strategy & Planning/` for context
5. Cite sources with file names and dates
```

**步骤 4：配置子代理（仅限 Claude Code/SDK）**

创建专门的子代理：

`market-researcher` 子代理：

```
name: market-researcher
description: Research market trends, industry reports, and competitive landscape data. Use proactively for competitive analysis.
tools: Read, Grep, Web-search
---
You are a market research analyst specializing in competitive intelligence.

When researching:
1. Identify authoritative sources (Gartner, Forrester, industry reports)
2. Gather quantitative data (market share, growth rates, funding)
3. Analyze qualitative insights (analyst opinions, customer reviews)
4. Synthesize trends and patterns

Present findings with citations and confidence levels.
```

`technical-analyst` 子代理：

```
name: technical-analyst
description: Analyze technical architecture, implementation approaches, and engineering decisions. Use for technical competitive analysis.
tools: Read, Bash, Grep
---
You are a technical architect analyzing competitor technology choices.

When analyzing:
1. Review public repositories and technical documentation
2. Assess architecture patterns and technology stack
3. Evaluate scalability and performance approaches
4. Identify technical strengths and limitations

Focus on actionable technical insights that inform our product decisions.
```

**第 5 步：激活您的研究智能体**

现在，当您询问 Claude 时：“分析我们的三大竞争对手如何定位其新的 AI 功能，并找出我们可以利用的差距”

发生的情况如下：

1. **项目上下文加载**：Claude 访问您上传的研究文档并遵循项目说明
2. **MCP 连接激活**：Claude 在您的 Google 云端硬盘中搜索最近的竞争对手简介并提取 GitHub 数据
3. **技能参与**：竞争分析技能提供了分析框架
4. **子代理执行** （在 Claude Code 中）：市场研究员收集行业数据，而技术分析师审查技术实施
5. **提示词精炼**：您提供对话指导：“特别关注医疗保健领域的企业客户”

**结果：** 全面的竞争分析，来自多个数据源，遵循您的分析框架，利用专业知识，并在整个研究项目中保持背景。

## **常见问题**

#### **技能如何发挥作用？**

技能运用 [渐进式披露](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) 保持 Claude 的高效。在处理任务时，Claude 首先扫描技能元数据（描述和摘要）以识别相关匹配项。如果技能匹配，Claude 加载完整指令。最后，如果技能包含可执行代码或参考文件，则仅在需要时加载。

这种架构意味着您可以拥有许多可用技能，而不会压垮 Claude 的上下文窗口。 Claude 在需要时准确访问所需内容。

#### **技能与子代理：何时使用什么**

**在以下情况下使用技能：** 您需要任何 Claude 实例都可以加载和使用的功能。技能就像培训材料 - 它们使 Claude 更好地完成所有对话中的特定任务。

**在以下情况下使用子代理：** 您需要完整、独立的智能体，专为特定目的而设计，可独立处理工作流程。子代理就像拥有自己的上下文和工具权限的专业员工。

**在以下情况下一起使用它们：** 您需要具有专业知识的子代理。例如，代码审查子代理可以使用技能来实现特定于语言的最佳实践，将子代理的独立性与技能的可移植专业知识相结合。

#### **技能 vs.提示词：何时使用什么**

**在以下情况下使用提示词：** 您正在给出一次性指示，提供即时上下文，或者进行来回对话。提示词是反应性的且短暂的。

**在以下情况下使用技能：** 您拥有反复需要的程序或专业知识。技能是主动的——Claude 知道何时应用它们——并且在对话中持续存在。

**一起使用它们：** 提示词和技能自然是相辅相成的。使用技能提供基础专业知识，然后使用提示词为每项任务提供特定的背景和细化。

#### **技能与项目：何时使用什么**

**在以下情况下使用项目：** 您需要背景知识和背景来告知有关特定计划的所有对话。项目提供始终加载的静态参考材料。

**在以下情况下使用技能：** 您需要程序知识和仅在相关时激活的可执行代码。技能提供按需加载的动态专业知识，从而节省您的上下文窗口。

**在以下情况下一起使用它们：** 您需要持久的上下文和专门的功能。例如，“产品开发”项目包含产品规格和用户研究，并结合创建技术文档和分析用户反馈数据的技能。

**主要区别：** 项目说“这就是你需要知道的”。技能说“这就是如何做事”。项目提供了您工作的知识库。技能提供了适用于任何地方的能力——任何对话、任何项目。

#### **副特工可以使用技能吗？**

是的。在 Claude Code 和智能体SDK 中，子代理可以像主智能体一样访问和使用技能。这创造了强大的组合，专业的子代理利用便携式专业知识。

例如，您的 python 开发人员子代理可以使用 pandas-analysis 技能按照团队的约定执行数据转换，而您的文档编写者子代理则使用技术编写技能来一致地格式化 API 文档。

## **开始使用**

准备好使用技能进行构建了吗？开始方法如下：

[**Claude.ai**](https://Claude.ai) **用户：**

- 在设置→功能中启用技能
- 在 Claude.ai/projects 创建您的第一个项目
- 尝试将项目知识与技能结合起来，完成下一个分析任务

**API 开发人员：**

- 探索技能端点 [文档](https://docs.anthropic.com)
- 看看我们的 [技能食谱](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction)

**Claude Code 用户：**

- 安装技能通过 [插件市场](https://code.claude.com/docs/en/plugin-marketplaces)
- 看看我们的 [技能食谱](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction)
