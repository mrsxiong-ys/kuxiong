# 配置参数完整说明

漫画工坊的所有配置项通过 `settings.json` 持久化，存储在 Electron 的 userData 目录下。以下为完整参数说明。

## 核心参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| mediaRoot | string | 用户盘漫画工坊目录 | 输出根目录，所有漫画项目存放在此目录下 |
| quality | number | 90 | 图片压缩质量（0-100） |
| pageQuality | number | 88 | 页面图片显示质量 |
| compress | boolean | true | 是否智能压缩 |
| translate | boolean | true | 是否翻译 |
| keepOriginal | boolean | true | 是否保留原图（不保留则处理后删除原图） |
| pdf | boolean | true | 是否生成 PDF |
| cbz | boolean | true | 是否生成 CBZ |
| proxy | string | '' | 代理地址（如 `http://127.0.0.1:7890`），留空直连 |
| modelId | string | '' | 默认文本模型 ID |
| imageModelId | string | '' | 默认图像模型 ID |
| downloadDelayMs | number | 350 | 下载间隔毫秒数 |
| translateMode | string | 'direct' | 翻译模式：`direct`（图片直译）/ `ocr`（OCR 识别后翻译） |
| translateIntervalMs | number | 800 | 翻译间隔毫秒数（避免限流） |
| editManual | boolean | true | 手动编辑模式（生成编辑会话，等待用户贴字） |
| aiRedraw | boolean | true | AI 图像重绘（用图像模型抹除原气泡） |

## 参数约束

- `quality`、`pageQuality`、`downloadDelayMs`：非负数，自动转数值
- `translateIntervalMs`：0-10000 之间
- `translateMode`：只接受 `direct` 或 `ocr`，其他值回退到 `ocr`
- 布尔参数：自动转布尔值
- `proxy`、`modelId`、`imageModelId`：字符串，自动 trim

## 翻译模式选择

### OCR 模式（translateMode: 'ocr'）

- 流程：OCR 识别气泡文字 → 批量翻译 → 覆盖绘制
- 适合：图片清晰、气泡文字规整的漫画
- 优点：速度快、不需要多模态模型
- 缺点：OCR 识别误差会累积到翻译

### 直译模式（translateMode: 'direct'）

- 流程：直接把页面图片发给多模态模型 → 看图识别+翻译 → 手动贴字
- 适合：图片复杂、气泡文字不规则、OCR 识别不准的漫画
- 优点：跳过 OCR 误差，多模态模型直接理解画面
- 缺点：需要多模态模型、必须配合手动编辑、速度较慢
- 注意：直译模式必须勾选「✏️ 手动编辑」，否则流水线报错

## 手动编辑模式（editManual）

- 开启后，流水线在 OCR/翻译后暂停，生成「编辑会话」
- 用户在编辑页逐页贴字、调整文字框
- 保存进度：自动写入台词翻译数据与文字框位置数据（编辑会话文件）
- 一键生成：渲染中文图片并合成 PDF/CBZ
- 断点续传：重启软件后在历史记录点「重新处理」，编辑进度自动恢复
- 注意：手动编辑模式需要配置图像模型（用于抹除气泡原文）

## 模型配置

模型配置持久化存储（应用用户数据目录），支持多个模型：

```json
[
  {
    "id": "m_xxx",
    "name": "GPT-4o-mini",
    "type": "text",
    "baseURL": "https://api.openai.com/v1",
    "apiKey": "sk-xxx",
    "modelName": "gpt-4o-mini"
  },
  {
    "id": "m_yyy",
    "name": "GPT-4o",
    "type": "image",
    "baseURL": "https://api.openai.com/v1",
    "apiKey": "sk-xxx",
    "modelName": "gpt-4o"
  }
]
```

- `type`：`text`（文本模型，用于翻译）/ `image`（图像模型，用于 AI 重绘/直译）
- 模型名包含 `image`/`img` 的自动归类为图像模型
- API Key 加密存储，界面显示时脱敏（••••）

## 模型测试

添加模型后可点击「测试」验证连接：
- 调用 `GET {baseURL}/models` 验证接口连通性
- 检查 API Key 有效性（401=无效，403=无权限）
- 验证模型名是否在可用列表中

## 数据存储位置

- Windows：应用用户数据目录（Electron userData 目录）下的漫画工坊文件夹
- 文件：设置、模型、历史记录、错误日志四类持久化数据文件
- 媒体文件：输出根目录下的漫画项目目录

## OCR 语言包

OCR 语言包由漫画工坊宿主应用随包分发（应用打包时内置到应用资源中），无需单独下载：
- 英语、俄语、意大利语、葡萄牙语四种语言包

tesseract.js 通过本地语言目录加载，避免从网络下载。

## 字体文件

漫画中文字体由漫画工坊宿主应用随包分发：
- 霞鹜文楷（优先）
- 思源黑体（回退）

覆盖绘制时使用 `LXGW WenKai, Noto Sans SC, Microsoft YaHei, SimHei, sans-serif` 字体栈，确保中文显示美观。
