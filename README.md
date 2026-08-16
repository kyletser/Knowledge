# Knowledge

个人 AI 与 Agent 技术知识库，集中归档技术文章、中文书稿、Claude Blog 译文，以及 Agent Harness 的学习与实践项目。

## 内容导航

| 目录 | 内容 | 快速入口 |
| --- | --- | --- |
| [`AI`](AI/) | AI Coding、Agent 工程、评测、治理、Skills 与 Harness Engineering 等主题文章 | [浏览文章](AI/) |
| [`ai-agent-book`](ai-agent-book/) | AI Agent 中文书稿，涵盖上下文工程、记忆、工具、评估、多模态与多 Agent 协作等主题 | [从引言开始](ai-agent-book/book/introduction.md) |
| [`claude-blog-sync`](claude-blog-sync/) | Claude Blog 抓取、增量归档与翻译工具，以及 2026 年技术文章中文译文 | [中文文章总目录](<claude-blog-sync/Claude博客-2026年技术文章-中文/2026-index.md>) · [工具说明](claude-blog-sync/README.md) |
| [`learn-claude-code-main`](learn-claude-code-main/) | 从 Agent Loop 到 MCP Plugin 的 20 个渐进式 Claude Code / Agent Harness 实作章节 | [中文课程说明](learn-claude-code-main/README-zh.md) |

## 仓库结构

```text
Knowledge/
├─ AI/                         # AI 与 Agent 技术文章
├─ ai-agent-book/
│  └─ book/                   # AI Agent 中文书稿（10 章及附录）
├─ claude-blog-sync/
│  ├─ Claude博客-2026年技术文章-中文/
│  ├─ src/                    # 抓取与翻译工具源码
│  └─ tests/
└─ learn-claude-code-main/
   ├─ s01_agent_loop/         # 从基础 Agent Loop 开始
   ├─ ...
   ├─ s20_comprehensive/      # 综合实现
   ├─ tests/
   └─ web/
```

## 使用方式

克隆仓库：

```bash
git clone https://github.com/kyletser/Knowledge.git
cd Knowledge
```

Markdown 内容可直接在 GitHub 或本地编辑器中阅读。需要运行抓取工具、课程代码或测试时，请进入对应子目录，并按照该目录的 README 安装依赖和执行命令。

## 说明

- Claude Blog 中文归档目前收录 2026 年 62 篇技术文章，按 Claude Code、智能体、Skills/MCP、模型与提示工程、安全合规、工程案例六个模块整理。
- 译文为机器翻译，术语或语义可能存在误差，请以文章中链接的英文原文为准。
- 仓库包含整理、翻译或引用的第三方内容；相关内容的版权与许可遵循原作者及对应项目的声明。
