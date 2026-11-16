# kuxiong · WorkBuddy 专家 Skill 合集

本仓库收录一组自研的 **WorkBuddy 专家（Expert）Skill 包**，覆盖内容创作、漫画汉化、副业调研与彩票数据分析等场景。所有包均按 WorkBuddy 开放平台专家包规范打包，可直接导入 WorkBuddy 使用，也可作为二次开发的参考模板。

## 包含的专家包

| 专家包 | 类型 | 版本 | 简介 |
|---|---|---|---|
| [`drama-subtitle-proofreader`](./drama-subtitle-proofreader) | agent 型 | 1.0.1 | 短剧字幕校对专家：导入短剧视频，本地 OCR / ASR 识别字幕，与台词原文逐条比对标色，修正后导出 SRT、烧录视频与校对报告 |
| [`home-side-hustle-scout`](./home-side-hustle-scout) | agent 型 | 1.0.1 | 家庭副业侦察兵：检索可在家操作的副业，按七条红线核验真伪，筛出手机 / 电脑可执行的项目，详述工作内容与收入机制 |
| [`manhua-gongfang`](./manhua-gongfang) | agent 型 | 1.0.1 | 漫画汉化流水线专家：漫画网页批量下载、智能压缩、多语言 OCR 与 AI 翻译、中文覆盖，合成 PDF / CBZ，支持编辑续传 |
| [`dlt-expert`](./dlt-expert) | skill 型 | 1.0.0 | 大乐透分析专家：基于中国体彩官方开奖数据，维护历史数据、分析号码冷热与规律、生成智能选号参考方案 |
| [`ssq-expert`](./ssq-expert) | skill 型 | 1.0.0 | 双色球分析专家：基于中国福彩官方开奖数据，维护历史数据、分析号码冷热与规律、生成智能选号参考方案 |

## 目录结构

每个专家包为一个独立目录，内部遵循 WorkBuddy 专家包规范：

```
kuxiong/
├── README.md                      # 本说明文件
├── drama-subtitle-proofreader/    # 短剧字幕校对专家（agent 型）
│   ├── SKILL.md
│   ├── .codebuddy-plugin/plugin.json
│   ├── agents/
│   ├── avatars/
│   ├── examples/
│   ├── references/
│   └── scripts/
├── home-side-hustle-scout/        # 家庭副业侦察兵（agent 型）
├── manhua-gongfang/               # 漫画汉化流水线专家（agent 型）
├── dlt-expert/                    # 大乐透分析专家（skill 型，SKILL.md 在 skills/ 子目录）
│   ├── .codebuddy-plugin/plugin.json
│   ├── agents/
│   ├── avatars/
│   └── skills/dlt-analysis/
└── ssq-expert/                    # 双色球分析专家（skill 型，SKILL.md 在 skills/ 子目录）
```

**两种专家类型说明：**

- **agent 型**：`SKILL.md` 位于包的顶层根目录。
- **skill 型**：`SKILL.md` 位于 `skills/<name>/` 子目录，`plugin.json` 中通过 `skills` 字段声明技能目录。

## 安装与使用

### 方法一：导入专家包目录

1. 在 WorkBuddy 中打开「专家 / 插件」管理入口；
2. 选择「导入本地专家包」，指向本仓库中对应的专家目录（如 `drama-subtitle-proofreader`）；
3. 确认导入后即可在对话中调用该专家。

### 方法二：从 zip 导入

将对应专家目录打包为 zip（保持单一顶层目录，且 `SKILL.md` 为首条目），再在 WorkBuddy 中导入该 zip 包。

### 使用示例

导入后，直接用自然语言提出需求即可，例如：

- 短剧字幕校对：「我有一集短剧需要校对字幕，请导入视频识别字幕并与台词原文比对」
- 家庭副业：「我想找一份在家能做的副业，请帮我调研并推荐手机或电脑就能操作的」
- 漫画汉化：「我有一部漫画需要汉化，请帮我解析网址并启动流水线处理」
- 大乐透 / 双色球：「帮我更新最新开奖数据并分析」「生成一组智能选号方案」

## 合规与免责说明

- **彩票分析类（dlt-expert / ssq-expert）**：仅基于官方开奖数据做数据统计与规律分析，输出为**理性参考**，**不构成任何投注建议，不承诺中奖**。彩票中奖为随机事件，请理性对待。
- **副业调研类（home-side-hustle-scout）**：所有推荐均经红线核验，仅保留可验证、可操作的项目；涉及收入的部分为公开信息整理，实际收益因人而异，请自行判断。
- 各专家包运行时所需的外部依赖（如模型、语言包、可执行程序等）均由宿主环境提供，包内不包含任何个人隐私信息。

## 二次开发

如需修改某个专家包：

1. 进入对应专家目录，编辑 `SKILL.md`（技能定义）、`agents/*.md`（角色人设）或 `references/`、`scripts/` 等资源；
2. 修改 `.codebuddy-plugin/plugin.json` 中的版本号（**版本号必须严格递增**，同版本重传会被平台拒绝）；
3. 重新打包时保持以下指纹：单一顶层目录（目录名 = `name` = `agentName`）、`SKILL.md` 为 zip 首条目、包内不放 `README.md`。

## License

本仓库专家包按「现状」提供，供学习与交流使用，使用者自行承担使用风险。
