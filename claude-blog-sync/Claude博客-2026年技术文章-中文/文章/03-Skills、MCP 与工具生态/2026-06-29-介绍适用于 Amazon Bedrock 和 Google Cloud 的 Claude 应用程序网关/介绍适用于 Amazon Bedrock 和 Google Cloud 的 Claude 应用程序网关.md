# 介绍适用于 Amazon Bedrock 和 Google Cloud 的 Claude 应用程序网关

> 发布日期：2026-06-29 · [原文链接](https://claude.com/blog/introducing-the-claude-apps-gateway) · 机器翻译，仅供学习。

今天，我们推出适用于 Amazon Bedrock 和 Google Cloud 的 Claude 应用程序网关。以前，在这些平台上运行 Claude Code 意味着为每个开发人员配置云凭证，手动将设置推送到每台笔记本电脑，并建立单独的工具来查看每个开发人员的支出。该网关是一个自托管控制平面，可为您提供企业 SSO 登录、集中实施的策略、基于角色的访问以及 Claude Code 的每用户成本归因。

## **部署网关**

该网关作为部署在 Linux 上的单个无状态容器运行，并由 PostgreSQL 数据库支持。它保存您的上游凭据，根据您的身份提供商对开发人员进行身份验证，分发和强制执行托管设置，并向您操作的收集器报告每个用户的使用情况。加入开发人员意味着将他们添加到您的身份提供商 (IdP)。下班意味着将他们移除。

该网关由 Anthropic 在同一内部构建和发货 `claude` 您的开发人员已经安装了二进制文件，因此您可以在基础设施上的一个无状态容器中运行它。由于网关和客户端是构建在一起的， `/login` flow 具有网关感知能力，客户端在登录时自动应用托管设置，并且对每个请求一致地执行策略。

## **网关的工作原理**

网关处理：

- **身份。** 它充当针对 Google Workspace、Microsoft Entra ID、Okta 或任何符合标准的 OIDC 提供商的 OpenID Connect (OIDC) 依赖方，并发出短期会话。开发人员的机器上没有长久的秘密。
- **政策。** 您可以在服务器上定义一次托管设置，客户端在登录时收到策略，网关会针对每个请求强制执行该策略。您可以集中调整允许的模型和默认设置。
- **遥测。** 客户端为每个请求标记一个使用指标，网关通过 OTLP 将其转发到您在网络中并按照保留计划配置的收集器。
- **路由。** 网关保存您的上游凭证，并将推理路由到 Claude API、Amazon Bedrock 或 Google Cloud，并在提供程序之间提供可选的故障转移。
- **花费上限。** 该网关允许您设置每日、每周和每月的支出限额。限制可以应用于每个组织、组或用户。

网关不会将推理流量或使用数据发送到 Anthropic，除非您将其配置为使用 Claude API。我们还发布了网关使用的协议，以便其他网关开发人员可以实现相同的功能。

## **开始使用**

该网关现已可用。开始使用：

- **部署网关**：下载Claude Code CLI二进制文件，点 `gateway.yaml` 在您的 OIDC 颁发者和上游凭证中，并在您的 IdP 中注册一个 OIDC 应用程序。
- **推出来**：配置 `forceLoginMethod` 和 `forceLoginGatewayUrl` 参数在 `managed-settings.json` 在客户端计算机上。客户端在首次启动时连接到您的网关。

[查看文档](https://code.claude.com/docs/en/claude-apps-gateway) 了解更多。
