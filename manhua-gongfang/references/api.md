# 本地 HTTP API 接口文档

漫画工坊（Electron 应用）内置 Express 本地服务，监听 `127.0.0.1:{随机端口}`，提供 REST API。以下为完整接口列表。

## 基础信息

- 基础地址：`http://127.0.0.1:{port}`（端口随机分配，启动时确定）
- 协议：HTTP/JSON
- 跨域：已启用 CORS
- 认证：无（本地服务，不对外暴露）

## 状态与版本

### GET /api/state

获取应用状态、版本、设置、模型列表。

**响应**：
```json
{
  "ok": true,
  "version": "1.2.4",
  "settings": { ... },
  "models": [ { "id": "m_xxx", "name": "GPT-4o-mini", "type": "text", ... } ]
}
```

### GET /api/version

获取应用名称和版本。

**响应**：
```json
{ "ok": true, "version": "1.2.4", "name": "漫画工坊" }
```

## 模型管理

### GET /api/models

获取模型列表（类型已归一化）。

### POST /api/models

添加或更新模型。

**请求体**（新增）：
```json
{
  "name": "GPT-4o-mini",
  "type": "text",
  "baseURL": "https://api.openai.com/v1",
  "apiKey": "sk-xxx",
  "modelName": "gpt-4o-mini"
}
```

**请求体**（更新，需带 id）：
```json
{
  "id": "m_xxx",
  "name": "新名称",
  "baseURL": "https://api.openai.com/v1",
  "apiKey": "sk-new",
  "modelName": "gpt-4o-mini"
}
```

**响应**：`{ "ok": true, "id": "m_xxx" }` 或 `{ "ok": true }`

### DELETE /api/models/:id

删除指定模型。

### POST /api/test-model

测试模型连接。

**请求体**：
```json
{
  "modelId": "m_xxx",
  "baseURL": "https://api.openai.com/v1",
  "apiKey": "sk-xxx",
  "modelName": "gpt-4o-mini"
}
```

**响应**：`{ "ok": true, "note": "连接正常，模型名可用" }` 或 `{ "ok": false, "error": "错误信息" }`

## 设置管理

### GET /api/settings

获取当前设置。

### POST /api/settings

更新设置（支持部分更新）。

**请求体**（示例）：
```json
{
  "quality": 90,
  "compress": true,
  "translate": true,
  "translateMode": "direct",
  "modelId": "m_xxx",
  "imageModelId": "m_yyy"
}
```

### POST /api/settings/media-root

更新媒体根目录。

**请求体**：`{ "mediaRoot": "{mediaRoot}" }`

## 网址解析

### POST /api/resolve

解析漫画网址。

**请求体**：`{ "url": "https://mangadex.org/chapter/xxx" }`

**响应**（MangaDex 作品）：
```json
{
  "ok": true,
  "kind": "manga",
  "id": "xxx",
  "title": "漫画标题",
  "alt": "别名",
  "coverUrl": "https://...",
  "chapters": [
    { "id": "xxx", "chapter": "1", "title": "", "pages": 20, "label": "第1话", "lang": "en", "langLabel": "英语" }
  ]
}
```

**响应**（MangaDex 章节）：
```json
{
  "ok": true,
  "kind": "chapter",
  "id": "xxx",
  "title": "漫画标题",
  "label": "第1话 - 标题",
  "pages": 20,
  "lang": "en",
  "langLabel": "英语"
}
```

**响应**（通用网页）：
```json
{ "ok": true, "kind": "generic", "url": "...", "title": "hostname" }
```

## 流水线任务

### POST /api/pipeline

启动流水线任务。

**请求体**：
```json
{
  "url": "https://mangadex.org/title/xxx",
  "chapterIds": ["chapter1", "chapter2"],
  "settings": {
    "editManual": false,
    "aiRedraw": true,
    "pdf": true,
    "cbz": true
  }
}
```

**响应**：`{ "ok": true, "jobId": "job_xxx" }`

### GET /api/jobs/:id

查询任务状态（含步骤进度、日志）。

**响应**：
```json
{
  "ok": true,
  "job": {
    "id": "job_xxx",
    "status": "working",
    "stage": "OCR 多语言识别",
    "current": 10,
    "total": 20,
    "logs": ["...", "..."],
    "steps": [ { "name": "解析网址", "status": "done", "dur": 1 }, ... ]
  }
}
```

### POST /api/jobs/:id/cancel

取消任务。

## 历史记录

### GET /api/history

获取历史记录列表（最多 200 条）。

### DELETE /api/history/:id

删除历史记录。

**查询参数**：`deleteFiles=1`（同时删除输出文件）

### POST /api/history/:id/resume

断点续传：恢复编辑会话或重新处理。

**响应**（恢复编辑）：
```json
{ "ok": true, "action": "resume-edit", "editId": "e_xxx", "title": "漫画标题" }
```

**响应**（重新处理）：
```json
{ "ok": true, "action": "reprocess", "url": "https://..." }
```

## 手动编辑会话

### GET /api/edit/:id

获取编辑会话数据（章节列表、文字框、覆盖层）。

**响应**：
```json
{
  "ok": true,
  "id": "e_xxx",
  "title": "漫画标题",
  "root": "{mediaRoot}/漫画标题",
  "chapters": [
    {
      "index": 0,
      "label": "第1话",
      "pageCount": 20,
      "boxes": { "1": [ { "n": 1, "text": "原文", "zh": "中文", "x": 100, "y": 200, "w": 300, "h": 50 } ] },
      "overlays": { "1": [ { "text": "中文", "x0": 100, "y0": 200, "x1": 400, "y1": 250 } ] }
    }
  ]
}
```

### GET /api/edit/:id/page/:ch/:n

获取某章节某页的图片（默认清空版，`?orig=1` 返回原图）。

### POST /api/edit/:id/save

保存某页的文字框和台词翻译。

**请求体**：
```json
{
  "ch": 0,
  "page": 1,
  "overlays": [ { "text": "中文", "x0": 100, "y0": 200, "x1": 400, "y1": 250 } ],
  "boxes": {
    "n": 1,
    "boxes": [ { "n": 1, "text": "原文", "zh": "中文", "x": 100, "y": 200, "w": 300, "h": 50 } ]
  }
}
```

### POST /api/edit/:id/finish

一键生成：渲染全部页文字 → 合成 PDF/CBZ。

**请求体**：`{ "pdf": true, "cbz": true }`

**响应**：
```json
{
  "ok": true,
  "root": "{mediaRoot}/漫画标题",
  "outputs": [ { "label": "第1话", "dir": "...", "pdf": "...", "cbz": "...", "pages": 20 } ],
  "message": "已生成 1 个章节（PDF）（CBZ）"
}
```

## 其他

### POST /api/open-folder

打开文件管理器到指定路径。

**请求体**：`{ "path": "{mediaRoot}/漫画标题" }`
