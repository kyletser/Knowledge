# 通过贡献指标了解 Claude Code 的影响

> 发布日期：2026-01-29 · [原文链接](https://claude.com/blog/contribution-metrics) · 机器翻译，仅供学习。

今天，我们在 Claude Code 中引入贡献指标，该指标已在公开测试版中提供。工程团队现在可以衡量 Claude Code 如何影响其团队的速度，在 Claude 的帮助下跟踪交付的 PR 和提交的代码。

## **我们如何在 Anthropic 发货**

Anthropic 的工程团队广泛使用 Claude Code，贡献数据帮助我们量化其影响。随着 Claude Code 内部采用率的增加，我们发现每位工程师每天合并的 PR 增加了 67%。在各个团队中，70-90% 的代码现在是在 Claude Code 的帮助下编写的。

虽然拉取请求本身并不能完全衡量开发人员的速度，但我们发现它们可以密切代表工程团队关心的事情：交付功能、修复错误和更快地取悦用户。

Claude Code 中的新贡献指标可帮助您衡量自己组织中的这种影响。

## **使用 Claude Code 测量速度**

通过与 GitHub 集成，贡献指标呈现以下数据点：

- **合并请求请求**：跟踪使用和不使用 Claude Code 协助创建的 PR
- **代码已提交**：在有或没有 Claude Code 帮助的情况下查看提交到存储库的代码行
- **每个用户的贡献数据**：确定整个团队的采用模式

贡献数据是通过将 Claude Code 会话活动与 GitHub 提交和 PR 进行匹配来计算的。我们保守地计算这一点，只有我们对 Claude Code 的参与有很高信心的代码才算作协助。

![](images/4253203e3dd7-697aba6d44c54e6710747e68-contribution-metrics-2.png)

![](images/252c0e28a99b-697aba633790d097ad08c6fc-contribution-metrics-1.png)

这些指标显示在您现有的 Claude Code 分析仪表板中，可供工作区管理员和所有者访问。不需要外部工具或数据管道。只需安装我们的 GitHub 应用程序并验证您组织的 GitHub 帐户，指标就会自动填充在仪表板上。

贡献指标旨在补充您现有的工程 KPI。将它们与 DORA 指标、冲刺速度或其他度量一起使用，以了解将 Claude Code 引入团队后的方向变化。

## **开始使用**

代码贡献指标现已为 Claude 团队和企业客户提供测试版。要启用它们：

1. 安装 [Claude GitHub 应用程序](https://github.com/apps/claude) 为您的组织
2. 导航至 [管理设置 > Claude Code](http://claude.ai/admin-settings/claude-code) 并打开 GitHub Analytics
3. 向您的 GitHub 组织进行身份验证

当您的团队使用 Claude Code 时，指标开始自动填充。查看 [文档](https://code.claude.com/docs/en/analytics) 有关详细的设置说明和解释指标的指导。
