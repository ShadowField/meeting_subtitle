---
description: 读取字幕内容，回答用户问题，把回答写入 log 文件
---

用户在字幕窗口里点击了"问 Claude"按钮。请执行以下步骤：

1. 读取 `/Users/tenghu/Desktop/code/meeting_subtitle/pending_ask.txt` 的内容（这是最近的字幕记录）
2. 判断内容里是否有值得回答的问题或需要总结的内容
3. 生成一段简洁的中文回答（1-3句话，适合在字幕窗口显示）
4. 找到 `/Users/tenghu/Desktop/code/meeting_subtitle/logs/` 目录下**最新的** `meeting_*.txt` 文件
5. 在文件末尾追加一行，格式严格为：`[HH:MM:SS] [Claude]: 你的回答`（时间用当前时间）

注意：
- 回答要简洁，不要换行，控制在 100 字以内
- 只追加一行，不要修改文件其他内容
- 追加完成后告诉用户"已回答，字幕窗口将自动显示"
