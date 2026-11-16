# 字幕烧录详解

短剧字幕校对工坊的烧录功能把修正后的字幕烧录进视频，保留原声，输出带字幕的新MP4。

## 烧录流程

```
字幕事件（rows）→ 生成ASS字幕 → ffmpeg libass烧录 → 输出MP4
```

## 生成 ASS 字幕（generateAss）

### 画幅自适应

根据视频宽高自动调整字号和边距：

| 画幅 | 判断 | 字号 | 边距 |
|------|------|------|------|
| 横屏（宽>高） | width > height | 高度 × 5.5% | 左/右：宽度×3%，底部：高度×8% |
| 竖屏（宽<高） | width < height | 宽度 × 4.5% | 左/右：宽度×3%，底部：根据zone |

**竖屏字号收缩原因**：竖屏画面窄，字号按高度放大后一行10来个字就溢出疯狂换行，字幕块巨大遮挡画面。

### ASS 样式

```
Style: Default,Microsoft YaHei,{fontSize},
  &H00FFFFFF,    # 白色文字
  &H000000FF,    # 次要颜色（蓝色，未使用）
  &H00000000,    # 描边颜色（黑色）
  &H80000000,    # 背景颜色（半透明黑）
  0,              # Bold=0
  0,              # Italic=0
  0,              # Underline=0
  0,              # StrikeOut=0
  100,            # ScaleX=100%
  100,            # ScaleY=100%
  0,              # Spacing=0
  0,              # Angle=0
  1,              # BorderStyle=1（描边）
  {outline},      # Outline=描边宽度
  0,              # Shadow=0
  2,              # Alignment=2（底部居中）
  {marginL},      # MarginL=左边距
  {marginR},      # MarginR=右边距
  {marginV},      # MarginV=底部边距
  1               # Encoding=1
```

### zone 字幕区适配

当项目有 zone.json（字幕区检测结果）时：

- 新字幕底部对齐字幕带下边缘：`marginV = playH × (1 - zone.y1) + 2`
- 避免新字幕烧到画面底部与原字幕错位
- 竖屏短剧字幕常在画面中部，固定底部边距会导致字幕位置不对

无 zone 时：`marginV = playH × 0.08`（底部8%，横屏兼容）

### 文本转义

- `{` → `｛`，`}` → `｝`（避免ASS内联代码被解析）
- `\n` → `\N`（ASS换行符）

### 文本优先级

每条字幕的显示文本：
```
editedText（人工修正） > suggested（原文建议） > ocrText（识别文本）
```

空文本跳过（不生成Dialogue行）。

## 烧录（burnSubtitles）

### ffmpeg 命令

```bash
ffmpeg -y -i 输入视频 -vf "ass=字幕文件.ass" -c:v libx264 -crf 23 -preset medium -c:a copy 输出视频.mp4
```

- `-c:a copy`：直接复制原音频流，不重新编码（保留原声，无损）
- `-c:v libx264 -crf 23 -preset medium`：H.264中等质量编码

### 遮罩策略

烧录前可选择遮盖原字幕区，避免新旧字幕重叠：

| 遮罩方式 | 说明 |
|---------|------|
| zone 遮罩 | 项目有 zone.json 时，模糊覆盖字幕带区域（y0到y1），竖屏短剧字幕在中部时精准遮盖 |
| maskBottom 遮罩 | 无 zone 时回退底部遮盖：横屏22%（`maskBottom=0.22`），竖屏30%（`maskBottom=0.3`） |
| 不遮罩 | maskBottom=0 且无 zone，直接烧录（可能新旧字幕重叠） |

**竖屏加大遮罩原因**：竖屏底部硬字幕可能盖在更靠上的位置，底部遮盖加大到30%才能盖住。

### 进度回调

烧录过程通过 ffmpeg 的 stderr 输出解析进度，回调 ratio（0~1）：

```
正在烧录字幕 45%
```

### ASS 临时文件

生成的 ASS 文件写入系统临时目录（`%TEMP%/zimu_burn_{timestamp}.ass`），烧录完成后删除。

## 输出

- 文件：带字幕的MP4（保留原声）
- 时长：与原视频一致
- 字幕：修正后字幕烧录在画面上

## 注意事项

- 烧录会遮盖原字幕区（如开启遮罩），请确认遮罩范围后再导出
- 烧录后的视频字幕不可再编辑（已烧录进画面），如需修改请重新校对后烧录
- 竖屏短剧字幕在中部时，务必确认 zone.json 检测准确，否则遮罩位置不对
- 烧录耗时与视频时长和编码参数有关，长视频可能需要几分钟
