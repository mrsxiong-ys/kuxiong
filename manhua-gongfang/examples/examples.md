# 使用示例

以下示例展示漫画工坊技能的典型调用场景，供 WorkBuddy 智能体参考。

## 场景 1：解析 MangaDex 章节链接

**用户请求**：帮我看看这个漫画链接 https://mangadex.org/chapter/xxx

**调用**：
```bash
node scripts/mhgf.js resolve "https://mangadex.org/chapter/xxx"
```

**输出**：
```json
{
  "ok": true,
  "kind": "chapter",
  "id": "xxx",
  "title": "某漫画标题",
  "label": "第1话 - 标题",
  "pages": 20,
  "lang": "en"
}
```

**解读**：返回章节标题、页数、语言，可据此决定是否继续处理。

---

## 场景 2：汉化整部 MangaDex 漫画（指定章节范围）

**用户请求**：把这部漫画前 5 话汉化成中文 PDF

**调用**：
```bash
node scripts/mhgf.js run "https://mangadex.org/title/xxx" --chapters 1,2,3,4,5 --pdf --no-cbz
```

**输出**：
```json
{
  "ok": true,
  "jobId": "job_xxx",
  "status": "done",
  "title": "某漫画标题",
  "outputs": [
    { "label": "第1话", "dir": "{输出目录}/某漫画标题/第1话", "pdf": "...第1话.pdf", "cbz": null, "pages": 20 }
  ],
  "logs": ["任务已创建：...", "—— 解析网址 ——", ...]
}
```

**解读**：流水线自动完成解析 → 下载 → 压缩 → OCR → 翻译 → 覆盖 → 合成，输出每章节 PDF 路径。

---

## 场景 3：批量翻译台词文件

**用户请求**：把这份台词 JSON 翻译成中文

**台词文件**（台词.json）：
```json
["Hello, what's your name?", "My name is Alice.", "Nice to meet you!"]
```

**调用**：
```bash
node scripts/mhgf.js translate --input 台词.json --baseURL https://api.openai.com/v1 --apiKey sk-xxx --model gpt-4o-mini
```

**输出**：
```json
{
  "ok": true,
  "count": 3,
  "output": "translated.json",
  "translations": ["你好，你叫什么名字？", "我叫爱丽丝。", "很高兴认识你！"]
}
```

---

## 场景 4：OCR 识别漫画页面文字

**用户请求**：识别这张漫画页的英文文字

**调用**：
```bash
node scripts/mhgf.js ocr --input page.jpg --lang eng
```

**输出**：
```json
{
  "ok": true,
  "lang": "eng",
  "count": 2,
  "boxes": [
    { "text": "Hello!", "conf": 95, "x0": 100, "y0": 200, "x1": 300, "y1": 250 },
    { "text": "Nice to meet you.", "conf": 92, "x0": 100, "y0": 300, "x1": 400, "y1": 350 }
  ]
}
```

**解读**：输出每条文字的原文、置信度、坐标框（x0,y0,x1,y1 为像素坐标），可用于后续覆盖绘制。

---

## 场景 5：图片目录合成 PDF/CBZ

**用户请求**：把下载好的漫画图片打包成 PDF 和 CBZ

**调用**：
```bash
node scripts/mhgf.js pack --input "{输出目录}/某漫画/第1话" --pdf --cbz
```

**输出**：
```json
{
  "ok": true,
  "pages": 20,
  "outputs": {
    "pdf": "{输出目录}/某漫画/第1话/第1话.pdf",
    "cbz": "{输出目录}/某漫画/第1话/第1话.cbz"
  }
}
```

---

## 场景 6：查看任务进度（轮询）

**用户请求**：刚才的任务处理到哪了？

**说明**：`run` 命令是同步等待任务完成的；若需查看进行中任务状态，使用本地 API：
```bash
curl http://127.0.0.1:{port}/api/jobs/{jobId}
```

**输出**：包含 status、stage、current/total、logs、steps，可实时展示进度。

---

## 场景 7：MangaDex 作品链接解析（查看章节列表）

**调用**：
```bash
node scripts/mhgf.js resolve "https://mangadex.org/title/xxx"
```

**输出**：
```json
{
  "ok": true,
  "kind": "manga",
  "id": "xxx",
  "title": "某漫画标题",
  "alt": "别名",
  "coverUrl": "https://...",
  "chapterCount": 128,
  "chapters": [
    { "id": "...", "chapter": "1", "pages": 20, "lang": "en" },
    ...
  ]
}
```

**解读**：`chapterCount` 为总章节数，`chapters` 返回前 50 章预览。用户可据此选择章节范围。

---

## 场景 8：直译模式（多模态模型看图翻译）

**用户请求**：这部漫画 OCR 识别不准，直接用图片翻译

**说明**：直译模式必须配合手动编辑，且需要多模态模型（image 类型）。在 GUI 设置中：
1. 翻译模式改为「直译」
2. 勾选「✏️ 手动编辑」
3. 配置图像模型（如 gpt-4o）
4. 开始处理后，在编辑页手动贴字确认位置

无头脚本 `run` 不支持直译+编辑会话（编辑需 GUI 交互），仅支持 OCR 模式全自动流水线。

---

## 常见问题速查

| 问题 | 解决 |
|------|------|
| 解析报「网址格式不对」 | 网址必须以 http:// 或 https:// 开头 |
| 解析报「无法识别 MangaDex 链接」 | 只支持 /chapter/ 和 /title/（或 /manga/）链接 |
| 下载超时 | 配置代理 MHGF_PROXY 或检查网络 |
| 翻译报 429 | 增大翻译间隔或换模型 |
| OCR 不准 | 换直译模式或手动编辑模式 |
| 找不到工程 | 设置环境变量 MHGF_HOME 指向工程根目录 |
