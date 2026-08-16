# 使用 Claude 的计算机和浏览器的最佳实践

> 来源：Claude Blog · Anthropic
> 原文链接：[best-practices-for-computer-and-browser-use-with-claude](https://claude.com/blog/best-practices-for-computer-and-browser-use-with-claude)
> 发布日期：2026-05-13 · 作者：Lucas Gonzalez、Luca Weihs
> 译校：对照英文原文人工重译

---

Claude 的[最新模型](https://www.anthropic.com/news/claude-sonnet-4-6)代表着计算机与浏览器使用能力的重大进步。凭借这些能力，LLM 现在能够为日益复杂的智能体式系统提供动力，去完成真实的工作，例如跨多种不同技术构建软件应用、自动化工作流。

在这篇博文中，我们分享了在计算机与浏览器中使用 Claude 的最佳实践，内容从简单的配置更改到更高级的集成模式。希望这篇文章能帮助你开始将 Claude 的计算机与浏览器使用能力集成到你的产品中。我们还发布了一个新的[演示实现](https://github.com/anthropics/claude-quickstarts/tree/main/computer-use-best-practices)，它封装了其中一些最佳实践，并提供了可用于在 Claude 计算机使用能力之上进行开发的额外工具。

*注意，除非另有说明，这些建议适用于 Claude 4.6 系列（Opus 4.6、Sonnet 4.6、Haiku 4.5）和 Claude Opus 4.7。如果 4.6 系列与 Opus 4.7 之间的指导有所不同，我们会在此处内联标注。我们的结论基于内部实验，并可能随着新模型与新技术出现而更新。*

# **入门：分辨率与缩放**

点击准确性是任何计算机使用集成的基础。如果点击没有落在它应该在的位置，下游的一切都无法运转：表单填不上、按钮按不动、工作流失败。影响最大的优化同时也最简单之一：在把截图发送到 API 之前，先对截图进行缩小（downscale）。

## **确保适当的缩放**

当你把一张截图发送到 Claude 的计算机使用 API 时，模型会看到它，并在你指定的 display_width_px / display_height_px 坐标空间中返回点击坐标。但有一个重要的限制：API 对图像尺寸有内部处理上限。超过这些上限的图像会在模型看到它们之前被缩小，这意味着模型是基于图像的降级版本来点击的，而你的线束期望坐标与原始分辨率对齐。

对于我们的 Claude 4.6 模型系列，API 的上限为：

- **最大长边**：1568 像素
- **最大总像素**：1.15 兆像素
- 图像只要超过**任意一项**上限，就会被内部缩小

我们的 Opus 4.7 模型支持更高的分辨率。其上限为：

- **最大长边**：2576 像素
- **最大总像素**：3.75 兆像素
- 图像只要超过**任意一项**上限，就会被内部缩小

当坐标空间与模型“看到”的图像不匹配时，模型预测的点击会落在一个与它实际所见图像不同的显示比例上。这是高分辨率下点击不准确的主要原因。解决方法很简单：在把截图发送到 API 之前，始终将其缩小到符合这些上限。我们一致观察到，图像一旦超过上限，准确性就会显著下降，而这一项改动的价值几乎超过其他任何优化。

## **推荐分辨率**

**从 1280x720 开始。** 对大多数用例来说，这是一个安全、实用的默认设置。它大约用掉 80% 的像素预算，稳稳落在长边和总像素上限之内，并且是模型在训练期间见过的一种标准分辨率。它同时适用于现代 Web UI 和传统桌面应用。

**如果你使用的是 Opus 4.7，我们建议从 1080p 开始**，因为它相比 720p 有显著提升，并在令牌使用与性能之间取得了良好平衡。

**对于想要最大化模型所接收视觉信息的开发者**，我们还推荐一种“最大 API 适配”（max API fit）的思路：根据源图像的原始宽高比，为每张图像计算最优分辨率：

```python
import math

# 4.6 系列为 1568，Opus 4.7 为 2576
MAX_LONG_EDGE = 1568

# 4.6 系列为 1.15MP，Opus 4.7 为 3.75MP
MAX_PIXELS = 1_150_000

def compute_max_api_fit(native_w, native_h):
    """Compute the largest resolution that fits API limits
    while preserving aspect ratio."""
    aspect = native_w / native_h

    # Compute max dimensions from pixel budget
    h_from_pixels = math.sqrt(MAX_PIXELS / aspect)
    w_from_pixels = h_from_pixels * aspect

    # Apply long edge constraint
    if native_w >= native_h:
        w = min(w_from_pixels, MAX_LONG_EDGE)
        h = w / aspect
    else:
        h = min(h_from_pixels, MAX_LONG_EDGE)
        w = h * aspect

    # Never upscale beyond native
    w = min(w, native_w)
    h = min(h, native_h)

    return int(w), int(h)
```

这种方法略复杂一些，但能避免宽高比失真，并充分利用每张图像可用的完整像素预算。相比固定的 1280x720，准确性的提升并不大，但它实现简单，能避免把 16:9 的源强制塞进 4:3 显示分辨率时所产生的失真。

**应避免的分辨率：**

- **原始分辨率（未缩放）**：除非你的源图像恰好低于分辨率上限，否则发送原始分辨率的截图是导致点击准确性差的最常见原因。
- **极低分辨率（低于 960x540）**：分辨率过低时，模型会丢失太多细节，无法准确识别小型 UI 元素。
- **如果在 MacOS 上**：浏览器使用的一个常见问题是，MacOS 上的截图往往以 2 的设备像素比（device pixel ratio）捕获，这意味着你最终得到的图像分辨率可能是屏幕坐标分辨率的 2 倍。
- **如果你使用的是 4.6 系列，请避免 1920x1080 及以上**：这些会超出像素上限，并被悄然缩小。在 Opus 4.7 上，上限更高（3.75 MP），因此 1080p 和 1440p 都在预算之内；但仍需避免在不缩小的情况下使用原生 4K。

## **坐标缩放**

当你在发送截图之前对其进行了缩放，模型会在你指定的显示分辨率中返回点击坐标。在执行点击之前，你必须把它们缩放回你的实际屏幕分辨率：

```python
# 你的屏幕是 screen_w x screen_h
# 你发送了一张被缩放到 display_w x display_h 的截图
scale_x = screen_w / display_w
scale_y = screen_h / display_h

screen_x = int(api_returned_x * scale_x)
screen_y = int(api_returned_y * scale_y)
```

这很简单却很关键，因为如果你忘记缩放，或者 `display_width_px` / `display_height_px` 与你发送图像的实际尺寸不匹配，每一次点击都会发生一致的偏移。

## **消息数组中的内容排序**

在构建消息内容数组时，请把文本指令放在图像*之前*，如下面的代码片段所示。这让模型在处理截图时知道它在找什么，从而提升点击准确性。

```python
# 推荐 —— 文本指令在前，截图在后：
content = [
    {"type": "text", "text": "Click on the Submit button"},
    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64}},
]

# 不推荐 —— 图像在前，文本在后：
content = [
    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64}},
    {"type": "text", "text": "Click on the Submit button"},
]
```

## **诊断点击问题**

如果点击没能命中目标，通常可以归结为以下某个原因：

| 症状 | 可能的原因 | 试试这个 |
| --- | --- | --- |
| 点击始终朝一个方向偏移 | - `display_width_px` / `display_height_px` 与发送的实际图像尺寸不匹配<br>- 截图超过 API 上限，正在被悄然缩小<br>- 内容排序是图像优先而非文本优先 | - 确保显示尺寸与你缩放后的截图完全匹配，而不是你的原始分辨率<br>- 预缩放到 1280x720，或使用 `compute_max_api_fit`<br>- 把文本指令移到内容数组中图像之前 |
| 点击大致落在正确区域，但没命中目标 | - 目标非常小（复选框、图标、切换开关）<br>- 源图像分辨率非常高（4K+），缩小过程中丢失了细节<br>- 强制使用非原生宽高比导致的宽高比失真 | - 对密集 UI 启用 `enable_zoom: True`<br>- 在以较低 DPI 捕获，或裁剪到相关屏幕区域之后再缩小<br>- 缩放时保留源宽高比 |
| 模型完全点错了元素 | - 指令含糊（当存在多个类似“提交”的按钮时说“点击提交”）<br>- 目标附近有视觉上相似的元素<br>- UI 对单条指令来说过于复杂 | - 使用更具体、带位置上下文的提示词（“点击表单右下方蓝色的提交按钮”）<br>- 把复杂交互拆成更小的步骤<br>- 提供关于页面布局的额外上下文 |
| 整体准确性较差 | - 发送的截图超过 API 上限<br>- 源图像来自极高分辨率显示器（4K+），且压缩比极大<br>- 分辨率太低，丢失了关键细节 | - 预缩小所有截图以符合上限<br>- 对于 4.6 系列上的 4K+ 源，Sonnet 比 Opus 4.6 更能耐受大幅缩小。在 Opus 4.7 上，这一差距已大幅缩小，请使用 4.7 的像素预算（最高 3.75 MP），从而一开始就减少所需缩小量<br>- 先以 1280x720 为基准；如果损失太大，就使用 `compute_max_api_fit` |

## **点击任务的模型选择**

根据我们的内部测试，Claude Sonnet 4.6 在点击上往往机械精度更高（空间精度更好、更接近命中），而 Claude Opus 4.6 带来更强的推理能力。当源图像需要大幅缩小时，Sonnet 4.6 也更加稳健。

Opus 4.7 缩小了这一差距：通过测试，我们发现它的点击精度与 Sonnet 4.6 大致相当，而且它更高的分辨率预算从一开始就减少了所需的缩小量，当你想要 Opus 级别的推理搭配强劲的点击精度时，它是一个强有力的选择。

对于大多数任务，我们建议从 Sonnet 4.6 开始，它在点击准确性、推理能力和成本之间提供了最佳平衡。当你想要更强的推理、尤其是使用高分辨率源图像时，请选择 Opus 4.7。当延迟是首要考量时，Haiku 4.5 仍然是一个极佳选项。高级工作流仍可能受益于“协调器 + 子代理”模式：由一个推理模型负责规划与决策，而由 Sonnet 或 Haiku 执行机械性的点击步骤。

## **处理小目标**

随着目标变小，点击精度会下降。大型和中型 UI 元素（按钮、输入框、标准菜单项）在安全区内的所有分辨率下都可靠。难点在于小型和微小目标，例如复选框、系统托盘图标、下拉箭头、小型切换开关，以及树视图的展开/折叠按钮。

如果你的应用需要频繁点击小目标，请考虑以下策略：

**对密集 UI 使用缩放。** Claude 4.6 和 4.7 模型支持缩放能力，让模型在点击前能以更高分辨率检视特定屏幕区域。在你的[工具配置](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)中启用它：

```python
{
    "type": "computer_20251124",
    "name": "computer",
    "display_width_px": 1280,
    "display_height_px": 720,
    "enable_zoom": True
}
```

**让目标更大。** 如果你控制着被自动化的 UI，那么哪怕只是适度增大点击目标的大小，也会对可靠性产生不成比例的影响。这可能意味着使用更低的系统 DPI、在浏览器中放大，或调整 UI 缩放设置。

**对微小目标使用键盘替代方案。** 对于非常小的元素（例如系统托盘图标或微小复选框），键盘快捷键或基于选项卡的导航可能比点击更可靠。如果你的工作流允许，提示模型在特定步骤使用键盘交互可以提高成功率。

**考虑源图像分辨率。** 来自 4K+ 显示器的截图被压缩到 720p 时会丢失大量细节（例如，3840x2160 原始分辨率下 16 像素的复选框，在 1280x720 显示分辨率下大约变成 5 像素，这使得目标更小、因而更难命中）。如果你使用的是极高分辨率的显示器，请考虑使用 Opus 4.7，它的分辨率上限比之前的模型更高。如果使用 4.6 系列模型，请考虑以较低的 DPI 捕获、使用显示缩放来放大 UI 元素，或者把截图聚焦在屏幕的相关部分而非整个显示上。因为这些模型用更少的像素表达更多的信息，我们观察到，随着源图像比例增大，性能会下降，也就是说需要更多的压缩。

## **我们测试过但无帮助的方法**

我们在内部评估中用几种流行的优化技术做了实验，没有发现这些方法能带来一致的提升，尽管具体结果可能因情况而异：

- **把图像拆成更小的图块**：把截图分割成象限或区域并分别发送，并没有提升点击准确性。
- **叠加带坐标的网格图案**：在截图上添加视觉坐标网格以帮助模型定位目标，并没有产生可靠的收益。
- **缩放算法的选择**：PIL LANCZOS、sips 以及其他常见的缩放算法产生的结果完全相同。用对你的技术栈最方便的那个即可。

## **检查故障**

如果模型在尝试上述修复后仍然行为不可预测，请记录完整的对话记录，并把预测的点击叠加到源截图上，以理解模型实际看到并作出了什么决定。

有些失败根本与点击准确性无关。例如，某些下拉菜单可能会调用浏览器视口无法捕获的系统级 UI——模型看似无法完成任务，但它根本看不到需要交互的那个菜单。在这种情况下，模型应当依赖替代方法，例如 JavaScript 执行、键盘导航，或直接操作文档对象模型（DOM），而不是点击。

## **快速参考**

*如何为计算机使用缩放并准备图像*

```python
import math
from PIL import Image
import base64
import io

# 4.6 系列为 1568，Opus 4.7 为 2576
MAX_LONG_EDGE = 1568

# 4.6 系列为 1.15MP，Opus 4.7 为 3.75MP
MAX_PIXELS = 1_150_000

def prepare_screenshot(screenshot: Image.Image, native_w: int, native_h: int) -> tuple[str, int, int]:
    """Resize a screenshot to fit API limits and return base64 + display dimensions."""

    # Option A: Fixed 720p (simple, reliable)
    display_w, display_h = 1280, 720

    # Option B: Max API fit (maximizes fidelity)
    # display_w, display_h = compute_max_api_fit(native_w, native_h)

    resized = screenshot.resize((display_w, display_h), Image.LANCZOS)

    buffer = io.BytesIO()
    resized.save(buffer, format="PNG")
    b64 = base64.standard_b64encode(buffer.getvalue()).decode()

    return b64, display_w, display_h


def scale_coordinates(api_x: int, api_y: int, display_w: int, display_h: int,
                      screen_w: int, screen_h: int) -> tuple[int, int]:
    """Scale API-returned coordinates back to native screen space."""
    screen_x = int(api_x * (screen_w / display_w))
    screen_y = int(api_y * (screen_h / display_h))
    return screen_x, screen_y


def compute_max_api_fit(native_w: int, native_h: int) -> tuple[int, int]:
    """Compute the largest resolution that fits API limits while preserving aspect ratio."""
    aspect = native_w / native_h
    h_from_pixels = math.sqrt(MAX_PIXELS / aspect)
    w_from_pixels = h_from_pixels * aspect

    if native_w >= native_h:
        w = min(w_from_pixels, MAX_LONG_EDGE)
        h = w / aspect
    else:
        h = min(h_from_pixels, MAX_LONG_EDGE)
        w = h * aspect

    w = min(w, native_w)
    h = min(h, native_h)
    return int(w), int(h)
```

**用法：**

```python
import anthropic
from PIL import Image

client = anthropic.Anthropic()

# Capture screenshot (your method here)
screenshot = Image.open("screenshot.png")
native_w, native_h = screenshot.size

# Prepare for API
b64, display_w, display_h = prepare_screenshot(screenshot, native_w, native_h)

# Send to Claude — text before image
response = client.beta.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    betas=["computer-use-2025-11-24"],
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Click on the Submit button"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
        ]
    }],
    tools=[{
        "type": "computer_20251124",
        "name": "computer",
        "display_width_px": display_w,
        "display_height_px": display_h,
    }],
)

# Scale coordinates back for execution
api_x, api_y = extract_click_coords(response)  # your parsing logic
screen_x, screen_y = scale_coordinates(api_x, api_y, display_w, display_h, native_w, native_h)
```

# **为计算机使用调校思维努力**

Claude 的最新模型支持[适应性思维](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking)，这项设置让 Claude 能够决定在行动之前通过中间步骤进行多少推理。适应性思维无需手动设置思维令牌预算，而是让 Claude 根据每个请求的复杂度，动态决定何时、以及使用多少扩展思维。对于计算机使用而言，这意味着 Claude 可以思考它在屏幕上看到的内容、规划多步交互，并在点击或按键之前自我纠正。

通过适应性思维，Claude 的思维深度由 thinking 参数通过一个工作量级别来控制：low、medium、high、xhigh（仅 Opus 4.7）和 max。更多的思考意味着每个动作有更多的推理，但也意味着更多的输出令牌、更高的延迟和更高的成本。

一个自然的问题是：取决于模型的不同，多少思考对计算机使用是最优的？

## **Claude Opus 4.7**

我们在一套涵盖桌面应用、浏览器和多应用工作流的端到端 UI 自动化任务上，测试了每一个思维努力级别。

![](images/79b14b830008-6a0240d5a273c79dddb95eb5-image1.png)

**Opus 4.7 优于 4.6 系列。** 在 OSWorld Verified 基准上，我们发现 Opus 在相同令牌用量和工作量级别下，优于所有 4.6 系列模型。Opus 4.7 在 low 努力下的得分与 Sonnet 4.6 在 max 下大致相当，而每个任务使用的令牌大约只有后者的 1/10。对于困难任务，Opus 4.7 是显而易见的选择。

**把努力级别设为 `high`**，能以大约一半于 `max` 的输出令牌达到接近最高的任务成功率。与 Opus 4.6 相比，low、medium 和 high 使用的令牌数量大致相同，同时提升了 OSWorld 上的得分。在我们的内部测试中，max 努力使用了更多令牌并给出了最佳分数。下表概述了我们关于何时使用各个思维努力级别的建议。

### **工作量级别建议**

| 场景 | 思考努力 | 为什么 |
| --- | --- | --- |
| 大多数用例的默认设置 | `high` | Opus 4.7 最擅长困难任务。使用 high 能为模型提供足够的推理来规划复杂的多步交互，而不会显著增加令牌用量。 |
| 高吞吐 / 成本敏感 | `low` | 更低的令牌用量，同时提供介于 Opus 4.6 的 high 与 max 努力设置之间的质量。 |
| 简单、定义明确的工作流 / 最快 | 建议尝试 Sonnet 4.6 | 如果低延迟是最高优先级则使用。适用于 UI 一致、工作流已知的短小、可预测任务。 |
| 复杂的、一次性任务 | `max` | 当任务极具挑战性，且你需要一次就做对时使用。 |

## **Claude 4.6 模型**

我们在一套涵盖桌面应用、浏览器和多应用工作流的端到端 UI 自动化任务上，测试了每一个思维努力级别。

![](images/a6900e74b7dc-6a024267c961b1b1c42684fc-image2.png)

有两种模式非常突出：

**medium 努力是最佳甜点。** 把努力级别设为 medium，能在使用大约一半于 high 的输出令牌的同时，达到接近最高的任务成功率。超过 medium 之后，性能会有所趋平。值得注意的是，当任务被重试时，medium 和 high 会收敛到相同的成功率。这意味着 high 努力可能帮助模型在第一次尝试时就做对困难任务，但给定多次尝试，medium 可能以更低的成本可靠地完成。

**一点点思考能带来很大帮助。** low 努力是一个出人意料地强劲的选项。它实际使用的*总*输出令牌比完全禁用思考还要*少*（模型犯错更少、需要的重试周期更少），同时匹配或略超无思考的准确性。这使它成为成本敏感、高吞吐工作负载的最佳选项。下表概述了我们的努力建议。

### **工作量级别建议**

| 场景 | 思考努力 | 为什么 |
| --- | --- | --- |
| 大多数用例的默认设置 | `medium` | 最佳的准确性—成本比。为模型提供足够的推理来规划多步交互，而不会过度思考。配合重试，能以一半的令牌成本达到 high 的性能。 |
| 高吞吐 / 成本敏感 | `low` | 比不思考更准确，且由于错误和重试更少，令牌用量更低。 |
| 简单、定义明确的工作流 / 最快 | 禁用思考 | 如果低延迟是最高优先级则使用。适用于 UI 一致、工作流已知的短小、可预测任务。 |
| 复杂的、一次性任务 | `high` | 当任务具有挑战性，且你需要一次就做对时使用。如果你的系统支持重试，medium 可能达到相同的最终成功率。 |

我们不推荐在计算机使用中使用 `max` 努力。在我们的测试中，它相比 `high` 没有提供准确性上的收益，却进一步增加了输出令牌成本。UI 任务主要是感知性的，而非深度逻辑性的，额外的推理预算要么用不上，要么导致过度思考。请记住，随着模型演进，这一建议也会变化。

## **中等工作量级别的示例配置**

```python
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16000,
    betas=["computer-use-2025-11-24"],
    thinking={"type": "adaptive"},
    output_config={"effort": "medium"},
    messages=[...],
    tools=[
        {
            "type": "computer_20251124",
            "name": "computer",
            "display_width_px": 1280,
            "display_height_px": 720,
        }
    ],
)
```

## **为什么更多的思考并不总是有帮助**

UI 自动化任务与编码或数学问题有着根本不同。大多数计算机使用行为都是感知性和机械性的：识别正确的元素、点击正确的位置，而非深度逻辑性的。思考在以下情况最有用：

- 在开始之前规划一个多步序列（例如，“我需要打开‘设置’，进入‘隐私’，然后关闭追踪”）
- 从意外的 UI 状态中恢复（例如，出现了一个未预料到的对话框）
- 将屏幕内容与任务指令进行交叉比对
- 用专业软件完成有挑战性的项目

# **提升安全性：利用提示词注入分类器**

*本节介绍提示词注入防护，如果你使用我们官方的计算机使用工具标头，该防护默认免费提供。不过，如果你有兴趣在自己的自定义计算机或浏览器使用工具上启用它，请填写我们的* [*提示词注入分类器意向表。*](https://docs.google.com/forms/d/e/1FAIpQLSfXj6rXC-SUQEYHCLabwUe5JuYiYyJ29Ja-KP7EhLIPlyz0tw/viewform?usp=dialog)

计算机使用智能体在设计上就会与不受信任的内容打交道。Claude 处理的每一张截图、网页或应用 UI，都可能包含对抗性指令，包括隐藏文本、被篡改的图像、欺骗性 UI 元素，或试图劫持智能体行为的社会工程尝试。这一攻击面与你控制输入的典型 API 集成有根本不同。在使用计算机时，模型的输入是开放的互联网以及智能体正在导航的任何软件。

随着计算机使用智能体变得更强、部署更广，提示词注入也变成了相应更严重的风险。一个能够点击、输入和导航的智能体，可能被操纵去执行真实世界的动作，例如填写表单、下载文件或导航到恶意 URL。针对这些攻击建立稳健的防御，对任何生产部署都至关重要。

## **我们如何应对提示词注入防御**

我们已经详细写过我们针对浏览器和计算机使用的[提示词注入防御方法](https://www.anthropic.com/research/prompt-injection-defenses)。我们的防御策略在多个层面运作：

**训练时的鲁棒性。** 我们使用强化学习，把提示词注入抵抗力直接构建进 Claude 的能力中。在训练过程中，Claude 会接触到嵌入在模拟网页和应用 UI 中的注入内容，并在正确识别并拒绝遵循恶意指令时获得奖励。这意味着 Claude 的第一道防线就是模型本身，因为它已经学会区分合法的用户指令与任务执行过程中遇到的对抗性内容。

**实时分类器。** 我们运行探针，扫描进入 Claude 上下文窗口的内容，并标记潜在的提示词注入尝试。这些探针能够检测多种形态的对抗性指令，例如隐藏在页面内容中的文本、嵌入图像中的指令，以及为欺骗智能体而设计的欺骗性 UI 元素，并在识别出攻击时调整 Claude 的行为。

**持续红队。** 我们的安全研究人员持续探查这些防御，并参与外部对抗性评估，以衡量面对不断演进的攻击技术时的鲁棒性。

自最初的计算机使用研究预览以来，我们持续在所有三个层面大量投入。每一代新模型都包含更强的训练时防御和更强大的分类器，并且我们扩大了红队评估所覆盖的攻击技术范围。

## **使用 Claude 的内置分类器**

当你通过 API 使用 Claude 的[官方计算机使用工具](https://docs.anthropic.com/en/docs/agents-and-tools/computer-use)时，提示词注入分类器会在每个请求上自动运行。这些分类器与主模型推理并行运行，增加的额外延迟几乎为零，也不会给你的请求带来额外成本。

你无需做任何配置即可启用这项防护。当你使用官方的 `computer_20251124` 工具类型时，它默认开启。分类器会评估截图及其他内容中是否存在提示词注入的迹象，并相应地影响 Claude 的响应。

```python
# 使用官方 CU 工具时分类器自动运行 —— 无需额外配置
tools = [
    {
        "type": "computer_20251124",
        "name": "computer",
        "display_width_px": 1280,
        "display_height_px": 720,
    }
]
```

## **如果你没有使用官方的计算机使用工具**

许多开发者使用自定义工具定义、而非官方的 `computer_20251124` 工具类型来构建计算机使用集成，例如定义自己的截图和点击工具。如果这描述的是你的设置，那么上述内置分类器目前不会在你的请求上运行。

我们正在积极探索如何把提示词注入防护扩展到这些自定义实现。如果你正在构建不使用官方工具类型的计算机使用或浏览器使用集成，并且对提示词注入分类器感兴趣，请[填写此意向表](https://docs.google.com/forms/d/e/1FAIpQLSfXj6rXC-SUQEYHCLabwUe5JuYiYyJ29Ja-KP7EhLIPlyz0tw/viewform?usp=dialog)，我们会在该功能可用时与你跟进。

## **无论是否使用分类器都适用的最佳实践**

分类器只是一层防御，而非完整的解决方案。我们建议对任何计算机使用部署采取以下做法：

**对高风险动作实施人机协同（human-in-the-loop）。** 在执行不可逆操作（例如提交表单、购买、发送消息或修改数据）之前，让智能体暂停并请求用户确认。无论分类器表现如何，这都是针对提示词注入最有效的缓解措施。

**划定智能体的权限范围。** 限制智能体能做什么。如果你的工作流不需要文件下载，就不要赋予智能体下载文件的权限。如果它不需要发送邮件，就不要给它访问邮件客户端的权限。缩小一次成功注入的爆炸半径，与防止注入本身同等重要。

**监控并记录智能体的操作。** 记录智能体执行的完整操作序列，包括每一步的截图。这让你能够检测异常行为，在出错时审计发生了什么，并建立反馈循环，随着时间推移提升系统的鲁棒性。

**将所有网络内容视为不可信。** 设计你的智能体系统提示词，以清晰区分用户的指令与任务执行过程中遇到的内容。提醒模型，在网页、邮件或应用 UI 中找到的文本并非来自用户，也不应被视为指令。

# **计算机使用的上下文管理**

在构建计算机使用智能体时，截图积累得很快。每个动作都会生成一张新图像，而每张图像会消耗大约 1,000–1,800 个令牌，具体取决于分辨率。在扣除系统提示词、工具定义和文本内容之后，一个 200k 的上下文窗口在不到 100 张截图内就可能被填满。

良好地管理这一上下文有两个目标：1）保持令牌总数有界；2）保持提示词缓存有效，这样你就不必为同一前缀反复支付全价。我们发现，有效的[上下文管理](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) 对长时间运行智能体的成本和延迟的影响，超过几乎任何其他优化。本节涵盖三层能干净组合的实践：放置缓存断点、在不破坏缓存的前提下裁剪旧截图，以及在裁剪不够时总结历史。

## **放置缓存断点**

只有当断点落在会跨回合复现的内容上时，提示词缓存才有帮助。API 总共支持四个缓存断点。把四个断点都放在一个稳定的前缀上（系统提示词、工具定义）是在浪费它们，因为该前缀已经被命中过一次且永远不会失效，所以一个断点就足够了。另外三个最好花在最近的历史上，那里失效风险最高，而且节省的费用会随长会话不断累积。

我们建议：

- **在系统提示词或尾部工具定义上放一个断点。** 这一前缀在会话中很少变化。
- **在最近的工具结果上最多再放三个断点**，每个回合推进一次，并清除上一轮迭代的断点，以免超出四个断点的上限。

把断点分布在较近的位置，可以让你实现优雅降级。如果你最近的断点失效了（例如由于图像裁剪、压缩或工具定义变更），较早的断点仍然可能命中，而你只需支付全额输入成本的 10%，而非 100%。

*缓存控制与设置断点的示例：*

```python
def set_trailing_cache_control(messages, max_breakpoints=3):
    """Place up to `max_breakpoints` ephemeral cache_control markers on the
    most recent tool_result blocks, after clearing any existing markers."""
    for msg in messages:
        for block in msg.get("content", []):
            if isinstance(block, dict):
                block.pop("cache_control", None)

    placed = 0
    for msg in reversed(messages):
        for block in reversed(msg.get("content", [])):
            if placed >= max_breakpoints:
                return
            if isinstance(block, dict) and block.get("type") == "tool_result":
                block["cache_control"] = {"type": "ephemeral"}
                placed += 1
```

## **方法 1：滚动缓冲区（感知缓存）**

限制令牌数量最简单的方法，是只保留最近 N 张截图，丢弃其余部分。在每次 API 调用之前，遍历消息数组，用短的占位符（例如一个写着“[Image omitted]”的文本块）替换较早的图像块。

这种模式的朴素版本是：随着截图变旧，一次丢弃一张，这会在每个回合都改变前缀，从而持续使提示词缓存失效。这正是滚动缓冲区“破坏缓存”名声的由来。修复方法是批量裁剪，让前缀在连续若干回合内保持逐字节相同，然后失效一次，再重新保持稳定。

我们测试过的一个具体模式是：

1. 以全分辨率保留最近的 keep_n 张截图。
2. 一旦截图总数超过 keep_n + interval，就在一次遍历中用占位符替换最早的 interval 张截图。
3. 在裁剪事件之间，消息数组在各回合间逐字节相同，因此你的缓存断点会持续命中。

合理的起始默认值是：keep_n = 3，interval = 25。这些是可调的，更大的 interval 意味着更少的裁剪事件（更好的缓存效率），但上下文中全分辨率截图的尾部也更大（更多令牌）。请在一个有代表性的轨迹上测量缓存命中率和总输入令牌，再进行调整。

*在保留缓存断点的同时裁剪旧截图的示例：*

```python
def prune_old_screenshots(messages, keep_n=3, interval=25):
    """Replace older screenshots with text placeholders in batches.
    Only prunes when the total count exceeds keep_n + interval, so the
    message prefix stays byte-stable for `interval` turns between prunes."""
    image_positions = [
        (msg_idx, block_idx)
        for msg_idx, msg in enumerate(messages)
        for block_idx, block in enumerate(msg.get("content", []))
        if isinstance(block, dict) and block.get("type") == "image"
    ]
    if len(image_positions) <= keep_n + interval:
        return messages

    to_prune = image_positions[:-keep_n][-interval:]
    for msg_idx, block_idx in to_prune:
        messages[msg_idx]["content"][block_idx] = {
            "type": "text",
            "text": "[Image omitted]",
        }
    return messages
```

滚动缓冲区仍有一个真正的局限：缓冲区之外的任何东西都会消失。原始指令、智能体已经尝试过的内容，以及它在任务中的位置，都会随着被裁剪的截图一起消失。对于短期任务（大约 50 个动作以内），这没关系。对于更长的任务，请把它与压缩结合起来。

## **方法 2：基于 LLM 的压缩**

与其悄悄丢弃旧图像，不如在丢弃之前总结完整的对话。总结保留了发生了什么、用户要求了什么、已完成的内容，以及从哪里继续。会保留几张最近的截图在它旁边，这样智能体就能看到它当前正在看的内容。

压缩与感知缓存的滚动缓冲区是互补的。逐回合使用滚动缓冲区来让令牌增长可控；偶尔使用压缩来回收窗口的其余部分，而不丢失早期的上下文。每次压缩事件在设计上都是一次缓存失效，因此你希望它很少发生，而不是每隔几回合就发生一次。

### **总结提示词**

这个示例提示词提供了一个框架，其中每个部分针对一种特定的失败模式。该提示词必须捕获智能体在不重新阅读原始对话的情况下继续任务所需的一切，如下例所示：

```python
COMPACT_PROMPT = """Your task is to create a detailed summary of this conversation that
will REPLACE the conversation history. The agent will continue working with only this
summary and a few recent screenshots as context.

CRITICAL: Preserve ALL user instructions verbatim. User instructions are the most
critical element. If they are lost, the agent will deviate from the task.

Before providing your summary, analyze the conversation in  tags:
1. Extract every user instruction, requirement, and constraint
2. Identify if this is a repeatable workflow (e.g., processing N items)
3. Chronologically trace what actions were taken and what happened

Your summary MUST include these sections:

1. USER INSTRUCTIONS:
   - Complete initial task definition (verbatim when possible)
   - ALL specific requirements and criteria
   - Every "DO NOT", "ALWAYS", "MUST" instruction
   - Any corrections or feedback that changed the approach

2. TASK TEMPLATE (if this is a repeatable workflow):
   - The pattern being repeated
   - Decision criteria for each iteration
   - Standard workflow steps
   - Example of one completed iteration

3. CONSTRAINTS AND RULES:
   - All user-specified rules and restrictions
   - Edge cases and exceptions discovered

4. ACTIONS TAKEN:
   - Pages visited and elements interacted with
   - Forms filled and buttons clicked

5. ERRORS AND FIXES:
   - What went wrong and how it was resolved
   - Approaches that failed (so they aren't retried)

6. PROGRESS TRACKING:
   - Items completed vs. remaining
   - Current position in the workflow

7. CURRENT STATE:
   - Current application, URL and domain (optional)
   - Important page state (logged in, form progress, etc.)

8. NEXT STEP:
   - Exactly what should be done next to continue
"""
```

在上述提示词中，**用户指令**防止任务漂移：没有它，智能体在压缩后会偏离方向。**任务模板**捕获可重复的模式，使智能体在压缩后能继续迭代，而无需从头重新推导工作流。**约束与规则**保留任务之前设定或期间发现的限制与边界情况，这样智能体就不会违反它本应遵守的既有规则。**已采取的行动**帮助跟踪过去的进度。**错误与修复**防止重试失败的方法（“我已经试过点击‘提交’了；在勾选‘条款’复选框之前它都不管用”）。**进度跟踪**防止重新开始或跳过项目。**当前状态**与**下一步**给出了一个明确的恢复入口点。

### **服务端压缩（测试版）**

使用这个提示词最简单的方式，是让 API 通过[服务端压缩](https://docs.anthropic.com/en/docs/build-with-claude/compaction)（测试版）来处理压缩。把你的自定义总结提示词作为 `context_management` 中的 `instructions` 参数传入，当输入令牌超过触发阈值时，API 会自动进行总结。`instructions` 参数会完全替换默认的总结提示词，因此上面这些部分就是模型将遵循的内容。设置 `pause_after_compaction` 以在压缩事件之间附加最近的消息（包括截图）。

*使用自动压缩工具的示例：*

```python
# 最小化 —— 用 API 默认值开启 autocompaction
response = client.beta.messages.create(
    model="claude-opus-4-7",
    max_tokens=16000,
    betas=["compact-2026-01-12", "computer-use-2025-11-24"],
    context_management={"edits": [{"type": "compact_20260112"}]},
    messages=[...],
    tools=[...],
)

# 自定义 —— 设置你自己的触发阈值与总结提示词
response = client.beta.messages.create(
    model="claude-opus-4-7",
    max_tokens=16000,
    betas=["compact-2026-01-12", "computer-use-2025-11-24"],
    context_management={
        "edits": [
            {
                "type": "compact_20260112",
                "trigger": {"type": "input_tokens", "value": 150_000},
                "instructions": COMPACT_PROMPT,
            }
        ]
    },
    messages=[...],
    tools=[...],
)
```

### **在客户端截断以匹配服务端**

当 API 运行服务端压缩时，它会在自己这一侧替换压缩前的内容，但你的本地消息数组仍然保留着完整的历史。如果你在后续每个回合继续发送完整历史，你将为服务器不再需要的令牌付费，而且你的滚动缓冲区裁剪器会在一个与服务端实际所见不同的消息切片上运行，这可能破坏你上面精心维护的缓存稳定前缀。

修复方法是在客户端镜像服务端的截断，如下面的代码片段所示。当响应报告发生了压缩时，在下一回合之前，从本地消息数组中删除压缩标记之前的所有内容。这使客户端与服务端的视图保持一致，并让滚动缓冲区能继续正常工作。

```python
def truncate_to_last_compaction(messages, response):
    """If the server compacted on this turn, drop pre-compaction messages
    locally so the next turn's cache prefix matches what the server sees."""
    context_mgmt = getattr(response, "context_management", None)
    if not context_mgmt or not context_mgmt.get("applied_edits"):
        return messages

    compaction = next(
        (e for e in context_mgmt["applied_edits"] if e["type"] == "compact"),
        None,
    )
    if compaction is None:
        return messages

    keep_from = compaction["message_index_after_compaction"]
    return messages[keep_from:]
```

## **客户端压缩**

如果你使用的模型不支持服务端压缩，或者你想要完全的控制，请用同一个提示词在客户端实现压缩。每次 API 调用之后，检查响应 usage 字段中的总输入令牌数。当超过某个阈值（例如上下文窗口的 90%）时，把对话发送给一个总结器模型，以 COMPACT_PROMPT 作为系统提示词。用总结加上几张最近的截图替换消息历史，然后继续智能体循环。

## **把它们放在一起**

对于一个长时间运行的计算机使用智能体，良好的默认值如下所示：

- 在稳定前缀上放一个缓存断点，在尾部工具结果上放三个缓存断点，每个回合清除并重新放置。
- 感知缓存的滚动缓冲区，keep_n = 3，interval = 25，用占位符批量替换旧截图。
- 服务端压缩在大约 150k 输入令牌处触发，配合自定义提示词，外加一次客户端截断传递以保持两端视图对齐。

有了这三层，一个典型的长程 CU 会话会在绝大多数回合上命中提示词缓存，将总输入令牌控制在远低于上下文窗口的水平，并通过压缩事件保留足够的历史，使智能体不会丢失任务跟踪。

# **改善计算机和浏览器使用的实验性设置**

下面的模式是我们在实现中测试过、显示出前景、但尚不构成普适性建议的技术。每一种都会以复杂性或成本为代价，换取特定类型工作负载的潜在提升。我们把它们放在这里，以便你能在自己的工作流中尝试，但请注意，本节中的指导可能会快速演进。

## **批处理工具**

在更新后的参考实现中，我们在标准计算机和浏览器工具之外，还暴露了两个工具：`computer_batch` 和 `browser_batch`。每个工具都接受一份子操作列表，并在单次工具调用中执行它们。例如，模型可以发出一个包含全部三个操作的 computer_batch 调用，而不是单独的点击、输入和按键操作。

吸引力在于效率：一个包含 N 个机械动作的工作流是单次往返，而非 N 次往返，这在长程任务中有意义地减少了挂钟时间以及输出令牌支出。风险则是错误的复合：如果操作 2 依赖于操作 1 改变的视觉状态，而操作 1 没命中，那么批次的其余部分就会基于过时的假设运行，智能体可能在没有看到真实状态截图的情况下发生漂移。

当子操作相互独立、且不依赖于彼此的视觉结果时（填写表单中的多个字段、串联键盘快捷键、滚动并点击已知目标），我们推荐使用批处理工具。在探索性导航、错误恢复序列，或任何“如果操作 1 失败，我需要重新规划”为真实状态的工作流中，我们会避免使用它们。

由于批处理工具是你自己的自定义定义，它们可以与标准计算机或浏览器工具干净地叠加。两者都保留可用，让模型自己选择。

## **顾问工具（测试版）**

[顾问工具](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool) 将一个执行器模型与一个智能更高的顾问模型配对，执行器可以在生成过程中就战略指引咨询顾问。执行器运行循环，当它遇到需要更深推理的东西时，就调用顾问，接收一份计划或路线修正，然后继续。这发生在服务端、单个请求内部，你的这一侧无需额外的往返。

特别是对于计算机使用，这种模式在长程任务中最有用——其中大多数回合都是机械性点击，但偶尔的规划时刻（选择打开哪个标签页、从意外弹窗中恢复、决定是否放弃某个策略）能从 Opus 级别的推理中受益。当大部分令牌生成以执行器速率发生时，你能获得接近“仅用顾问”的质量。

*启用顾问工具的示例：*

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16000,
    betas=["advisor-tool-2026-03-01", "computer-use-2025-11-24"],
    tools=[
        {
            "type": "advisor_20260301",
            "name": "advisor",
            "model": "claude-opus-4-7",
        },
        {
            "type": "computer_20251124",
            "name": "computer",
            "display_width_px": 1280,
            "display_height_px": 720,
        },
    ],
    messages=[...],
)
```

顾问工具有用的控制项包括：

- **`max_uses`**：按请求上限顾问调用次数。当你想约束最坏情况的成本时很有帮助。
- **线束中的全对话上限**：顾问每次咨询都按 Opus 4.7 的费率计费，因此在很长的会话中，你可能想在使用一定次数后停止提供顾问。
- **顾问侧缓存**：在多调用对话中，缓存顾问的前缀大约在三次咨询之后就开始回本。在参考实现中，我们默认使用 5 分钟的临时缓存。

有两件不明显的事情值得了解：顾问在没有工具、也没有上下文管理的情况下运行，因此它无法代表你点击或浏览，它只返回文本建议。并且由于执行器模型并不总记得顾问存在于长程任务中，请参阅下面的提醒轻推部分。

## **清理孤立的顾问块**

当顾问工具被触发时，执行器会发出一个 `server_tool_use` 块，其名称为“advisor”，随后跟着一个 `advisor_tool_result` 块，出现在返回的内容中。这些块与其他所有内容一起存在于你的消息数组中。

如果你之后从工具数组中删除了顾问工具——因为你达到了会话范围上限、更改了配置或切换了模型——那些先前的 `server_tool_use` / `advisor_tool_result` 块就变成了孤儿块。API 会在下一个请求时返回 400，因为它所引用的工具已不再被声明。

修复方法是一个简单的发送前处理：每当顾问在某回合被禁用时，遍历消息历史，并删除任何类型为 `server_tool_use`（名称 == “advisor”）和 `advisor_tool_result` 的内容块。

*删除过时顾问块的示例：*

```python
def strip_orphaned_advisor_blocks(messages):
    """Remove advisor server_tool_use / tool_result blocks from history.
    Call this before any request that doesn't include the advisor tool."""
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        msg["content"] = [
            block for block in content
            if not (
                isinstance(block, dict)
                and (
                    (block.get("type") == "server_tool_use"
                     and block.get("name") == "advisor")
                    or block.get("type") == "advisor_tool_result"
                )
            )
        ]
    return messages
```

## **周期性的提醒轻推**

在长会话中，执行器模型可能会忘记哪些工具可用、或应该优先使用哪些工具。在我们的测试中，两种简短的提醒模式有所帮助：

**批处理提醒。** 如果你在标准形式工具之外还暴露了 `computer_batch` 或 `browser_batch`，并且观察到模型在本适合批处理的场合仍然串联单操作调用，可在下一条工具结果之后附加一条简短的系统级轻推：“记住，当连续操作不依赖于中间截图时，你可以用 `computer_batch` 把它们合并到一次工具调用中。”目标是把模型拉回到批处理上，而不指定确切的时机。

**顾问提醒。** 执行器很容易忘记顾问工具的存在，尤其是在多回合没有调用它的情况下。在超过约 20 回合且没有顾问调用的会话中，附加一条简短提醒，说明顾问可用于规划或路线修正。在参考实现中，我们使用 20 回合的节奏，并附加一行提示。

这两种轻推都是轻量的上下文注入，而非系统提示词重写。每次附加会花费几十个输入令牌。如果你的系统提示词已经很长，或者你的缓存断点已精确放置，请权衡提升是否值得增加失效风险。

## **参考实现中的调试模式**

当出现问题、而你不确定是线束、截图还是模型的问题时，在开始添加日志之前，不妨使用参考实现中的三个辅助工具：

- **轨迹查看器（streamlit run viewer/app.py）**。加载记录的轨迹，让你逐步查看智能体的回合，并查看截图、思维、工具调用以及每一步的使用情况。最适合在运行失败后回答“模型实际看到了什么，它决定了什么？”。
- **工具调试面板（uvicorn debug.server:app --reload）**。一个小型 Web UI，让你可以单独使用每个工具：截取截图、捕获点击坐标、输入、滚动、缩放。对于确认你的捕获管道和坐标缩放确实产生了你所期望的结果非常有用。
- **本地化游乐场（uvicorn localize.server:app --reload --port 8001）**。上传任意图像，让模型指向目标。在显示分辨率和原始分辨率下，把预测坐标渲染回图像上。这是诊断点击失误究竟是缩放错误、坐标缩放错误，还是真正的模型错误的最快方法。当客户报告不良点击、而你又想单独复现故障时，这尤其有用。

这些都不是构建有效集成所必需的；它们是调试辅助工具，用于默认反馈循环（记录、重跑、眯眼看记录）不够快的时候。

## **提升可靠性：教 Claude**

你不必反复迭代文本提示词直到 Claude 做对某个工作流，而是可以直接向它展示正确的行为。记录你自己执行任务的过程，捕获每一步的截图、操作，以及可选的语音旁白，然后在 Claude 执行相同工作流时，把这段演示作为上下文回放。录音会变成一份 Claude 可以遵循的可复用规范，并能适应实时 UI 状态的差异。

我们在 Chrome 中的 Claude（我们称之为“教学模式”）里内部使用这种模式，并在此分享，因为底层方法对构建计算机使用或浏览器使用产品的任何人来说都广泛适用。它在两方面有帮助：提升 Claude 大体能处理、但偶尔会出错的工作流的可靠性，以及解锁 Claude 仅凭文本提示词无法完成的全新工作流。核心思路（捕获一次演示，把它作为上下文反馈回去）易于实现，并且能很好地适配浏览器和桌面环境。

### **核心理念：展示，而非讲述**

传统的提示词工程要求用户用文字描述他们想要的内容，然后在 AI 误解时进行迭代。这种模式将其反转：用户演示任务，而系统记录他们的操作、截图和（可选的）语音旁白。在回放期间，Claude 接收完整的演示作为上下文，并遵循相同的步骤顺序，适应当前 UI 状态的任何差异。

关键的洞见在于，回放并不是严格的重播。Claude 以演示为指导，同时对实时环境进行推理。如果按钮移动了或菜单被重组了，Claude 可以在当前 UI 中找到等效的元素，而不是盲目点击记录下来的坐标。

### **数据模型**

基本单位是“工作流步骤”（workflow step），即录制期间捕获的单次动作。每个步骤都打包了做了什么、发生在哪里，以及屏幕当时的样子：

```python
from dataclasses import dataclass, field
from typing import Literal, Optional

@dataclass
class WorkflowStep:
    action: Literal["click", "type", "navigate", "scroll", "select"]
    description: str                         # Human-readable, e.g. "Click the Submit button"
    timestamp: float
    selector: Optional[str] = None           # CSS selector or XPath
    coordinates: Optional[dict] = None       # {"x": int, "y": int}
    url: Optional[str] = None
    screenshot: Optional[str] = None         # Base64-encoded screenshot
    viewport_dimensions: Optional[dict] = None  # {"width": int, "height": int}
    speech_transcript: Optional[str] = None  # Voice narration, if captured
    value: Optional[str] = None              # For type actions

@dataclass
class SavedWorkflow:
    id: str
    name: str                                # e.g. "Submit expense report"
    steps: list[WorkflowStep] = field(default_factory=list)
    description: Optional[str] = None        # AI-generated summary of the workflow
    start_url: Optional[str] = None
    created_at: float = 0.0
    usage_count: int = 0
```

同时捕获选择器和坐标是有意为之的：选择器对布局变化更鲁棒，而坐标在选择器失效时提供了一个 Claude 可用的视觉后备。存储视口尺寸，以便在回放环境与录制环境不同时能够缩放坐标。

### **录制：捕获什么**

至少，要捕获点击事件、键盘输入、导航变更，以及每次操作的截图。对于每次点击，生成一段人类可读的描述（来自 aria-labels、文本内容，或通过一次快速的 Claude 调用），并用视觉标记在点击位置对截图进行标注：

```python
def on_click(event):
    step = WorkflowStep(
        action="click",
        selector=generate_selector(event.target),
        coordinates={"x": event.client_x, "y": event.client_y},
        url=current_url(),
        description=generate_description(event.target),
        timestamp=now(),
        viewport_dimensions=get_viewport_size(),
    )
    # Annotate screenshot with a circle at the click position
    screenshot = capture_screenshot()
    step.screenshot = annotate_with_circle(screenshot, event.client_x, event.client_y)
    workflow_steps.append(step)
```

标注（点击位置的彩色圆圈）有两个用途：帮助用户验证录制捕获了正确的元素，并在回放期间准确显示 Claude 操作发生的位置。你的回放提示词应澄清，这些标记是录制产物，而非实时 UI 的一部分。

### **回放：构建提示词**

这是最重要的一块。当用户触发一个已保存的工作流时，你要构建一条发给 Claude 的消息，其中包含三样东西：用户的意图、解释演示格式的上下文块，以及录制下来的截图。

上下文块告诉 Claude 如何解读带标注的截图，以及当实时 UI 不同时如何调整：

```python
def generate_playback_context(steps: list[WorkflowStep]) -> str:
    steps_description = "\n".join(
        f"Step {i+1}: {step.description}"
        for i, step in enumerate(steps)
    )

    return f"""<demonstration_context>
The user has recorded a demonstration showing how to perform this task.

RECORDED STEPS:
{steps_description}

ABOUT THE SCREENSHOTS:
- Each screenshot shows the screen state when an action was taken
- BLUE CIRCLES mark where the user clicked — these are recording annotations
- The blue highlighting is NOT part of the actual interface
- Your own screenshots will NOT have these markers

HOW TO USE THIS DEMONSTRATION:
1. Review all steps and screenshots to understand the complete workflow
2. Take your own screenshot to see the CURRENT page state
3. The blue highlights show which element to interact with — find it in your current view
4. Follow the same sequence of actions, adapting to any differences
5. If the UI has changed significantly, use judgment to find equivalent elements
</demonstration_context>"""
```

然后把完整的消息与用户的提示词、上下文块，以及每个步骤的截图（作为图像）组装在一起：

```python
import anthropic

client = anthropic.Anthropic()

content = [
    {"type": "text", "text": user_prompt},
    {"type": "text", "text": generate_playback_context(workflow.steps)},
]

for i, step in enumerate(workflow.steps):
    if step.screenshot:
        content.append({"type": "text", "text": f"[Step {i+1}: {step.description}]"})
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": step.screenshot},
        })

response = client.beta.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    betas=["computer-use-2025-11-24"],
    messages=[{"role": "user", "content": content}],
    tools=[{
        "type": "computer_20251124",
        "name": "computer",
        "display_width_px": 1280,
        "display_height_px": 720,
    }],
)
```

### **回放模式**

并非每个工作流都需要同等程度地遵循录制的演示。有些工作流太长，会消耗大量输入令牌，最终拖慢延迟、增加成本。请考虑在上下文提示词中支持一个严格度（strictness）参数：

**严格（Strict）：** 严格遵循步骤；如果 UI 变化太大，就停止并报告。适用于对合规性敏感、确切顺序至关重要的工作流。

**自适应（Adaptive）：** 把演示作为指导，但适应 UI 变化。这是大多数用例的最佳默认——它能从容应对较小的布局变动、更新的按钮标签和重组的菜单。

**目标导向（Goal-oriented）：** 关注最终结果；把录制的步骤当作提示而非指令。当 UI 频繁变化但目标保持不变时非常有用。用模型总结录制的演示（使用与下一节所述策略类似的策略），然后把那份总结传给 CU 模型。

### **示例：端到端费用报销工作流**

以下是一个已保存工作流在实践中的样子。该工作流包含五个步骤：导航到费用表单、选择费用类型、从下拉列表中选择“差旅”、输入金额，然后点击“提交”。

```python
expense_workflow = SavedWorkflow(
    id="wf_abc123",
    name="Submit Expense Report",
    start_url="https://expenses.company.com/new",
    steps=[
        WorkflowStep(
            action="navigate",
            url="https://expenses.company.com/new",
            description="Navigate to new expense form",
            timestamp=1700000000,
        ),
        WorkflowStep(
            action="click",
            selector="#expense-type-dropdown",
            coordinates={"x": 400, "y": 200},
            description="Click on expense type dropdown",
            timestamp=1700000001,
        ),
        WorkflowStep(
            action="click",
            selector="[data-value='travel']",
            coordinates={"x": 400, "y": 280},
            description='Select "Travel" expense type',
            timestamp=1700000002,
        ),
        WorkflowStep(
            action="type",
            selector="#amount-input",
            value="150.00",
            description="Enter expense amount",
            timestamp=1700000003,
        ),
        WorkflowStep(
            action="click",
            selector="#submit-expense-btn",
            coordinates={"x": 1150, "y": 420},
            description="Click the Submit button",
            speech_transcript="Now I'll click submit to send the report for approval",
            timestamp=1700000004,
        ),
    ],
)
```

当用户稍后说“提交我们团队午餐的费用报销（85.50 美元）”时，回放服务会构建一条提示词，包含演示上下文、全部五张带标注的截图，以及新请求中的具体数值。Claude 能准确看到点击位置、遵循的顺序，并调整金额和描述以匹配当前任务。如果你的工作流因为输入令牌数量而太长、不实用，那么在把它用作示例之前，请考虑先对工作流程进行压缩。有关管理上下文的提示，请参阅下一节。

# **开始使用计算机和浏览器**

这些实践反映了我们当前对如何让计算机使用集成在生产中可靠的最佳理解。它们适用于 Claude 4.6 模型系列和 Opus 4.7，并将随着新模型与新技术出现而更新。

随着集成的成熟，最重要的模式将取决于你的特定环境、目标应用和可靠性要求。

*开始使用*[计算机使用文档](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)*，查看我们关于这些最佳实践的*[新演示实现](https://github.com/anthropics/claude-quickstarts/tree/main/computer-use-best-practices)*，或重温* [原始计算机使用研究文章](https://www.anthropic.com/news/developing-computer-use)*，了解这些能力是如何构建的，以及它们将走向何方。*

*致谢：本文及相应的演示由 Lucas Gonzalez 和 Luca Weihs 撰写。作者感谢 Molly Vorwerck、Javier Rando、Maya Nielan、Gabe Mulley 和 Brigit Brown 的贡献。*
