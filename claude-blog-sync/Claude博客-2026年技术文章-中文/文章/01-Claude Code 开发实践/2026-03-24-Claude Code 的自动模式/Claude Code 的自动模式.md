# Claude Code 的自动模式

> 发布日期：2026-03-24 · [原文链接](https://claude.com/blog/auto-mode) · 机器翻译，仅供学习。

***更新****：Claude Code 中的自动模式通常适用于所有用户。 （2026 年 7 月 10 日）*

今天，我们引入自动模式，这是 Claude Code 中的一种新权限模式，其中 Claude 代表您做出权限决策，并在操作运行之前进行监控。它现已作为团队计划的研究预览提供，并将在未来几天内向企业计划和 API 用户提供。

## 它是如何运作的

Claude Code 的默认权限是故意保守的：每个文件写入和 bash 命令都要求批准。这是一个安全的默认值，但这意味着您无法启动一项大型任务并走开，因为 Claude 在此过程中会请求频繁的人工批准。虽然一些开发人员选择使用 --dangerously-skip-permissions 绕过权限检查，但跳过权限可能会导致危险和破坏性结果，因此不应在隔离环境之外使用。

自动模式是一条中间路径，可让您运行更长的任务、更少的中断，同时比跳过所有权限带来的风险更小。在每个工具调用运行之前，分类器都会对其进行审查 [检查潜在的破坏性行为](https://code.claude.com/docs/en/permission-modes#what-the-classifier-blocks-by-default) 例如批量删除文件、敏感数据泄露或恶意代码执行。

分类器认为安全的操作会自动进行，有风险的操作会被阻止，重定向 Claude 以采取不同的方法。如果Claude坚持执行被持续阻止的操作，最终会触发用户的权限提示词。

## 会发生什么

与 --dangerously-skip-permissions 相比，自动模式可降低风险，但并不能完全消除风险，我们继续建议在隔离环境中使用它。分类器可能仍允许一些有风险的操作：例如，如果用户意图不明确，或者 Claude 没有足够的有关您的环境的上下文来了解某个操作可能会产生额外的风险。它有时也可能阻止良性行为。随着时间的推移，我们将继续改善体验。

自动模式可能会对工具调用的令牌消耗、成本和延迟产生很小的影响。

## 开始使用

自动模式现已在 Claude Code 中作为 Claude 团队用户的研究预览提供，并将在未来几天向企业和 API 用户推出。它适用于 Claude Sonnet 4.6 和 Opus 4.6。

- **对于管理员**：自动模式很快将适用于企业、团队和 Claude API 计划的所有 Claude Code 用户。要为 CLI 和 VS Code 扩展禁用它，请在托管设置中设置 "disableAutoMode": "disable"。默认情况下，Claude 桌面应用程序上自动模式处于禁用状态，并且可以使用组织设置 -> Claude Code 进行切换。
- **对于开发商**：运行“Claude --enable-auto-mode”以启用自动模式，然后使用 Shift+Tab 循环到它。在桌面和 VS Code 扩展中，首先在“设置”->“Claude Code”中打开自动模式，然后从会话中的权限模式下拉列表中选择它。

[探索文档](https://code.claude.com/docs/en/permission-modes#eliminate-prompts-with-auto-mode) 了解更多信息。
