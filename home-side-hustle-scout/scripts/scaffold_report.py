#!/usr/bin/env python3
"""Generate a skeleton Markdown report for a home-side-hustle research run.

This script only produces the STRUCTURE. It never invents candidates, scores,
income figures or any other finding -- every placeholder is filled by the
research process itself.

Usage:
    python3 scaffold_report.py --out "./副业调研报告" --top 3

Options:
    --out           Output directory or file path (created if missing). Default: .
    --top           Number of Top recommendations. Default: 3
    --candidates    Number of candidate rows in the pool. Default: 10
"""

import argparse
import sys
from pathlib import Path

DISCLAIMER = (
    "本报告为公开信息整理，不构成投资、就业或收益承诺。所有门槛、费率、结算规则以平台官方页面"
    "及账号后台实际显示为准；收入相关数字若标注「待实测」，需本人小额试跑后自行校准。"
    "涉及税务、合同、经营资质的问题请咨询专业人士。本报告不含任何需先行付费的项目。"
)

SUMMARY_HINT = "> 待填：Top{top} 一句话推荐，每条附一条最大风险提示。"

CANDIDATE_TABLE = """| # | 副业名 | 平台/渠道 | 收入机制 | 设备要求 | 启动门槛 | 来源 URL | 可信度 |
|---|---|---|---|---|---|---|---|"""

CANDIDATE_ROW = "| {i} |  |  |  |  |  |  |  |"

VERIFY_TABLE = """| 候选 | 判定 | 依据（来源等级 + URL） | 命中红线 | 备注 |
|---|---|---|---|---|"""

SCORE_TABLE = """| 候选 | 设备 | 时间 | 成本 | 持续 | 合规 | 总分 | 推荐理由 | 最大风险 |
|---|---|---|---|---|---|---|---|---|"""

SCORE_ROW = "|  |  |  |  |  |  |  |  |  |"

BRIEF_SECTIONS = [
    ("1. 一句话定义", "≤30 字，说清这个活到底是什么"),
    ("2. 准入门槛", "年龄 / 实名 / 粉丝数 / 账号条件，每条附官方来源"),
    ("3. 每天实际干什么", "动作拆到可执行粒度，如「选题 10min → 拍摄 15min → 剪辑 20min → 发布 5min」"),
    ("4. 需要什么", "设备 / 技能（写清没有怎么办）/ 启动资金"),
    ("5. 收入机制", "谁付钱 → 按什么算 → 何时入账"),
    ("6. 收入区间", "起步 / 常见 / 上限 三档，每档标来源；官方未公开的写「官方未公开，待实测」"),
    ("7. 结算与提现", "周期、门槛、手续费、税费；写不清则回退 Step 2 重做核验"),
    ("8. 时间账", "到第一笔收入预计多少天 / 多少篇（单），不用「很快」"),
    ("9. 风险与红线", "≥3 条，含违规、政策、沉没成本"),
]


def build_report(top: int, candidates: int) -> str:
    lines = []
    lines.append("# 家庭副业调研报告")
    lines.append("")
    lines.append(f"> 本报告由家庭副业侦察兵工作流生成骨架，正文内容需由调研过程填充。")
    lines.append(f"> Top 推荐数：{top}；候选池条目数：{candidates}。")
    lines.append("")

    # 1
    lines.append("## 1. 结论摘要")
    lines.append("")
    lines.append(SUMMARY_HINT.format(top=top))
    for i in range(1, top + 1):
        lines.append(f"- **Top{i}**：<一句话推荐> ｜ **最大风险**：<一条风险>")
    lines.append("")

    # 2
    lines.append("## 2. 候选池")
    lines.append("")
    lines.append(CANDIDATE_TABLE)
    for i in range(1, candidates + 1):
        lines.append(CANDIDATE_ROW.format(i=i))
    lines.append("")
    lines.append("> 完成条件：候选 ≥8 条，收入机制覆盖 ≥3 种，每条至少 1 个可点击来源。")
    lines.append("")

    # 3
    lines.append("## 3. 真实性核验结果")
    lines.append("")
    lines.append(VERIFY_TABLE)
    for _ in range(candidates):
        lines.append("|  | 可推进 / 待补 / 淘汰 |  | R1–R7 / — |  |")
    lines.append("")
    lines.append("> 完成条件：每条候选有明确判定；淘汰项写明红线编号与触发话术；「可推进」项至少 1 条官方来源。")
    lines.append("")

    # 4
    lines.append("## 4. Top 推荐")
    lines.append("")
    lines.append(SCORE_TABLE)
    for _ in range(top):
        lines.append(SCORE_ROW)
    lines.append("")
    lines.append("> 评分维度：设备适配 / 时间适配 / 启动成本 / 可持续性 / 合规风险，每项 0–2 分。")
    lines.append("> 任何「先付费」候选直接淘汰，不参与评分；某维 0 分的候选不得进入 Top。")
    lines.append("")

    # 5
    lines.append("## 5. 副业说明书")
    lines.append("")
    for i in range(1, top + 1):
        lines.append(f"### 5.{i} 项目名：<待填>")
        lines.append("")
        for heading, hint in BRIEF_SECTIONS:
            lines.append(f"#### {heading}")
            lines.append("")
            lines.append(f"> 待填：{hint}")
            lines.append("")
        lines.append("#### 待补项")
        lines.append("")
        lines.append("> 格式：`- [待补] 缺什么 —— 去哪补 / 谁能补`")
        lines.append("")

    # 6
    lines.append("## 6. 待补项汇总")
    lines.append("")
    lines.append("> 格式：`- [待补] 缺什么 —— 去哪补 / 谁能补 / 补到什么程度算数`")
    lines.append("> 规则：指不回来源的数字一律进待补项，禁止用「大概 / 通常 / 一般」替代。")
    lines.append("")
    lines.append("- [待补]  ——  ")
    lines.append("")

    # 7
    lines.append("## 7. 免责声明")
    lines.append("")
    lines.append(DISCLAIMER)
    lines.append("")

    return "\n".join(lines)


def resolve_output(out_arg: str, filename: str) -> Path:
    """Return the target file path. If --out is a directory, append filename."""
    path = Path(out_arg).expanduser()
    if path.suffix.lower() in (".md", ".markdown"):
        return path
    return path / filename


def main() -> int:
    parser = argparse.ArgumentParser(
        description="生成家庭副业调研报告的七段式骨架（不含任何编造内容）"
    )
    parser.add_argument(
        "--out",
        default=".",
        help="输出目录或 .md 文件路径，目录不存在会自动创建（默认：当前目录）",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Top 推荐数量（默认：3）",
    )
    parser.add_argument(
        "--candidates",
        type=int,
        default=10,
        help="候选池条目数量（默认：10）",
    )
    args = parser.parse_args()

    if args.top < 1:
        print("❌ --top 必须 ≥ 1", file=sys.stderr)
        return 1
    if args.candidates < 1:
        print("❌ --candidates 必须 ≥ 1", file=sys.stderr)
        return 1

    target = resolve_output(args.out, "副业调研报告.md")
    target.parent.mkdir(parents=True, exist_ok=True)

    content = build_report(args.top, args.candidates)
    target.write_text(content, encoding="utf-8")

    print(f"✅ 报告骨架已生成：{target}")
    print(f"   文件大小：{target.stat().st_size / 1024:.1f} KB")
    print(f"   段落数：7（结论摘要 / 候选池 / 核验结果 / Top 推荐 / 说明书 / 待补项 / 免责声明）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
