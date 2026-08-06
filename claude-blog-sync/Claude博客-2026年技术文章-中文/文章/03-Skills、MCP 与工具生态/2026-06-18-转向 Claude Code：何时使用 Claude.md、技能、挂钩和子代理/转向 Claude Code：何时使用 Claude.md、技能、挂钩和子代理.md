# 转向 Claude Code：何时使用 Claude.md、技能、挂钩和子代理

> 发布日期：2026-06-18 · [原文链接](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more) · 机器翻译，仅供学习。

### 规则

[**规则**](https://code.claude.com/docs/en/memory#organize-rules-with-claude/rules/) 是 Markdown 文件吗 `.claude/rules/` 给出 Claude 特定的约束或约定。

无作用域规则的行为类似于 Claude.md，因为它们始终在会话启动时加载，并在压缩时重新注入。即使加载上下文与手头的任务无关，这也可能会浪费令牌。

路径范围的规则允许您仅在相关时加载规则指令，方法是添加 `paths` 控制它们何时加载的字段。

例如：规则范围为 `src/api/**` 在纯文档会话期间脱离上下文。仅当 Claude 读取其中的文件时才会加载它 `src/api/` 目录。

看起来是这样的：

```
---
paths:
  - "src/api/**"
  - "**/*.handler.ts"
---
All API handlers must validate input with Zod before processing.
```

**提示**：特定于文件的约束，例如“迁移只能追加”，最适合作为 **规则** 放置在您的路径中：frontmatter。当指令涉及出现在代码库的多个（但不是所有）角落的横切关注点或文件时，在嵌套的 Claude.md 文件上获取路径范围规则。

### 技能

[**技能**](https://code.claude.com/docs/en/skills) 住在 `.claude/skills/` 作为 Claude 动态加载的指令、脚本和资源的文件夹。每个技能都有一个 `SKILL.md` 包含名称、描述和正文的文件。

仅在会话开始时加载名称和描述；当 Claude 通过斜线命令 (/code-review) 或自动匹配任务调用技能时，会加载完整的正文。

![](images/5d7ff264b063-6a340f852d1f938ab867559f-2199ed03.png)

技能通过您的系统提示词触发。

例如， `/code-review` 是一项内置技能，可在不编辑文件的情况下查看当前差异并报告其发现结果。该技能定义了剧本，因此 Claude 每次调用它时都遵循相同的结构化方法。

在压缩时，Claude Code 重新注入调用的技能，直至所有调用的技能的总预算。如果您在一次会话中调用了许多技能，那么最早的技能会首先被删除。

**提示：** 程序性指令（例如部署工作流程、发布清单或审核流程）属于技能而不是 Claude.md。

Claude Code 附带技能，但您也可以编写自己的自定义技能。我们的 [Claude 技能构建完整指南](https://claude.com/blog/complete-guide-to-building-skills-for-claude) 向您展示如何操作。

### 子代理

[**子代理**](https://code.claude.com/docs/en/sub-agents) 是 Markdown 文件吗 `.claude/agents/` 为特定的副任务定义独立的助手。每个文件都使用 YAML frontmatter（名称、描述以及模型和工具访问的可选字段），后跟成为该子代理系统提示词的正文。

子代理与技能类似，名称、描述和工具列表在会话开始时加载，但智能体正文中的较大上下文不会自动调用。 Claude 通过智能体工具调用它们，并传入提示词字符串。

![](images/00005b50503c-6a340f852d1f938ab86755a2-914c1942.png)

Claude Code 的上下文窗口包含 Claude 所了解的有关您的会话的所有内容。的 [互动时间轴在这里](https://code.claude.com/docs/en/context-window) 遍历加载内容和加载时间。

子代理体内的更大的指导上下文不仅不会自动调用，而且根本不会进入父会话。

然后，子代理在其自己的新上下文窗口中运行，返回主会话的唯一内容是子代理的最终消息（通常是许多子任务的聚合结果）加上元数据。

此模式可扩展：子代理最多可以嵌套五层深度，并且 [动态工作流程](https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code) 编排数十到数百个后台智能体，无需您指定子代理架构的每个细节。编排计划和中间结果存在于脚本变量中，而不是存在于 Claude 的上下文窗口中，这可以在不损失教学保真度的情况下实现扩展。

**提示：** 这种孤立是寻求子代理而不是技能的主要原因之一。当诸如深度搜索、日志分析传递或依赖性审核之类的副任务会使您的主要对话与您不会再次引用的中间结果变得混乱时，请使用子代理。当您希望该过程在主线程内执行时，请使用一项技能，以便您可以查看并引导每个步骤。

### 挂钩

[**挂钩**](https://code.claude.com/docs/en/hooks-guide) 是用户定义的命令、HTTP 端点或 LLM提示词，通过触发对 Claude 的行为提供更具确定性的控制 [Claude 生命周期中的特定事件](https://code.claude.com/docs/en/hooks#hook-lifecycle) 例如文件编辑、工具调用或会话启动。

![](images/093aecaea7a7-6a340f852d1f938ab867559c-e782277c.png)

当钩子可以触发时 Claude Code 会话中的事件映射。

您在中注册钩子 `settings.json`、托管策略设置或技能/智能体frontmatter。

挂钩有多种类型：command、HTTP、mcp\_tool、提示词和智能体。所有钩子都是确定性触发的。前三个是确定性执行的，而后两个提示词和智能体使用 Claude 的判断而不是一组规则来确定输出。

挂钩的上下文成本较低，因为配置或指令位于主上下文窗口之外。线束运行处理程序（命令、http、mcp\_tool）或根据挂钩类型使用单独的窗口（提示词、智能体）进行模型调用。

某些挂钩可能会将输出保存到主上下文窗口中。例如，阻塞钩子的标准错误保存在上下文中，因此 Claude 知道调用被拒绝的原因。

但大多数钩子不会将输出保存到主窗口，除非配置显式返回它。如果您在压缩之前将聊天记录备份到另一个文件中以供以后参考 `PreCompact` 事件中，Claude 不知道哪个文件保存了聊天记录。

这使得这些钩子类型与Claude.md、规则和技巧有根本的不同。您可以在我们的帖子中了解更多信息[**如何配置钩子**](https://claude.com/blog/how-to-configure-hooks).

**提示：** 对应该确定性发生的任何事情使用钩子：编辑后运行 linter，完成后发布到 Slack，或者在执行之前阻止特定命令。一个 `PreToolUse` hook 可以检查任何工具调用并退出代码 2 来拒绝它。

它们的上下文成本较低，因为它们是线束运行的代码，而不是加载到上下文中的 Claude 指令。技能和挂钩也是构建模块 [设计智能体循环](https://claude.com/blog/getting-started-with-loops)- 重复运行的工作流程，直到满足停止条件。

### 输出样式

[**输出样式**](https://code.claude.com/docs/en/output-styles) 文件在 `.claude/output-styles/` 将指令注入系统提示词。它们永远不会被压缩，在每个会话开始时加载，并在会话中的第一个请求后被缓存，这意味着它们具有适中的上下文成本。

因为它们位于系统提示词中，所以输出样式在我们迄今为止介绍的任何方法中具有最高的指令跟随权重，因此应谨慎使用。

**对输出样式的更改将替换默认输出样式** （除非您在样式的 frontmatter 中设置 keep-coding-instructions: true ）。

在 Claude Code 中，这将删除告诉 Claude 它正在帮助用户完成软件工程任务的指令，并包含其他关键的默认指令，例如：

- 如何确定变更范围；
- 何时添加或省略代码注释；
- 对于安全问题该怎么办；和
- 验证习惯，例如在宣布工作完成之前运行测试。

默认情况下，自定义输出样式会放弃所有这些，Claude Code 更像是一个通用助理，而不是软件工程师助理。

**提示**：在编写自定义输出样式之前，请检查内置样式。 **积极主动**, **解释性的**, 和 **学习** 涵盖最常见的需求（自主性、教学模式、协作编码），而无需维护样式文件。

### 追加系统提示词

修改输出样式的另一种方法是 `append-system-prompt` 标志。虽然修改输出样式文件可能会对 Claude 的行为产生较大的、意外的更改，但附加标志仅对原始系统提示词进行附加。它不会修改Claude的角色；它只是向其默认角色添加指令。

它也在调用时传递，并且仅适用于该调用，而不是跨会话持久保存为文件。

与其他传递指令的方法相比，附加系统提示词可能具有更高的上下文成本。它增加了输入令牌，尽管提示词缓存在会话中的第一个请求后降低了此成本。指示 Claude 使用更详细或更长的样式也会增加输出标记。

**提示：** 附加系统提示词最适合添加特定的编码标准、输出格式或特定领域的知识。请记住，附加系统提示词的坚持回报会递减。一般来说，您使用此方法提供的说明越多，Claude 遵循它们的严格程度就越低，特别是如果有任何矛盾的话。

## 何时使用每种方法

如果您发现自己正在执行以下操作之一，您可能需要考虑使用替代位置来获取说明：

**Claude.md 中的“每次 X，总是做 Y”。** 如果行为应该可靠地发生，例如每次编辑后运行 prettier 或完成后发布到 Slack，请使用钩子 `settings.json` 相反。模型选择运行格式化程序与自动运行格式化程序不同。

**Claude.md 中的“永远不要这样做”**。当某些事情绝对不能发生时，指令就是错误的工具。 Claude 在大多数情况下都会遵循指令，但在压力下、长时间会话或模棱两可的情况下，或者由于提示词注入到作为任务一部分访问的文件中，模型可能无法遵循提示规则。真正的护栏需要是确定性的，执行方法是 [钩子](https://code.claude.com/docs/en/hooks) 和 [权限](https://code.claude.com/docs/en/permissions)。一个 `PreToolUse` hook 可以检查调用并使用代码 2 退出以阻止它。 [**托管设置**](https://code.claude.com/docs/en/settings#managed-settings)更进一步：它们是管理员部署的，不能被用户的本地配置覆盖，并且是强制实施确定性的、组织范围的护栏的唯一方法。

**Claude.md 中的 30 行程序。** 程序属于技能。 Claude.md 是 Claude 应该始终保留的事实：构建命令、monorepo 布局、团队约定。部署运行手册或安全审查清单应存在于 `.claude/skills/`，其中主体仅在调用时加载。

**没有路径的 API 特定规则。** 如果规则仅适用于 `src/api/**`，将其范围界定为 `paths:` 在不相关的工作中使其脱离上下文。无范围规则在机制上与将内容放入 Claude.md 中相同：始终加载，始终消耗令牌。

**将个人首选项写入项目级 Claude.md 文件。** 所有基于文件的方法都会为每个 Claude Code 会话加载一个用户级对应项，无论您位于哪个存储库。根据个人喜好使用本地文件（始终使用语义提交消息）。保留项目级文件以获取团队范围内但特定于给定代码库的首选项。

## Claude Code 定制入门

您可以在我们的网站中找到更多关于充分利用 Claude Code 的技巧和模式，从配置环境到跨并行会话进行扩展。 [Claude Code 的最佳实践](https://code.claude.com/docs/en/best-practices#write-an-effective-claude-md) 文档。

一旦你有了其中的一些功能，你就可以将它们中的许多（技能、子代理、挂钩、输出样式）捆绑为一个 [插件](https://code.claude.com/docs/en/plugins) 在团队成员或项目之间共享一致的设置。

*本文由 Anthropic 员工 Michael Segner 撰写。*
