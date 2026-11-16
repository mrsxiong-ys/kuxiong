# 使用示例

以下示例展示短剧字幕校对工坊技能的典型调用场景，供 WorkBuddy 智能体参考。

## 场景 1：探测视频信息

**用户请求**：帮我看看这个短剧视频的信息

**调用**：
```bash
node scripts/zimu.js probe "D:/短剧/第01集.mp4"
```

**输出**：
```json
{
  "ok": true,
  "duration": 600.5,
  "width": 1080,
  "height": 1920,
  "orientation": "portrait",
  "aspectRatio": "9:16"
}
```

**解读**：返回时长、宽高、画幅方向（横屏/竖屏），竖屏字幕烧录时字号和遮罩策略不同。

---

## 场景 2：OCR 模式完整校对流水线

**用户请求**：我有一集短剧需要校对字幕，请导入视频识别字幕并与台词原文比对

**调用**：
```bash
node scripts/zimu.js run "D:/短剧/第01集.mp4" --script "D:/短剧/第01集台词.txt" --mode ocr
```

**输出**：
```json
{
  "ok": true,
  "projectDir": "D:/短剧字幕校对工坊/第01集",
  "mode": "ocr",
  "probe": { "duration": 600.5, "width": 1080, "height": 1920 },
  "zone": { "y0": 0.55, "y1": 0.72 },
  "stripCount": 600,
  "frameCount": 600,
  "eventCount": 234,
  "events": [
    { "start": 0, "end": 3, "frameIndex": 0, "text": "你以为我会相信你吗", "source": "ocr" }
  ],
  "logs": ["正在抽帧（每秒 1 帧，自动定位字幕区）…", "正在识别字幕文字（0/600）", ...]
}
```

**解读**：流水线自动完成抽帧 → 字幕区定位 → OCR识别 → 事件分组，输出字幕事件数组。竖屏短剧字幕区在 y0=0.55 到 y1=0.72（画面中部偏下），zone 信息用于后续烧录遮罩。

---

## 场景 3：纯音频 ASR 模式

**用户请求**：这部短剧画面没有字幕，帮我用音频识别字幕

**调用**：
```bash
node scripts/zimu.js run "D:/短剧/第02集.mp4" --script "D:/短剧/第02集台词.txt" --mode asr
```

**输出**：
```json
{
  "ok": true,
  "projectDir": "D:/短剧字幕校对工坊/第02集",
  "mode": "asr",
  "probe": { "duration": 580.2, "width": 1080, "height": 1920 },
  "asrCount": 210,
  "eventCount": 210,
  "events": [
    { "start": 0.0, "end": 2.8, "frameIndex": null, "text": "你以为我会相信你吗", "source": "asr" }
  ],
  "logs": ["正在提取音频…", "正在转写音频（0/210）", ...]
}
```

**解读**：ASR 模式时间轴以音频为准，frameIndex 为 null。适合画面无字幕的短剧。

---

## 场景 4：双通道融合模式

**用户请求**：这部短剧画面有字幕但识别不准，帮我用融合模式重新识别

**调用**：
```bash
node scripts/zimu.js run "D:/短剧/第03集.mp4" --script "D:/短剧/第03集台词.txt" --mode fusion
```

**输出**：
```json
{
  "ok": true,
  "projectDir": "D:/短剧字幕校对工坊/第03集",
  "mode": "fusion",
  "probe": { "duration": 620.0, "width": 1080, "height": 1920 },
  "zone": { "y0": 0.50, "y1": 0.70 },
  "stripCount": 620,
  "frameCount": 620,
  "asrCount": 240,
  "eventCount": 238,
  "events": [
    { "start": 0, "end": 3, "frameIndex": 0, "text": "你以为我会相信你吗", "asrText": "你以为我会相信你吗", "frameText": "你以为我会相信你吗", "source": "frame" }
  ],
  "logs": ["正在抽帧…", "正在识别字幕文字…", "正在提取音频…", "正在转写音频…", "正在融合双通道…", ...]
}
```

**解读**：Fusion 模式同时跑 OCR 和 ASR，source='frame' 表示画面分段（主文本来自语音），source='asr' 表示画面无字幕的纯语音退化行。

---

## 场景 5：台词原文比对

**用户请求**：把识别出的字幕和台词原文比对一下

**调用**：
```bash
node scripts/zimu.js align --events "D:/短剧字幕校对工坊/第01集/events.json" --script "D:/短剧/第01集台词.txt"
```

**输出**：
```json
{
  "ok": true,
  "totalEvents": 234,
  "totalScript": 240,
  "rows": [
    {
      "start": 0, "end": 3, "frameIndex": 0,
      "ocrText": "你以为我会相信你吗",
      "scriptText": "你以为我会相信你吗",
      "similarity": 100,
      "isDiff": false,
      "suggested": "你以为我会相信你吗",
      "diffChars": [],
      "diffStatus": "ok"
    },
    {
      "start": 3, "end": 6, "frameIndex": 3,
      "ocrText": "我来历不明",
      "scriptText": "我来路不明",
      "similarity": 80,
      "isDiff": true,
      "suggested": "我来路不明",
      "diffChars": [2],
      "diffStatus": "diff"
    }
  ],
  "missing": [
    { "index": 45, "text": "这句台词识别漏了" }
  ],
  "extra": [
    { "start": 12.0, "end": 14.0, "text": "识别多出的内容" }
  ]
}
```

**解读**：比对结果包含 rows（匹配行，isDiff 标记差异）、missing（漏检）、extra（多余行）。第二行是同音错字（来历/来路），diffChars=[2] 标记差异字符位置。

---

## 场景 6：导出 SRT 字幕

**用户请求**：导出修正后的SRT字幕

**调用**：
```bash
node scripts/zimu.js export-srt --events "D:/短剧字幕校对工坊/第01集/events.json" --out "D:/短剧字幕校对工坊/第01集/output/第01集.srt"
```

**输出**：
```json
{
  "ok": true,
  "count": 234,
  "outPath": "D:/短剧字幕校对工坊/第01集/output/第01集.srt"
}
```

**解读**：导出 SRT 使用修改后文本（editedText > suggested > ocrText 优先级），空文本跳过。

---

## 场景 7：烧录字幕视频

**用户请求**：把修正后的字幕烧录进视频，导出带字幕的MP4

**调用**：
```bash
node scripts/zimu.js burn "D:/短剧/第01集.mp4" --events "D:/短剧字幕校对工坊/第01集/events.json" --out "D:/短剧字幕校对工坊/第01集/output/第01集-带字幕.mp4" --maskBottom 0.3
```

**输出**：
```json
{
  "ok": true,
  "outPath": "D:/短剧字幕校对工坊/第01集/output/第01集-带字幕.mp4",
  "duration": 600.5
}
```

**解读**：烧录会先遮盖原字幕区（竖屏短剧 maskBottom=0.3，横屏0.22），再烧录修正后字幕，保留原声。项目有 zone.json 时用 zone 精准遮罩字幕带。

---

## 场景 8：导出校对报告

**用户请求**：生成校对报告

**调用**：
```bash
node scripts/zimu.js export-report --events "D:/短剧字幕校对工坊/第01集/events.json" --out "D:/短剧字幕校对工坊/第01集/output/第01集-校对报告.txt"
```

**输出**：
```json
{
  "ok": true,
  "diffs": 12,
  "missing": 6,
  "extra": 3,
  "outPath": "D:/短剧字幕校对工坊/第01集/output/第01集-校对报告.txt"
}
```

**解读**：校对报告包含错误清单（时间轴+识别字幕+原文+修改后）、漏检列表、多余行列表。

---

## 场景 9：导出 CSV 事件表

**用户请求**：导出CSV事件表

**调用**：
```bash
node scripts/zimu.js export-csv --events "D:/短剧字幕校对工坊/第01集/events.json" --out "D:/短剧字幕校对工坊/第01集/output/第01集-事件表.csv"
```

**输出**：
```json
{
  "ok": true,
  "count": 234,
  "outPath": "D:/短剧字幕校对工坊/第01集/output/第01集-事件表.csv"
}
```

**解读**：CSV 字段：序号/开始/结束/识别字幕/台词原文/修改后/状态，带 BOM 头（Excel 兼容）。

---

## 常见问题速查

| 问题 | 解决 |
|------|------|
| 字幕区检测不准 | 手动指定字幕区 / 切换ASR或Fusion模式 |
| OCR识别乱码 | 切换ASR模式 / 关闭其他内存占用程序 / 人工修正 |
| ASR转写失败 | 检查音轨 / 检查模型文件 / 设置ZIMU_HOME |
| 烧录后字幕重叠 | 开启遮罩 / 检查zone.json / 竖屏加大遮罩 |
| 比对漏检多 | 检查原文格式 / 切换识别模式 / 人工补录 |
| 找不到工程 | 设置环境变量 ZIMU_HOME 指向工程根目录 |
