# Claude API 技能现已在 CodeRabbit、JetBrains、Resolve AI 和 Warp 中使用

> 发布日期：2026-04-29 · [原文链接](https://claude.com/blog/claude-api-skill) · 机器翻译，仅供学习。

今天，CodeRabbit、JetBrains、Resolve AI 和 Warp 正在捆绑 [Claude-api技能](https://github.com/anthropics/skills/tree/main/skills/claude-api)，为开发人员提供可用于生产的 Claude API 代码，无论他们在何处构建。该技能于 3 月份在 Claude Code 中首次引入，现在更多开发人员已经在使用该技能。

## 使用 Claude API 技能进行构建

的 `claude-api` 技能捕获了使 Claude API 代码正常工作的细节，例如哪种智能体模式适合给定的作业、模型代之间的参数变化以及何时应用提示词缓存。结果是更少的错误、更好的缓存、更干净的智能体模式以及更平滑的模型迁移。

当我们的 SDK 发生变化时，它会保持最新状态。当新的模型发布或 API 获得功能时，Claude 已经知道了。

只要有该技能，请请求 Claude：

- **“提高我的缓存命中率。”** 该技能适用于许多开发人员忽略的提示词缓存规则。
- **“为我的智能体添加上下文压缩。”** 它引导您了解我们文档中的压缩原语和智能体模式。
- **“将我升级到最新的 Claude模型。”** Claude 检查您的代码并引导您更新模型名称、提示词以及新模型的工作量设置，例如 [Opus 4.7](https://www.anthropic.com/news/claude-opus-4-7)。在Claude Code中，您也可以直接运行 `/claude-api migrate.`**‍**
- **“为我的行业建立深度研究智能体。”** Claude 引导您完成配置 [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview)，所以长期运行的研究是几个提示词，而不是自定义项目。在Claude Code中，您也可以直接运行 `/claude-api managed-agents-onboard`.
