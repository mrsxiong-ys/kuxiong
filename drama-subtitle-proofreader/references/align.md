# 台词原文比对算法详解

短剧字幕校对工坊的核心是「识别字幕 × 台词原文」的逐条比对，本文档详细说明比对算法。

## 输入

- **字幕事件（events）**：OCR/ASR/Fusion 识别出的字幕行，每项 `{ start, end, frameIndex, text, source }`
- **台词原文（scriptItems）**：从 txt/srt 文件解析出的台词条目，每项 `{ index, text, start?, end? }`

## 台词原文解析

### txt 格式

- 每行一句台词
- 空行跳过
- 输出：`{ kind: 'txt', items: [{ index, text }] }`

### srt 格式

- 标准 SRT 格式：序号 + 时间轴 + 文本
- 解析时间轴：`00:00:01,000 --> 00:00:03,500`
- 文本行合并（去掉序号和时间轴行）
- 输出：`{ kind: 'srt', items: [{ index, text, start, end }] }`

### ass 格式

- 支持 ASS 字幕格式解析（备用）

## 归一化（normalize）

比对前先对文本做归一化处理：

```
1. 去除所有空白字符（\s+ → 空）
2. 去除标点符号：
   中文：，。！？、；：""''「」『』《》〈〉（）【】…—·
   英文：,.!?;:'"\-–~～
   括号：()[]
3. 全角字母数字转半角（Ａ-Ｚａ-ｚ０-９ → A-Za-z0-9）
4. 转小写
```

**目的**：消除格式差异，聚焦内容差异。同音错字（如"来路/来历"）归一化后仍不同，能被检出。

## 相似度计算（similarity）

基于编辑距离（Levenshtein distance）：

```
similarity(a, b) = 1 - levenshtein(normalize(a), normalize(b)) / max(len(a), len(b))
```

- 完全相同：1.0
- 完全不同：0.0
- 归一化后为空字符串：0.0

## 顺序对齐算法（align）

### 阈值

| 阈值 | 值 | 含义 |
|------|-----|------|
| MATCH | 0.55 | 达到此值视为匹配 |
| LOOSE | 0.35 | 达到此值视为宽松匹配 |

### 对齐逻辑

使用双指针（i=事件指针, j=原文指针）顺序扫描：

```
while i < events.length && j < scriptItems.length:
    ev = events[i], sc = scriptItems[j]
    s = similarity(ev.text, sc.text)          # 当前对相似度
    sNext = similarity(ev.text, sc[j+1].text) # 与下一句原文的相似度
    eNext = similarity(ev[i+1].text, sc.text) # 下一事件与当前原文的相似度

    if s >= MATCH:
        # 匹配
        isDiff = normalize(ev.text) != normalize(sc.text)
        output matched row (isDiff=True/False)
        i++, j++
    elif sNext >= MATCH && sNext > eNext:
        # 原文这句识别漏了
        missing.push(sc)
        j++
    elif eNext >= MATCH:
        # 识别多出了这句
        extra.push(ev)
        i++
    elif s > LOOSE:
        # 宽松匹配（差异较大但可能对得上）
        output matched row (isDiff=True)
        i++, j++
    elif sNext > eNext && sNext > LOOSE:
        # 原文这句识别漏了
        missing.push(sc)
        j++
    else:
        # 识别多出了这句
        extra.push(ev)
        i++
```

### 尾部处理

- 事件剩余（i < events.length）：全部加入 extra（多余行）
- 原文剩余（j < scriptItems.length）：全部加入 missing（漏检）

## 输出结构

### rows（匹配行）

```json
{
  "start": 1.0,           // 开始时间（秒）
  "end": 3.5,             // 结束时间（秒）
  "frameIndex": 1,        // 对应帧索引
  "ocrText": "识别字幕",    // OCR/ASR识别出的文本
  "scriptText": "台词原文",  // 台词原文
  "similarity": 85,       // 相似度百分比（0-100）
  "isDiff": true,         // 是否有差异
  "suggested": "台词原文",  // 建议修改文本（原文）
  "diffChars": [3, 5],    // 差异字符位置（归一化文本中）
  "diffStatus": "diff"    // 差异状态：diff / ok
}
```

### missing（漏检）

原文有、识别未出现的台词：
```json
[{ "index": 5, "text": "这句台词识别漏了" }]
```

### extra（多余行）

识别出现、原文没有的台词：
```json
[{ "start": 12.0, "end": 14.0, "text": "识别多出的内容", "source": "ocr" }]
```

## 差异字符高亮（diffChars）

基于归一化文本逐字比较，找出差异位置：

```
ocrText:   "我来路不明"  → normalize → "我来路不明"
scriptText: "我来历不明"  → normalize → "我来历不明"
diffChars: [2]  （第2个字符不同：路 vs 历）
```

GUI 中根据 diffChars 在建议文本上高亮差异字符。

## 已知限制

- **顺序对齐**：采用顺序对齐而非全局最优对齐，如果识别顺序与原文顺序不一致（如漏检导致错位），可能产生连锁误判
- **同音错字**：能检出（"来路/来历"归一化后不同），但同义替换（"好/棒"）可能被判为一致
- **多句并排**：短剧画面有时多句台词并排显示，OCR可能识别为一条，导致与原文对不上
- **字幕遮挡**：字幕被画面元素遮挡时，OCR识别不全，比对会显示为差异
- **建议人工扫一眼**：漏检/多余列表需要人工确认，自动比对不能完全替代人工校对
