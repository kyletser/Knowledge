# 如何以及何时在 Claude Code 中使用子代理

> 发布日期：2026-04-07 · [原文链接](https://claude.com/blog/subagents-in-claude-code) · 机器翻译，仅供学习。

[Claude Code](https://code.claude.com/docs/en/overview) 能够很好地处理复杂、多步骤的项目，但长时间的训练会增加体重。每个读取的文件、探索的每个切线、每个半完成的想法都停留在上下文窗口中，从而减慢了响应速度并提高了代币成本。

考虑在大型 TypeScript monorepo 中构建新功能。主要工作是实现，但副任务不断出现：跟踪现有服务如何处理身份验证，找到用于日期格式化的共享实用程序，检查设计系统是否已经具有接近您需要的组件。这些都不需要完整的项目上下文，并且在主会话中运行它们会增加噪音。如果可以并行运行它们会怎样？

输入 [分代理](https://code.claude.com/docs/en/sub-agents)。子代理是一个独立的 Claude 实例，具有自己的上下文窗口。它接受一个任务，完成工作，然后只返回结果。将子代理视为 Claude Code 会话的浏览器选项卡：一个在不丢失主线程的情况下追逐切线的地方。

在本文中，我们将讨论何时使用子代理有意义、如何调用它们以及何时不值得这样做。

## 什么是子代理？

子代理是独立的智能体，可以使用自己的上下文窗口进行操作。当 Claude 生成子代理时，该助手独立工作以读取文件、探索代码或进行更改。当完成其任务时，子代理仅将相关结果返回到主对话。

每个子代理都会重新开始，不受对话历史或调用的技能的影响。多个子代理可以并行运行，并且每个子代理可以具有不同的权限：研究子代理可能具有只读访问权限，而实施子代理则具有完整的编辑功能。

Claude Code 包含多种内置子代理类型，包括：

- **通用型智能体** 用于复杂的多步骤任务
- **计划智能体** 在提出实施策略之前研究代码库
- **探索智能体** 针对快速只读代码搜索进行了优化

Claude Code 通常会自行生成子代理来处理分配的任务。还可以显式地指导该行为并定义 Claude 自动委托的可重用专家。知道何时联系子代理是该功能的有用之处。

## 什么时候应该使用子代理？

某些类别的工作明显受益于子代理授权。学会识别它们可以使该功能更加有效。

### 研究任务繁重

当了解某些内容的工作原理是更改它的先决条件时，子代理可以探索代码库并返回摘要，而不是将数十个文件转储到对话中。

**信号：** 收集上下文需要阅读数十个文件。

**好处：** 主要对话保持干净，综合的发现而不是原始内容出现。

### 多个独立任务

当修复多个文件中的错误、更新多个组件中的模式或进行彼此不依赖的更改时，并行子代理可以更快地完成任务。

**信号：** 子任务之间没有依赖关系。

**好处：** 同时工作的三个子代理通常可以在更短的时间内完成任务。

### 需要新的视角

当目标是对实施进行公正的审查时，子代理会提供一个干净的记录，因为它不会继承主要对话中的假设、上下文或盲点。

**信号：** 需要验证而不影响分析的对话历史记录。

**好处：** 更清晰、更客观的反馈。

**专业提示：** /clear 命令还重置上下文和对话历史记录，提供类似的公正的信息，但代价是完全丢失该历史记录。子代理获得了同样新鲜的视角，而主要对话保持不变。

### 提交前验证

在完成更改之前，独立的子代理可以验证实施是否过度适合测试或遗漏边缘情况。

**信号：** 在提交代码之前需要征求第二意见。

**好处：** 发现熟悉代码可能会掩盖的问题。

### 管道工作流程

当一项任务有不同的阶段（即设计，然后实施，然后测试）时，每个阶段都会受益于集中注意力。

**信号：** 具有明确交接的连续阶段。

**好处：** 每个子代理都专注于其阶段，没有来自其他阶段的上下文产生噪音。

‍**专业提示：** 当一项任务需要探索十个或更多文件，或者涉及三个或更多独立工作时，这是将 Claude 引导至子代理的强烈信号。

## 如何指导子代理的使用

存在多种调用子代理的方法，从简单的对话到自动化的工作流程。正确的起点取决于工作流程，并且随着模式的出现，复杂性可以分层。

### 会话调用

最灵活的方法是简单地要求 Claude 在对话中使用子代理。这适用于所有 Claude Code 界面：终端、VS Code、JetBrains、Web 和桌面应用程序。

可靠地调用子代理的自然语言模式包括：

- “使用子代理来探索身份验证在此代码库中的工作原理”
- “请单独的智能体检查此代码是否存在安全问题”
- “并行研究这个问题。同时检查 API 路由、数据库模型和前端组件”
- “启动子代理来修复不同包中的这些 TypeScript 错误”

明确很重要。指定范围，在任务独立时请求并行执行，并描述所需的输出。

这是一个有效的提示词结构：

```
Use subagents to explore this codebase in parallel:

1. Find all API endpoints and summarize their purposes
2. Identify the database schema and relationships
3. Map out the authentication flow

Return a summary of each, not the full file contents.
```

这个提示词之所以有效，是因为它明确定义了三个独立的任务，明确请求并行执行，并指定输出格式。 Claude 理解意图并生成适当的子代理。

有效对话调用的技巧包括：

- **明确任务范围。** “探索付款方式”胜过“探索一切”。
- **明确请求并行化。** 说“这些可以并行运行”或“同时处理所有三个”。
- **指定应返回的内容。** 摘要、具体发现或建议。命名输出格式有助于 Claude 交付它。
- **当公正的分析很重要时，询问新的背景。** “使用未看到我们之前讨论的子代理”可确保干净的评估。

**专业提示：** 当子代理需要一段时间时，Ctrl+B 将其发送到后台。对话可以在运行时继续，并在结束时自动显示结果。 /tasks 命令显示后台运行的所有内容。

### 自定义子代理

当不断请求相同类型的子代理（安全审阅者、测试编写者、文档校对者）时，可以将其定义为自定义子代理一次。

然后，只要任务与其描述匹配，Claude 就会自动委派给它，无需提示。

自定义子代理作为 markdown 文件存在于 `.claude/agents/` （项目级别，与团队共享）或 `~/.claude/agents/` （用户级别，可用于所有项目）。每个都有自己的系统提示词、工具权限以及可选的自己的模型。

创建一个的最简单方法是 /智能体命令，该命令以交互方式逐步完成设置，并可以根据描述生成初稿。该文件也可以手写，例如：

```
---
name: security-reviewer
description: Reviews code changes for security vulnerabilities,
  injection risks, auth issues, and sensitive data exposure.
  Use proactively before commits touching auth, payments, or user data.
tools: Read, Grep, Glob
model: sonnet
---

You are a security-focused code reviewer. Analyze the provided
changes for:
- SQL injection, XSS, and command injection risks
- Authentication and authorization gaps
- Sensitive data in logs, errors, or responses
- Insecure dependencies or configurations

Return a prioritized list of findings with file:line references
and a recommended fix for each. Be critical. If you find nothing,
say so explicitly rather than inventing issues.
```

完成此操作后，Claude 会自动将匹配的工作路由到子代理。也可以通过名称调用它：“让安全审核员查看分阶段的更改。”

自定义子代理在以下情况下效果最佳：

- 当任务匹配时，Claude 应该可以自动委派一名专家
- 这项工作受益于范围严格的系统提示词和受限的工具
- 配置应该在团队中共享或在项目中重用

**专业提示：** 描述字段是 Claude 用于决定何时委托的字段。要具体说明触发条件，而不仅仅是功能。 “在提交之前检查代码的安全问题”比“安全专家”更好。

有关完整的配置参考，包括权限模式以及项目和用户子代理如何交互，请参阅我们的 [Claude Code 子代理文档。](https://code.claude.com/docs/en/sub-agents)

### Claude.md说明

自定义子代理定义专家是谁。 Claude.md 文件定义了 Claude 何时应到达的规则。如果每个代码审查都应该经过只读子代理，或者每个架构问题都应该首先触发研究通过，那么 Claude.md 就是该策略所在的位置。 Claude 在每次对话开始时都会阅读它，因此整个会话和队友之间的行为保持一致，而无需任何人记住询问。

Claude.md 在以下情况下非常适合子代理指令：

- 代码审查应始终使用只读子代理
- 该项目有具体的研究模式Claude应遵循
- 团队成员和会议之间需要一致的行为

以下是一个简单的 Claude.md 文件示例，该文件在给定特定条件下触发子代理：

```
## Code review standards

When asked to review code, ALWAYS use a subagent with READ-ONLY access
(Glob, Grep, Read only). The review should ALWAYS check for:
- Security vulnerabilities
- Performance issues
- Adherence to project patterns in /docs/architecture.md

Return findings as a prioritized list with file:line references.
```

通过上述 Claude.md 文件，每个代码审查请求都会自动使用定义的模式，从而无需每次都指定它。

有关 Claude.md 文件的更多信息，请参阅 [为您的代码库自定义 Claude Code：设置 Claude.md 文件](https://preview.claude.ai/chat/link) 和我们的 Claude Code [Claude.md](http://claude.md) [文件文档](https://code.claude.com/docs/en/memory#claude-md-files).

### 技能

对于重复运行的复杂多步骤工作流程，技能提供了可重用的界面。在 .Claude/skills/ 中定义一次技能，然后使用 /skill-name 调用它，或者让 Claude 在任务与其描述匹配时自动加载它。

技能与 Claude.md 文件的范围不同。 Claude.md 文件始终会加载并塑造每次交互。技能是按需加载的，因为它是显式调用的，或者是因为 Claude 将当前任务与技能的描述字段相匹配。这使得技能成为工作流程的正确场所，这些技能应该可用，但不适用于每个提示词。

技能在以下情况下非常适合：

- 某些操作会定期运行
- 不同的团队成员需要访问相同的复杂操作
- 标准化团队中某些任务的执行方式很重要

以下是全面代码审查的深度审查技巧的示例：

```
# .claude/skills/deep-review/SKILL.md

---
name: deep-review
description: Comprehensive code review that checks security,
  performance, and style in parallel. Use when reviewing staged
  changes before a commit or PR.
---

Run three parallel subagent reviews on the staged changes:

1. Security review - check for vulnerabilities, injection risks,
   authentication issues, and sensitive data exposure
2. Performance review - check for N+1 queries, unnecessary iterations,
   memory leaks, and blocking operations
3. Style review - check for consistency with project patterns
   documented in /docs/style-guide.md

Synthesize findings into a single summary with priority-ranked issues.
Each issue should include the file, line number, and recommended fix.
```

在上面的代码片段中，/deep-review 按需触发由三部分组成的子代理分析。因为描述提到在提交之前审查分阶段的更改，所以 Claude 也可以在上下文出现时自动使用此技能。

技能是一个目录，而不是单个文件。旁边 `SKILL.md,` 它可以保存 Claude 填写的模板、显示预期格式的示例输出或作为工作流程的一部分执行的脚本 Claude。遗产 `.claude/commands/` 格式是单个平面文件，因此所有内容都必须位于提示词本身中。

有关使用 Claude Code 技能的更多信息，请参阅我们的 [Claude Code 技能文档。](https://code.claude.com/docs/en/skills#extend-claude-with-skills)

### 挂钩

挂钩是用户定义的 shell 命令、HTTP 端点或 LLM提示词，它们在 Claude Code 生命周期的特定点自动执行。 [挂钩](https://code.claude.com/docs/en/hooks-guide) 可以根据事件自动执行子代理工作流程。挂钩触发特定操作并运行子代理任务，无需手动调用。

在以下情况下，Hook 是正确的工具：

- 每个提交在创建之前都应该被自动审查
- 安全检查应该在没有人记得询问的情况下进行
- 类似 CI 的质量门属于本地开发过程

下面是一个 Stop 钩子的示例，它阻止 Claude 结束其回合，直到测试通过：

```
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-tests.sh"
          }
        ]
      }
    ]
  }
}
```

脚本位于 `.claude/hooks/check-tests.sh`:

```
#!/bin/bash
INPUT=$(cat)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')

# Don't loop forever — if we already blocked once this turn, let it through
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi

if ! npm test --silent > /dev/null 2>&1; then
  jq -n '{
    decision: "block",
    reason: "Tests are failing. Run `npm test` to see the failures and fix them before finishing."
  }'
  exit 0
fi

exit 0
```

当 Claude 完成其回合时，将触发 Stop 事件。该脚本运行测试套件 - 如果测试失败，它会返回 JSON `decision: "block"` 和一个 `reason`。 Claude Code 读取该信息，不会让 Claude 停止，并将原因反馈到对话中作为继续工作的指令。的 `stop_hook_active` 顶部的防护可防止无限循环：如果 Claude 由于先前的 stop-hook 块而已经继续，则脚本会让它退出。

Hook 代表了最自动化的子代理编排方法。会话调用或 Claude.md 指令是更好的起点；随着工作流程的成熟，挂钩会出现得更晚。

有关完整的钩子配置，请参见 [Claude Code 高级用户定制：如何配置挂钩](https://claude.com/blog/how-to-configure-hooks) 或我们的 [Claude Code 挂钩文档](https://code.claude.com/docs/en/hooks).

## 使用子代理的实用模式

以下模式演示了应用于常见场景的子代理方向。

### 实施前研究

当向不熟悉的代码添加功能时，首先将研究委托给子代理，以保持实现讨论的知情性而不是探索性，例如：

```
Before I implement user notifications, use a subagent to research:
- How are emails currently sent in this codebase?
- What notification patterns already exist?
- Where should new notification logic live based on the current architecture?

Summarize findings, then we'll plan the implementation together.
```

收到的是综合摘要，而不是二十个原始上下文文件，并且实现讨论从坚实的基础开始。

### 并行修改

当同一模式需要跨多个文件更新时，并行子代理可以更快地完成并保持焦点，例如：

```
Use parallel subagents to update the error handling in these files:
- src/api/users.ts
- src/api/orders.ts
- src/api/products.ts

Each should follow the pattern established in src/api/auth.ts.
Work on all three simultaneously.
```

三个并行工作的子代理的完成时间大致与一个子代理所需的时间相当。每个人都专注于自己的文件，而没有其他人的上下文，从而造成混乱或不一致。

### 独立审查

实施复杂的操作后，不受实施过程影响的子代理的验证可以捕获熟悉度所掩盖的内容，例如：

```
Use a fresh subagent with read-only access to review my implementation of the payment flow. It should not see our previous discussion. I want an unbiased review.

Check for: security vulnerabilities, unhandled edge cases, and error handling gaps. Be critical.
```

审查子代理在不知道考虑了哪些权衡、拒绝了哪些方法或做出了哪些假设的情况下评估了代码。这种外部视角揭示了主要对话可能忽略的问题。

### 管道工作流程

对于多阶段任务，通过阶段之间的显式切换链接子代理可以保持每个阶段的重点，例如：

```
Let's build this feature as a pipeline:

1. First subagent: Design the API contract and write it to docs/api-spec.md
2. Second subagent: Implement the backend endpoints based on that spec
3. Third subagent: Write integration tests for the implementation

Each stage should complete before the next begins. Use the output
files as the handoff mechanism between stages.
```

使用管道工作流程，任务中的每个阶段都会接收重点上下文。设计子代理不会因实现问题而分心，实现子代理根据干净的规范工作，测试子代理独立评估结果。

## 什么时候不应该使用子代理？

虽然子代理是一个有用的功能，但子代理会带来开销。每个都启动自己的上下文，消耗令牌，并在开发人员和工作之间添加一层间接层。当上下文隔离、并行性或新的视角确实有帮助时，这些成本是值得的。

对于较小或紧密连续的任务，坚持主要对话通常更简单，例如：

- **连续的、相互依赖的工作。** 当第二步需要第一步的完整输出，而第三步需要两者时，处理链的单个会话通常比通过文件传递状态的子代理中继更干净。
- **同一文件编辑。** 两个子代理并行编辑同一文件会导致冲突。在这种情况下，请在一个上下文窗口中保持紧密耦合的更改。
- **小任务。** 对于快速解决问题或集中解决问题，委派的开销超过了好处。只需提示词或在您的主要对话中询问。
- **太多专家智能体。** 为所有内容定义自定义子代理是很诱人的，但是用选项淹没 Claude 会使自动委派不太可靠。大多数团队都会选择少数范围广泛的智能体，而不是庞大的名单。
- **需要智能体相互配合的工作。** 子代理向主要对话汇报，但不能相互交谈。对于子代理需要通信的任务，使用 [智能体团队](https://code.claude.com/docs/en/agent-teams)。对于智能体团队，子代理在不同的会话之间而不是在一个会话内进行协调，这使得它们更重、更昂贵。有关何时使用子代理与智能体Teams 的更多指导，请查看我们的 [Claude Code智能体团队文档](https://code.claude.com/docs/en/agent-teams).

前面描述的信号（即需要第二意见、子任务之间缺乏依赖性以及广泛的研究）清楚地表明何时委派给子代理是值得的。

## 开始对话，稍后自动化

精心使用时，子代理可以发挥其全部价值。 Claude 提供的自动调用很有帮助，但知道何时委派研究、并行工作以及请求新的视角会产生比碰运气更好的结果。

使用子代理时，请从会话提示词开始。注意哪些请求不断发生，并随着这些模式的澄清而构建自动化。目标是让子代理轻松委派，以便您的注意力集中在重要的工作上。
