# kuxiong · WorkBuddy 专家 Skill 合集

本仓库收录一组自研的 **WorkBuddy 专家（Expert）Skill 包**，覆盖内容创作、漫画汉化、副业创业、求职就业与彩票数据分析等场景。所有包均按 WorkBuddy 开放平台专家包规范打包，可直接导入 WorkBuddy 使用，也可作为二次开发的参考模板。

共收录 **13 个专家包**：内容创作与本地化 2 个、副业与创业 6 个、求职就业 1 个、AI 接单与本地生活 2 个、彩票数据分析 2 个。

## 包含的专家包

### 内容创作与本地化

| 专家包 | 类型 | 版本 | 简介 |
|---|---|---|---|
| [`drama-subtitle-proofreader`](./drama-subtitle-proofreader) | agent 型 | 1.0.2 | 短剧字幕校对专家：导入短剧视频，本地 OCR / ASR 识别字幕，与台词原文逐条比对标色，修正后导出 SRT、烧录视频与校对报告 |
| [`manhua-gongfang`](./manhua-gongfang) | agent 型 | 1.0.1 | 漫画汉化流水线专家：漫画网页批量下载、智能压缩、多语言 OCR 与 AI 翻译、中文覆盖，合成 PDF / CBZ，支持编辑续传 |

### 副业与创业

| 专家包 | 类型 | 版本 | 简介 |
|---|---|---|---|
| [`home-side-hustle-scout`](./home-side-hustle-scout) | agent 型 | 1.0.1 | 家庭副业侦察兵：检索可在家操作的副业，按七条红线核验真伪，筛出手机 / 电脑可执行的项目，详述工作内容与收入机制 |
| [`after-work-sidehustle-planner`](./after-work-sidehustle-planner) | agent 型 | 1.0.2 | 下班副业规划师：先问诊技能、时间与本金，从真实项目库匹配并核实最适合的下班赚钱方向，输出可执行方案与 7 天启动计划 |
| [`mom-business-architect`](./mom-business-architect) | agent 型 | 1.0.2 | 宝妈个人事业架构师：问清碎片时间与回报预期，调研真实行情，为宝妈匹配低投入、可在家做的个人事业冷启动方案 |
| [`resale-operations-advisor`](./resale-operations-advisor) | agent 型 | 1.0.2 | 二手转卖运营顾问：盘点货源与投入，调研二手平台真实行情与规则，给出定价策略、上架曝光优化与复购运营方案 |
| [`small-business-planner`](./small-business-planner) | agent 型 | 1.0.2 | 小生意创业测算顾问：问诊品类与资金回本预期，调研真实成本行情，算清启动预算、盈亏平衡与首月运营方案，避免盲目投钱 |
| [`product-launch-expert`](./product-launch-expert) | agent 型 | 1.0.3 | 新品选品与上市策略专家：从内容场挖掘原生诉求、定位品牌真空，走完选品、产品定义、**商标近似查询与可注册性分析**、知产保护、打样到上架全流程 |

### 求职就业

| 专家包 | 类型 | 版本 | 简介 |
|---|---|---|---|
| [`employment-navigation-expert`](./employment-navigation-expert) | agent 型 | 1.0.2 | 就业导航专家：问诊技能与约束，调研真实就业市场，给出可落地的求职方向、简历优化与面试行动方案 |

### AI 接单与本地生活

| 专家包 | 类型 | 版本 | 简介 |
|---|---|---|---|
| [`ai-gig-matcher`](./ai-gig-matcher) | agent 型 | 1.0.2 | AI 接单匹配师：盘点可交付技能，调研接单平台真实规则与行情，用 AI 工具匹配接单方向、报价话术与首单交付流程 |
| [`local-life-content-advisor`](./local-life-content-advisor) | agent 型 | 1.0.2 | 本地生活内容顾问：问诊店铺与目标，调研本地生活平台规则与同城竞品，输出内容选题、拍摄脚本与团购转化方案 |

### 彩票数据分析

| 专家包 | 类型 | 版本 | 简介 |
|---|---|---|---|
| [`dlt-expert`](./dlt-expert) | skill 型 | 1.0.0 | 大乐透分析专家：基于中国体彩官方开奖数据，维护历史数据、分析号码冷热与规律、生成智能选号参考方案 |
| [`ssq-expert`](./ssq-expert) | skill 型 | 1.0.0 | 双色球分析专家：基于中国福彩官方开奖数据，维护历史数据、分析号码冷热与规律、生成智能选号参考方案 |

## 目录结构

每个专家包为一个独立目录，内部遵循 WorkBuddy 专家包规范：

```
kuxiong/
├── README.md                      # 本说明文件
│
│  ── 内容创作与本地化 ──
├── drama-subtitle-proofreader/    # 短剧字幕校对专家（agent 型）
│   ├── SKILL.md
│   ├── .codebuddy-plugin/plugin.json
│   ├── agents/
│   ├── avatars/
│   ├── examples/
│   ├── references/
│   └── scripts/
├── manhua-gongfang/               # 漫画汉化流水线专家（agent 型）
│
│  ── 副业与创业 ──
├── home-side-hustle-scout/        # 家庭副业侦察兵（agent 型）
├── after-work-sidehustle-planner/ # 下班副业规划师（agent 型）
├── mom-business-architect/        # 宝妈个人事业架构师（agent 型）
├── resale-operations-advisor/     # 二手转卖运营顾问（agent 型）
├── small-business-planner/        # 小生意创业测算顾问（agent 型）
├── product-launch-expert/         # 新品选品与上市策略专家（agent 型）
│
│  ── 求职就业 / AI 接单 / 本地生活 ──
├── employment-navigation-expert/  # 就业导航专家（agent 型）
├── ai-gig-matcher/                # AI 接单匹配师（agent 型）
├── local-life-content-advisor/    # 本地生活内容顾问（agent 型）
│
│  ── 彩票数据分析（skill 型）──
├── dlt-expert/                    # 大乐透分析专家（SKILL.md 在 skills/ 子目录）
│   ├── .codebuddy-plugin/plugin.json
│   ├── agents/
│   ├── avatars/
│   └── skills/dlt-analysis/
└── ssq-expert/                    # 双色球分析专家（SKILL.md 在 skills/ 子目录）
```

**两种专家类型说明：**

- **agent 型**（多数包）：`SKILL.md` 位于包的顶层根目录。
- **skill 型**（dlt-expert / ssq-expert）：`SKILL.md` 位于 `skills/<name>/` 子目录，`plugin.json` 中通过 `skills` 字段声明技能目录。

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
- 漫画汉化：「我有一部漫画需要汉化，请帮我解析网址并启动流水线处理」
- 家庭副业：「我想找一份在家能做的副业，请帮我调研并推荐手机或电脑就能操作的」
- 下班副业：「我下班后有 3 小时，想找个靠谱的副业赚钱，帮我匹配适合我的项目」
- 宝妈事业：「我是全职宝妈，每天只有两小时，想做点在家赚钱的事，帮我出一套个人事业方案」
- 二手转卖：「想在闲鱼卖闲置赚钱，帮我做定价和上架曝光方案」
- 小生意测算：「我想摆摊卖小吃，帮我算清启动成本、回本周期，并给出运营方案」
- 新品选品：「我想做女性健身方向，帮我看看有没有选品机会，并推荐能注册的商标」
- 就业求职：「我失业三个月了，想找个靠谱工作，帮我分析就业方向并制定求职计划」
- AI 接单：「我会写文案，想用 AI 接单赚钱，帮我匹配接单方向和平台」
- 本地生活：「我是本地餐饮老板，想做抖音本地生活，帮我出内容和转化方案」
- 大乐透 / 双色球：「帮我更新最新开奖数据并分析」「生成一组智能选号方案」

## 合规与免责说明

- **彩票分析类（dlt-expert / ssq-expert）**：仅基于官方开奖数据做数据统计与规律分析，输出为**理性参考**，**不构成任何投注建议，不承诺中奖**。彩票中奖为随机事件，请理性对待。
- **副业 / 创业 / 就业类**：所有推荐均经红线核验或基于公开信息调研整理，仅保留可验证、可操作的方向；涉及收入、成本、回本周期的部分为公开信息整理与测算参考，**实际收益因人而异**，创业与求职有真实风险，请结合自身情况独立判断。
- **商标 / 知产类（product-launch-expert）**：推荐任何拟注册商标前，必须先到**国家知识产权局**做近似商标查询并将结果反馈给专家，专家基于查询结果做可注册性分析；**不代替官方审查结论，不承诺注册成功**，最终注册结果以国家知识产权局审查为准。
- 各专家包运行时所需的外部依赖（如模型、语言包、可执行程序等）均由宿主环境提供，包内不包含任何个人隐私信息。

## 二次开发

如需修改某个专家包：

1. 进入对应专家目录，编辑 `SKILL.md`（技能定义）、`agents/*.md`（角色人设）或 `references/`、`scripts/` 等资源；
2. 修改 `.codebuddy-plugin/plugin.json` 中的版本号（**版本号必须严格递增**，同版本重传会被平台拒绝）；
3. 重新打包时保持以下指纹：单一顶层目录（目录名 = `name` = `agentName`）、`SKILL.md` 为 zip 首条目、包内不放 `README.md`。

## License

本仓库专家包按「现状」提供，供学习与交流使用，使用者自行承担使用风险。
