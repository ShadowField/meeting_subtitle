---
description: 退出前把本次对话里值得长期保留的信息提炼进 memory
---

用户即将退出当前对话。请回顾本次对话的全部内容，把值得跨会话保留的信息写入 memory 系统（`/Users/tenghu/.claude/projects/-Users-tenghu-Desktop-code-meeting-subtitle/memory/`）。

注意：Claude Code 会自动保存完整 transcript，用 `claude -c` 就能恢复。所以这个命令**不是**再存一份对话，而是把"长期有用、从代码/git 里推不出来"的信息沉淀下来。

## 执行步骤

1. **先读** `MEMORY.md` 和现有 memory 文件，避免写重复或过时内容。

2. **扫描本次对话**，按 memory 的四种类型分别筛选：
   - **user**：用户的角色、背景、偏好、知识水平
   - **feedback**：用户纠正过我的做法，或明确认可过的非常规做法（带 **Why** 和 **How to apply**）
   - **project**：进行中的工作、决策、截止日期、事故背景（带 **Why** 和 **How to apply**，相对日期要换算成绝对日期）
   - **reference**：外部系统/资源的位置指针

3. **过滤掉不该存的**：代码模式、架构、文件路径、git 历史能查到的东西、一次性调试细节、临时任务状态、CLAUDE.md 里已有的内容。

4. **优先更新已有 memory**，而不是新建重复的。内容冲突时以本次对话为准，并修正旧记录。

5. **写入**：每条一个文件（命名如 `user_role.md` / `feedback_xxx.md` / `project_xxx.md` / `reference_xxx.md`），带完整 frontmatter；然后在 `MEMORY.md` 里加一行不超过 150 字符的索引。

6. **最后报告**：用不超过 5 行告诉用户新增/更新了哪些 memory，以及跳过了什么（比如"这些是一次性调试细节，不值得存"）。

如果本次对话没有任何值得长期保留的内容，直接说明并不要硬凑。
