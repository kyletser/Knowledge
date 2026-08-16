# Anthropic 第一手 · 中文精选集

共 37 篇。源自 `claude.com/blog` 的 Anthropic 第一方英文技术博客，经筛选（剔除产品发布、功能更新、合作动态与营销系列）后，**对照英文原文人工重译**为中文，独立于 `claude-blog-sync/` 工具链存放。

> 本集合与 `AI/`（微信公众号技术文章归档）互为补充：
> - `AI/` 是**国内一线从业者**的 Agent / Harness 工程实践；
> - 本集合是 **Anthropic 官方**关于 Claude Code、智能体、Skills、MCP、安全与工程方法的第一手设计判断。
> 两者主题高度重合，分别从"厂商怎么做"与"行业怎么落地"两个角度印证同一套架构原则。

## 筛选说明

本集合定位为**架构判断与工程经验精选**，不收录以下类型：

- 产品发布与功能介绍（"今天我们推出 X""现在可用"）
- 平台集成与合作动态（"X 现已支持 Claude""Y 可在 Z 中使用"）
- 营销系列与个人化风格文章
- 厂商自家数据栈宣传（信息密度低、客户案例色彩重）

保留标准：讲设计原则、最佳实践、工程经验、架构判断——穿越模型与产品迭代周期。

## 翻译说明

- 每篇均**对照英文原文人工重译**，非机器翻译直出；
- 术语统一：agent=智能体、harness=线束、framework=框架、subagent=子代理、skill=技能、progressive disclosure=渐进式披露、context rot=上下文腐烂；
- 文首标注 `译校：对照英文原文人工重译`，并保留原文链接。

## 学习路径

- [01-Claude Code 开发实践](<01-Claude Code 开发实践/README.md>)：工具设计、入职实践、大型代码库工作方法与 HTML 工程有效性。（4 篇）
- [02-智能体与多智能体系统](<02-智能体与多智能体系统/README.md>)：智能体设计原则、工作流程模式、Harness 设计、子代理、多智能体协调与企业级构建。（10 篇）
- [03-Skills、MCP 与工具生态](<03-Skills、MCP 与工具生态/README.md>)：Skills 设计与培养、MCP 生产实践、连接器可观察性与 Claude Code 工具治理经验。（8 篇）
- [04-模型能力、上下文与提示工程](<04-模型能力、上下文与提示工程/README.md>)：网络搜索过滤、会话管理、模型选型、提示词缓存与计算机/浏览器使用的最佳实践。（6 篇）
- [05-安全、身份与合规](<05-安全、身份与合规/README.md>)：AI 加速攻击防御、源代码保护、智能体零信任、威胁检测平台与智能体身份访问模型。（5 篇）
- [06-工程方法与技术案例](<06-工程方法与技术案例/README.md>)：2026 年软件构建趋势判断、AI 遗留系统现代化、AI Native 工程组织与循环工程方法论。（4 篇）

## 01-Claude Code 开发实践

| 发布日期 | 中文标题 | 原文 |
|---|---|---|
| 2026-04-10 | [像智能体一样看待：我们如何在 Claude Code 中设计工具](<01-Claude Code 开发实践/2026-04-10-像智能体一样看待：我们如何在 Claude Code 中设计工具/像智能体一样看待：我们如何在 Claude Code 中设计工具.md>) | [查看原文](https://claude.com/blog/seeing-like-an-agent) |
| 2026-04-28 | [像新开发者一样入职 Claude Code：17 年开发的经验教训](<01-Claude Code 开发实践/2026-04-28-像新开发者一样入职 Claude Code：17 年开发的经验教训/像新开发者一样入职 Claude Code：17 年开发的经验教训.md>) | [查看原文](https://claude.com/blog/onboarding-claude-code-like-a-new-developer-lessons-from-17-years-of-development) |
| 2026-05-14 | [Claude Code 如何在大型代码库中工作：最佳实践和从哪里开始](<01-Claude Code 开发实践/2026-05-14-Claude Code 如何在大型代码库中工作：最佳实践和从哪里开始/Claude Code 如何在大型代码库中工作：最佳实践和从哪里开始.md>) | [查看原文](https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start) |
| 2026-05-20 | [使用Claude Code：HTML的不合理有效性](<01-Claude Code 开发实践/2026-05-20-使用Claude Code：HTML的不合理有效性/使用Claude Code：HTML的不合理有效性.md>) | [查看原文](https://claude.com/blog/using-claude-code-the-unreasonable-effectiveness-of-html) |

## 02-智能体与多智能体系统

| 发布日期 | 中文标题 | 原文 |
|---|---|---|
| 2026-01-23 | [构建多智能体系统：何时以及如何使用它们](<02-智能体与多智能体系统/2026-01-23-构建多智能体系统：何时以及如何使用它们/构建多智能体系统：何时以及如何使用它们.md>) | [查看原文](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them) |
| 2026-03-05 | [AI智能体的常见工作流程模式 — 以及何时使用它们](<02-智能体与多智能体系统/2026-03-05-AI智能体的常见工作流程模式 — 以及何时使用它们/AI智能体的常见工作流程模式 — 以及何时使用它们.md>) | [查看原文](https://claude.com/blog/common-workflow-patterns-for-ai-agents-and-when-to-use-them) |
| 2026-04-02 | [智能体线束设计：利用 Claude 智能的 3 种模式](<02-智能体与多智能体系统/2026-04-02-智能体线束设计：利用 Claude 智能的 3 种模式/智能体线束设计：利用 Claude 智能的 3 种模式.md>) | [查看原文](https://claude.com/blog/harnessing-claudes-intelligence) |
| 2026-04-07 | [如何以及何时在 Claude Code 中使用子代理](<02-智能体与多智能体系统/2026-04-07-如何以及何时在 Claude Code 中使用子代理/如何以及何时在 Claude Code 中使用子代理.md>) | [查看原文](https://claude.com/blog/subagents-in-claude-code) |
| 2026-04-09 | [顾问策略：给予智能体智力提升](<02-智能体与多智能体系统/2026-04-09-顾问策略：给予智能体智力提升/顾问策略：给予智能体智力提升.md>) | [查看原文](https://claude.com/blog/the-advisor-strategy) |
| 2026-04-10 | [多智能体协调模式：五种方法以及何时使用它们](<02-智能体与多智能体系统/2026-04-10-多智能体协调模式：五种方法以及何时使用它们/多智能体协调模式：五种方法以及何时使用它们.md>) | [查看原文](https://claude.com/blog/multi-agent-coordination-patterns) |
| 2026-04-30 | [为企业构建AI智能体](<02-智能体与多智能体系统/2026-04-30-为企业构建AI智能体/为企业构建AI智能体.md>) | [查看原文](https://claude.com/blog/building-ai-agents-for-the-enterprise) |
| 2026-05-27 | [CodeRabbit 如何使用 Claude 构建智能体编排系统](<02-智能体与多智能体系统/2026-05-27-CodeRabbit 如何使用 Claude 构建智能体编排系统/CodeRabbit 如何使用 Claude 构建智能体编排系统.md>) | [查看原文](https://claude.com/blog/how-coderabbit-used-claude-to-build-an-agent-orchestration-system) |
| 2026-06-02 | [适用于每项任务的工具：Claude Code 中的动态工作流程](<02-智能体与多智能体系统/2026-06-02-适用于每项任务的工具：Claude Code 中的动态工作流程/适用于每项任务的工具：Claude Code 中的动态工作流程.md>) | [查看原文](https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code) |
| 2026-06-24 | [打造高效的人力-智能体团队](<02-智能体与多智能体系统/2026-06-24-打造高效的人力-智能体团队/打造高效的人力-智能体团队.md>) | [查看原文](https://claude.com/blog/building-effective-human-agent-teams) |

## 03-Skills、MCP 与工具生态

| 发布日期 | 中文标题 | 原文 |
|---|---|---|
| 2026-01-22 | [用技能构建智能体：为专业工作配备智能体](<03-Skills、MCP 与工具生态/2026-01-22-用技能构建智能体：为专业工作配备智能体/用技能构建智能体：为专业工作配备智能体.md>) | [查看原文](https://claude.com/blog/building-agents-with-skills-equipping-agents-for-specialized-work) |
| 2026-01-29 | [Claude 技能培养完整指南](<03-Skills、MCP 与工具生态/2026-01-29-Claude 技能培养完整指南/Claude 技能培养完整指南.md>) | [查看原文](https://claude.com/blog/complete-guide-to-building-skills-for-claude) |
| 2026-03-03 | [提高技能创造者：测试、测量和完善智能体技能](<03-Skills、MCP 与工具生态/2026-03-03-提高技能创造者：测试、测量和完善智能体技能/提高技能创造者：测试、测量和完善智能体技能.md>) | [查看原文](https://claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills) |
| 2026-03-05 | [技能解释：技能与提示词、项目、MCP 和子代理的比较](<03-Skills、MCP 与工具生态/2026-03-05-技能解释：技能与提示词、项目、MCP 和子代理的比较/技能解释：技能与提示词、项目、MCP 和子代理的比较.md>) | [查看原文](https://claude.com/blog/skills-explained) |
| 2026-04-22 | [使用 MCP 构建可到达生产系统的智能体](<03-Skills、MCP 与工具生态/2026-04-22-使用 MCP 构建可到达生产系统的智能体/使用 MCP 构建可到达生产系统的智能体.md>) | [查看原文](https://claude.com/blog/building-agents-that-reach-production-systems-with-mcp) |
| 2026-06-03 | [构建 Claude Code 的经验教训：我们如何使用技能](<03-Skills、MCP 与工具生态/2026-06-03-构建 Claude Code 的经验教训：我们如何使用技能/构建 Claude Code 的经验教训：我们如何使用技能.md>) | [查看原文](https://claude.com/blog/lessons-from-building-claude-code-how-we-use-skills) |
| 2026-06-08 | [开发人员构建连接器的可观察性](<03-Skills、MCP 与工具生态/2026-06-08-开发人员构建连接器的可观察性/开发人员构建连接器的可观察性.md>) | [查看原文](https://claude.com/blog/observability-for-developers-building-connectors) |
| 2026-06-18 | [转向 Claude Code：何时使用 Claude.md、技能、挂钩和子代理](<03-Skills、MCP 与工具生态/2026-06-18-转向 Claude Code：何时使用 Claude.md、技能、挂钩和子代理/转向 Claude Code：何时使用 Claude.md、技能、挂钩和子代理.md>) | [查看原文](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more) |

## 04-模型能力、上下文与提示工程

| 发布日期 | 中文标题 | 原文 |
|---|---|---|
| 2026-02-17 | [通过动态过滤提高网络搜索的准确性和效率](<04-模型能力、上下文与提示工程/2026-02-17-通过动态过滤提高网络搜索的准确性和效率/通过动态过滤提高网络搜索的准确性和效率.md>) | [查看原文](https://claude.com/blog/improved-web-search-with-dynamic-filtering) |
| 2026-04-15 | [使用Claude Code：会话管理和1M上下文](<04-模型能力、上下文与提示工程/2026-04-15-使用Claude Code：会话管理和1M上下文/使用Claude Code：会话管理和1M上下文.md>) | [查看原文](https://claude.com/blog/using-claude-code-session-management-and-1m-context) |
| 2026-04-16 | [将 Claude Opus 4.7 与 Claude Code 结合使用的最佳实践](<04-模型能力、上下文与提示工程/2026-04-16-将 Claude Opus 4.7 与 Claude Code 结合使用的最佳实践/将 Claude Opus 4.7 与 Claude Code 结合使用的最佳实践.md>) | [查看原文](https://claude.com/blog/best-practices-for-using-claude-opus-4-7-with-claude-code) |
| 2026-04-30 | [构建 Claude Code 的经验教训：提示词缓存就是一切](<04-模型能力、上下文与提示工程/2026-04-30-构建 Claude Code 的经验教训：提示词缓存就是一切/构建 Claude Code 的经验教训：提示词缓存就是一切.md>) | [查看原文](https://claude.com/blog/lessons-from-building-claude-code-prompt-caching-is-everything) |
| 2026-05-13 | [使用 Claude 的计算机和浏览器的最佳实践](<04-模型能力、上下文与提示工程/2026-05-13-使用 Claude 的计算机和浏览器的最佳实践/使用 Claude 的计算机和浏览器的最佳实践.md>) | [查看原文](https://claude.com/blog/best-practices-for-computer-and-browser-use-with-claude) |
| 2026-07-07 | [选择 Claude模型和 Claude Code 中的工作量级别](<04-模型能力、上下文与提示工程/2026-07-07-选择 Claude模型和 Claude Code 中的工作量级别/选择 Claude模型和 Claude Code 中的工作量级别.md>) | [查看原文](https://claude.com/blog/claude-model-and-effort-level-in-claude-code) |

## 05-安全、身份与合规

| 发布日期 | 中文标题 | 原文 |
|---|---|---|
| 2026-04-10 | [为 AI 加速攻击准备安全程序](<05-安全、身份与合规/2026-04-10-为 AI 加速攻击准备安全程序/为 AI 加速攻击准备安全程序.md>) | [查看原文](https://claude.com/blog/preparing-your-security-program-for-ai-accelerated-offense) |
| 2026-05-12 | [Anthropic 的网络安全团队如何使用 Claude Code 构建威胁检测平台](<05-安全、身份与合规/2026-05-12-Anthropic 的网络安全团队如何使用 Claude Code 构建威胁检测平台/Anthropic 的网络安全团队如何使用 Claude Code 构建威胁检测平台.md>) | [查看原文](https://claude.com/blog/how-anthropic-uses-claude-cybersecurity) |
| 2026-05-27 | [使用 LLM 保护源代码](<05-安全、身份与合规/2026-05-27-使用 LLM 保护源代码/使用 LLM 保护源代码.md>) | [查看原文](https://claude.com/blog/using-llms-to-secure-source-code) |
| 2026-05-27 | [对 AI智能体的零信任](<05-安全、身份与合规/2026-05-27-对 AI智能体的零信任/对 AI智能体的零信任.md>) | [查看原文](https://claude.com/blog/zero-trust-for-ai-agents) |
| 2026-06-24 | [智能体标签中的智能体身份：用于自主、团队范围 AI 的新访问权限模型](<05-安全、身份与合规/2026-06-24-智能体标签中的智能体身份：用于自主、团队范围 AI 的新访问权限模型/智能体标签中的智能体身份：用于自主、团队范围 AI 的新访问权限模型.md>) | [查看原文](https://claude.com/blog/agent-identity-access-model) |

## 06-工程方法与技术案例

| 发布日期 | 中文标题 | 原文 |
|---|---|---|
| 2026-01-21 | [定义 2026 年软件构建方式的八个趋势](<06-工程方法与技术案例/2026-01-21-定义 2026 年软件构建方式的八个趋势/定义 2026 年软件构建方式的八个趋势.md>) | [查看原文](https://claude.com/blog/eight-trends-defining-how-software-gets-built-in-2026) |
| 2026-02-23 | [使用 AI 实现 COBOL 现代化：打破成本障碍](<06-工程方法与技术案例/2026-02-23-使用 AI 实现 COBOL 现代化：打破成本障碍/使用 AI 实现 COBOL 现代化：打破成本障碍.md>) | [查看原文](https://claude.com/blog/how-ai-helps-break-cost-barrier-cobol-modernization) |
| 2026-06-03 | [运行 AI 本地工程组织](<06-工程方法与技术案例/2026-06-03-运行 AI 本地工程组织/运行 AI 本地工程组织.md>) | [查看原文](https://claude.com/blog/running-an-ai-native-engineering-org) |
| 2026-06-30 | [循环工程：循环入门](<06-工程方法与技术案例/2026-06-30-循环工程：循环入门/循环工程：循环入门.md>) | [查看原文](https://claude.com/blog/getting-started-with-loops) |
