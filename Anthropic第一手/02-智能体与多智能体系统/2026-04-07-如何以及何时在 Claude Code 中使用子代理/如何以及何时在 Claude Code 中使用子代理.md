# 如何以及何时在 Claude Code 中使用子代理

> 来源：Claude Blog · Anthropic
> 原文链接：[how-and-when-to-use-subagents-in-claude-code](https://claude.com/blog/how-and-when-to-use-subagents-in-claude-code)
> 发布日期：2026-04-07
> 译校：对照英文原文人工重译

---

[Claude Code](https://claude.com/product/claude-code) 很擅长处理复杂、多步骤的项目，但漫长的会话会不断累积负担。每一个被读取的文件、每一次被探索的旁支、每一个半成形的念头，都停留在上下文窗口里，拖慢响应速度，推高 token 成本。

不妨设想在一个大型 TypeScript monorepo 中构建新功能。主要工作是做实现，但旁支任务层出不穷：追溯某个现有服务如何处理鉴权、找到用于日期格式化的共享工具函数、查看设计系统里是否已有接近你需求的组件。这些都不需要完整的项目上下文，把它们放在主会话里跑只会增加噪音。要是能并行跑它们呢？

这就引出 [子代理](https://code.claude.com/docs/en/sub-agents)（subagents）。子代理是一个独立的 Claude 实例，拥有自己的上下文窗口。它接受一个任务、完成工作，然后只返回结果。可以把子代理想象成 Claude Code 会话里的浏览器标签页：一个让你去追旁支、又不会丢失主线程的地方。

本文中，我们将讨论何时使用子代理才有意义、如何调用它们，以及何时不值得这么做。

## 什么是子代理？

子代理是独立的智能体，运作于自己的上下文窗口之中。当 Claude 生成一个子代理时，这个助手会独立地去读文件、探索代码，或做出改动。任务完成后，子代理只把相关的成果返回给主对话。

每个子代理都从零开始，不受对话历史或被调用技能的影响。多个子代理可以并行运行，且各自可以拥有不同的权限：一个研究型子代理可能只有只读权限，而实现型子代理则拥有完整的编辑能力。

子代理之所以好用，关键在于懂得何时动用它。Claude Code 内置了若干种子代理类型，包括：

- **通用智能体**（general-purpose），用于复杂的多步骤任务
- **规划智能体**（plan agents），在研究代码库之后才给出实现策略
- **探索智能体**（explore agents），为快速、只读的代码搜索而优化

Claude Code 常常会自动派生子代理来处理被分配的任务。你也可以显式地引导这种行为，并定义可复用的专家，让 Claude 自动把任务委派给它们。

## 何时该用子代理？

有若干类工作明显受益于子代理委派。学会识别它们，能让这个功能发挥出大得多的作用。

### 研究密集型任务

当「理解某物如何运作」是「改动它」的前提时，子代理可以探索代码库并返回一个摘要，而不是把几十个文件一股脑倒进对话里。

**信号：** 收集上下文需要阅读几十个文件。

**好处：** 主对话保持干净，拿到的是经过综合的发现，而非原始内容。

### 多个相互独立的任务

当要在多个文件中修复错误、在多个组件里更新模式，或是做彼此无依赖的改动时，并行子代理能更快完成任务。

**信号：** 子任务之间互不依赖。

**好处：** 三个子代理同时工作，通常能在更短的时间内完成。

### 需要全新视角

当目标是给某个实现做一次不带偏见的审查时，子代理能提供一个干净的起点，因为它不会继承主对话里的假设、上下文或盲点。

**信号：** 需要不受对话历史影响的验证。

**好处：** 更干净、更客观的反馈。

**专业建议：** `/clear` 命令同样会重置上下文与对话历史，提供类似的「无偏见白纸」，代价是彻底丢失那段历史。子代理能在主对话保持完整的同时，达到同样的新鲜视角。

### 提交前验证

在敲定改动之前，一个独立的子代理可以验证实现是否过拟合于测试、或遗漏了边界情况。

**信号：** 提交代码前值得征求第二意见。

**好处：** 能抓住那些因对代码过于熟悉而被忽略的问题。

### 管道式工作流

当任务有清晰的阶段（如先设计、再实现、后测试）时，每个阶段都能受益于专注的注意力。

**信号：** 带有明确交接的连续阶段。

**好处：** 每个子代理专注于自己的阶段，不会被其他阶段的上下文干扰。

**专业建议：** 当一项任务需要探索十个以上文件，或涉及三个及以上相互独立的子工作时，就是一个强烈的信号——该把 Claude 引向子代理了。

## 如何引导子代理的使用

调用子代理有多种方式，从简单的对话到自动化工作流都有。正确的起点取决于你的工作流，而随着模式逐渐清晰，可以再叠加更复杂的手段。

### 对话式调用

最灵活的方式，就是直接在对话中要求 Claude 使用子代理。这种方式在所有 Claude Code 界面上都有效：终端、VS Code、JetBrains、Web 以及桌面应用。

能稳定触发子代理的自然语言模式包括：

- 「用子代理去探索这个代码库里鉴权是怎么实现的」
- 「让一个独立的智能体审查这段代码有没有安全问题」
- 「并行研究这个问题。同时查一下 API 路由、数据库模型和前端组件」
- 「派生子代理去修复不同包里的这些 TypeScript 错误」

说得明确很重要。界定好范围，在任务相互独立时要求并行执行，并描述你希望得到的输出。

下面是一个有效的提示词结构：

```
Use subagents to explore this codebase in parallel:

1. Find all API endpoints and summarize their purposes
2. Identify the database schema and relationships
3. Map out the authentication flow

Return a summary of each, not the full file contents.
```

这个提示词之所以有效，是因为它清晰地定义了三个相互独立的任务、显式要求了并行执行，并指定了输出格式。Claude 理解了意图，便会派生合适的子代理。

有效的对话式调用技巧包括：

- **明确任务范围。** 「探索付款是怎么运作的」胜过「探索一切」。
- **显式要求并行。** 说「这些可以并行跑」或「同时处理这三项」。
- **指定应当返回什么。** 摘要、具体发现，还是建议？点明输出格式能帮助 Claude 交付到位。
- **当不带偏见的剖析很重要时，要求全新上下文。** 「用一个看不到我们此前讨论的子代理」能确保评估干净。

**专业建议：** 当某个子代理要跑一阵子时，按 Ctrl+B 把它送到后台。对话可以在它运行期间继续，结果在它完成时自动浮现。`/tasks` 命令会显示所有在后台运行的内容。

### 自定义子代理

当同一种子代理被反复请求时（安全审查员、测试编写者、文档校对者），可以一次性把它定义为一个自定义子代理。

此后，只要任务与其描述匹配，Claude 就会自动委派给它，无需任何提示。

自定义子代理以 markdown 文件的形式存在：放在 `.claude/agents/`（项目级，与团队共享）或 `~/.claude/agents/`（用户级，在所有项目中可用）。每一个都有自己的系统提示词、工具权限，以及可选的专属模型。

最简单的创建方式是 `/agents` 命令，它会以交互方式引导你完成设置，并能根据描述生成初稿。文件也可以手写，例如：

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

配置好之后，Claude 会自动把匹配的工作路由给该子代理。也可以通过名字调用它：「让 security-reviewer 看一下暂存的改动。」

自定义子代理在以下情况下效果最佳：

- 当某项任务匹配时，应当有一位专家让 Claude 自动委派
- 工作受益于范围收紧的系统提示词与受限的工具
- 配置需要在团队间共享，或在多个项目中复用

**专业建议：** `description` 字段是 Claude 用来决定何时委派的依凭。要具体写明触发条件，而不只是能力。「在提交前审查代码的安全问题」比「安全专家」路由得更准。

关于完整的配置参考（包括权限模式，以及项目级与用户级子代理如何交互），请参阅我们的 [Claude Code 子代理文档](https://code.claude.com/docs/en/sub-agents)。

### CLAUDE.md 指令

自定义子代理定义的是「专家是谁」。CLAUDE.md 文件定义的则是「Claude 何时该动用它们」的规则。如果每次代码审查都应走只读子代理，或者每个架构问题都该先触发一轮研究，那么 CLAUDE.md 就是安放这条策略的地方。Claude 在每轮对话开始时都会读取它，因此无论跨会话还是跨团队成员，行为都能保持一致，而无需任何人记得去要求。

CLAUDE.md 适合承载子代理指令的场景包括：

- 代码审查应当始终使用只读子代理
- 项目有特定的研究模式需要 Claude 遵循
- 需要在团队成员与多次会话之间保持行为一致

下面是一个简单的 CLAUDE.md 文件示例，它会在特定条件下触发子代理：

```
## Code review standards

When asked to review code, ALWAYS use a subagent with READ-ONLY access
(Glob, Grep, Read only). The review should ALWAYS check for:
- Security vulnerabilities
- Performance issues
- Adherence to project patterns in /docs/architecture.md

Return findings as a prioritized list with file:line references.
```

有了上面的 CLAUDE.md 文件，每一次代码审查请求都会自动套用所定义的模式，无需每次都重新指定。

关于 CLAUDE.md 文件的更多信息，请参阅 [为你的代码库定制 Claude Code：设置 CLAUDE.md 文件](https://preview.claude.ai/chat/link) 以及我们的 Claude Code [CLAUDE.md](http://claude.md) [文件文档](https://code.claude.com/docs/en/memory#claude-md-files)。

### 技能（Skills）

对于需要反复运行的复杂多步骤工作流，技能（Skills）提供了一个可复用的接口。在 `.claude/skills/` 中定义一次技能，然后用 `/skill-name` 调用它，或者让 Claude 在任务与其描述匹配时自动加载。

技能与 CLAUDE.md 文件在作用范围上不同。CLAUDE.md 文件始终被加载，并且塑造每一次交互。技能则是按需加载——要么被显式调用，要么因为 Claude 将当前任务与技能的描述字段匹配上。这使得技能成为「应当可用、但不必套用到每个提示词」那类工作流的正确归宿。

技能在以下情况下很合适：

- 某些操作会定期运行
- 不同成员需要访问同一套复杂操作
- 在团队中统一某些任务的执行方式很重要

下面是一个用于全面代码审查的 deep-review 技能示例：

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

在上面的代码片段中，`/deep-review` 会按需触发一场由三部分组成的子代理分析。因为描述里提到了「在提交前审查暂存改动」，当这种上下文出现时，Claude 也能自动动用这个技能。

技能是一个目录，而非单个文件。在 `SKILL.md` 之外，它还可以放置供 Claude 填充的模板、展示预期格式的示例输出，或是作为工作流一部分由 Claude 执行的脚本。旧式的 `.claude/commands/` 格式是单个扁平文件，因此所有内容都必须塞进提示词本身。

关于在 Claude Code 中使用技能的更多信息，请参阅我们的 [Claude Code 技能文档](https://code.claude.com/docs/en/skills#extend-claude-with-skills)。

### 钩子（Hook）

钩子（Hook）是用户定义的 shell 命令、HTTP 端点或 LLM 提示词，会在 Claude Code 生命周期的特定节点自动执行。[钩子](https://code.claude.com/docs/en/hooks-guide) 可以基于事件来自动化子代理工作流。钩子在特定动作上触发，无需手动调用即可运行子代理任务。

在以下情况下，钩子是合适的工具：

- 每次提交在创建前都应当被自动审查
- 安全检查应当在没人记得去要求的情况下也能运行
- 类 CI 的质量关卡应当嵌入本地开发流程

下面是一个 Stop 钩子的示例，它会在测试通过前阻止 Claude 结束自己的回合：

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

脚本位于 `.claude/hooks/check-tests.sh`：

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

当 Claude 结束自己的回合时，Stop 事件被触发。脚本运行测试套件——如果测试失败，它会返回 `decision: "block"` 和 `reason` 的 JSON。Claude Code 读到后，不让 Claude 停下，而是把原因作为「继续工作」的指令反馈回对话。顶部的 `stop_hook_active` 护栏能防止无限循环：如果 Claude 已经因为上一轮 stop-hook 的阻拦而继续，脚本就会让它退出。

钩子代表了子代理编排中最自动化的手段。对话式调用或 CLAUDE.md 指令才是更好的起点；随着工作流成熟，再引入钩子。

关于完整的钩子配置，请参阅 [Claude Code 高级用户定制：如何配置钩子](https://claude.com/blog/how-to-configure-hooks) 或我们的 [Claude Code 钩子文档](https://code.claude.com/docs/en/hooks)。

## 使用子代理的实用模式

以下模式演示了把子代理引导应用于常见场景。

### 实现前先做研究

当向不熟悉的代码添加功能时，先把研究委派给一个子代理，能让后续的「实现讨论」建立在充分知情的基础上，而非探索性的，例如：

```
Before I implement user notifications, use a subagent to research:
- How are emails currently sent in this codebase?
- What notification patterns already exist?
- Where should new notification logic live based on the current architecture?

Summarize findings, then we'll plan the implementation together.
```

拿到的是经过综合的摘要，而非二十个原始上下文文件，实现讨论也从一个扎实的基础上开始。

### 并行修改

当同一模式需要跨多个文件更新时，并行子代理能更快完成，并保持专注，例如：

```
Use parallel subagents to update the error handling in these files:
- src/api/users.ts
- src/api/orders.ts
- src/api/products.ts

Each should follow the pattern established in src/api/auth.ts.
Work on all three simultaneously.
```

三个并行工作的子代理，耗时大致与一个子代理单独完成相当。每个都专注于自己的文件，没有来自其他子代理的上下文，也就不会产生混乱或不一致。

### 独立审查

在实现一个复杂功能之后，让一个不受实现过程影响的子代理来做验证，能抓住那些因过于熟悉而被掩盖的问题，例如：

```
Use a fresh subagent with read-only access to review my implementation of the payment flow. It should not see our previous discussion. I want an unbiased review.

Check for: security vulnerabilities, unhandled edge cases, and error handling gaps. Be critical.
```

审查子代理在评估代码时，并不知道曾考虑过哪些权衡、否决过哪些方案、做过哪些假设。这种外部视角能揭示主对话可能忽略的问题。

### 管道式工作流

对于多阶段任务，通过阶段之间显式的交接把子代理串起来，能让每个阶段保持专注，例如：

```
Let's build this feature as a pipeline:

1. First subagent: Design the API contract and write it to docs/api-spec.md
2. Second subagent: Implement the backend endpoints based on that spec
3. Third subagent: Write integration tests for the implementation

Each stage should complete before the next begins. Use the output
files as the handoff mechanism between stages.
```

使用管道式工作流，任务中的每个阶段都能收到聚焦的上下文。设计子代理不会被实现问题分心，实现子代理依据干净的规格工作，测试子代理则独立评估结果。

## 何时不该用子代理？

子代理虽好用，却也带着开销。每一个都要拉起自己的上下文、消耗 token，并在开发者与工作之间多垫一层间接。只有当上下文隔离、并行化或全新视角确实有帮助时，这笔成本才值得。

对于较小或紧密顺序的任务，留在主对话里通常更简单，例如：

- **顺序的、相互依赖的工作。** 当第二步需要第一步的完整输出、第三步又需要前两步时，用一个会话来处理整条链，通常比「靠文件传递状态的子代理接力」更干净。
- **同一文件内的编辑。** 两个子代理并行编辑同一文件，是冲突的温床。这种情况下，请把紧密耦合的改动留在同一个上下文窗口里。
- **小任务。** 对于快速修复或聚焦的问题，委派的额外开销会超过其收益。直接在主对话里提示或提问就好。
- **过多的专家智能体。** 为一切定义自定义子代理很诱人，但用过多选项淹没 Claude 会降低自动委派的可靠性。多数团队最终会收敛到少数几个边界清晰的智能体，而不是一份冗长的名册。
- **需要智能体彼此协调的工作。** 子代理向主对话汇报，却无法互相交谈。对于子代理需要彼此通信的任务，请使用 [智能体团队（Agent Teams）](https://code.claude.com/docs/en/agent-teams)。在智能体团队中，子代理是在不同的会话之间（而非同一会话内）协调，因此更重、也更贵。关于何时用子代理、何时用智能体团队的更多指引，请参阅我们的 [Claude Code 智能体团队文档](https://code.claude.com/docs/en/agent-teams)。

前文所述的那些信号（即需要第二意见、子任务之间缺乏依赖、以及广泛的研究），已经清楚地指明了何时把任务委派给子代理才值得。

## 从对话起步，日后再自动化

子代理在「被刻意使用」时才能发挥全部价值。Claude 提供的自动调用固然有用，但懂得何时委派研究、何时并行化工作、何时索取全新视角，收获的结果比听天由命要好得多。

使用子代理时，先从对话式提示词起步。留意哪些请求反复出现，并随着这些模式逐渐清晰而逐步构建自动化。目标是让子代理委派变得轻而易举，好让你的注意力留在真正重要的工作上。
