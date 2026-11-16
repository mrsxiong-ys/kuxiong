# -*- coding: utf-8 -*-
"""
双色球历史数据合并工具（技能版，参数化路径）。

把外部补充的历史开奖数据（Excel）合并进双色球工作台，与现有数据去重、
防断档，并同步更新 Excel 表格与分析页面 HTML 的内联数据。

用法：
    python merge_history.py [补充数据.xlsx] [--workdir DIR] [--xlsx PATH] [--html PATH]

    --workdir  工作目录，默认取脚本所在目录。
    --xlsx     历史开奖 Excel 路径，缺省为 <workdir>/双色球历史开奖结果-2007年至当日更新.xlsx
    --html     分析工具 HTML 路径，缺省为 <workdir>/ssq-analyzer.html 或 双色球智能分析专家.html
    位置参数    补充数据 Excel 路径，缺省为默认下载路径。

补充数据 Excel 表头须为：期号,开奖日期,红球1,红球2,红球3,红球4,红球5,红球6,蓝球
- 以现有工作台数据为准，重叠期号取现有数据（若补充数据与之不一致会如实报告差异）。
"""
import sys, io, os, re, shutil, argparse
from copy import copy
from datetime import datetime, date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

XLSX_DEFAULT = "双色球历史开奖结果-2007年至当日更新.xlsx"
HTML_ALT = "双色球智能分析专家.html"
HTML_SKILL = "ssq-analyzer.html"
DEFAULT_SRC = "双色球历史开奖数据2007-2013.xlsx"

FRONT_N = 33
BACK_N = 16
FRONT_SEL = 6
BACK_SEL = 1


def log(msg):
    print(msg)


def fmt_date(v):
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    if v is None:
        return ""
    return str(v)[:10]


def load_src(path):
    """读取补充数据 Excel，返回 [{issue,time,front,back}]，升序。"""
    from openpyxl import load_workbook
    if not os.path.exists(path):
        log("补充数据文件不存在：%s" % path)
        return []
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] is None:
            continue
        issue = str(r[0])
        if not re.fullmatch(r"\d{7}", issue):
            log("  跳过非法期号行：%r" % (r,))
            continue
        red = r[2:8]
        blue = r[8]
        try:
            front = [int(x) for x in red]
            back = [int(blue)]
        except (ValueError, TypeError):
            log("  跳过号码非法行（期号 %s）：%r" % (issue, r))
            continue
        front.sort()
        if not (len(front) == FRONT_SEL and all(1 <= x <= FRONT_N for x in front)):
            log("  跳过红球非法行（期号 %s）：%r" % (issue, r))
            continue
        if not (len(back) == BACK_SEL and 1 <= back[0] <= BACK_N):
            log("  跳过蓝球非法行（期号 %s）：%r" % (issue, r))
            continue
        rows.append({"issue": issue, "time": fmt_date(r[1]), "front": front, "back": back})
    wb.close()
    rows.sort(key=lambda x: x["issue"])
    return rows


def load_existing(xlsx_path):
    """读取现有工作台 Excel，返回 [{issue,time,front,back}]。"""
    from openpyxl import load_workbook
    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] is None:
            continue
        issue = str(r[0])
        nums = [int(x) for x in r[2:9]]
        rows.append({"issue": issue, "time": fmt_date(r[1]),
                     "front": nums[:6], "back": nums[6:]})
    wb.close()
    return rows


def write_xlsx(xlsx_path, rows):
    """以 9 列（期号,日期,红球1-6,蓝球）重写 Excel。"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    headers = ["期号", "日期", "红球1", "红球2", "红球3", "红球4", "红球5", "红球6", "蓝球"]
    head_font = Font(name="宋体", size=11, bold=True)
    tmpl_font = Font(name="宋体", size=11)
    tmpl_align = Alignment(horizontal="center", vertical="center")
    tmpl_border = Border(*[Side(style="thin", color="A6A6A6")] * 4)
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(1, c)
        cell.value = h
        cell.font = head_font
        cell.alignment = copy(tmpl_align)
        cell.border = copy(tmpl_border)
    for r in rows:
        row = [int(r["issue"]), r["time"] or ""] + r["front"] + r["back"]
        ridx = ws.max_row + 1
        for c, v in enumerate(row, start=1):
            cell = ws.cell(ridx, c)
            cell.value = v
            cell.font = copy(tmpl_font)
            cell.alignment = copy(tmpl_align)
            cell.border = copy(tmpl_border)
    wb.save(xlsx_path)


def write_html(html_path, rows):
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    lines = ["const SSQ_RAW = ["]
    for r in rows:
        nums = r["front"] + r["back"]
        lines.append('"%s,%s,%s",' % (r["issue"], r["time"] or "", ",".join(str(n) for n in nums)))
    lines[-1] = lines[-1].rstrip(",")
    lines.append("];")
    new_block = "\n".join(lines)
    html2, n = re.subn(r"const SSQ_RAW = \[[\s\S]*?\];", new_block, html, count=1)
    if n != 1:
        log("HTML 内联数据块未找到，跳过 HTML 更新。")
        return False
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html2)
    return True


def check_gaps(rows):
    """按年份分组检查年内期号序号是否连续，返回断档列表。"""
    from collections import defaultdict
    by_year = defaultdict(list)
    for r in rows:
        by_year[r["issue"][:4]].append(int(r["issue"][4:]))
    gaps = []
    for y in sorted(by_year):
        ns = sorted(by_year[y])
        for i in range(len(ns) - 1):
            if ns[i + 1] - ns[i] != 1:
                gaps.append((y + str(ns[i]).zfill(3), y + str(ns[i + 1]).zfill(3), ns[i + 1] - ns[i] - 1))
    return gaps


def main():
    ap = argparse.ArgumentParser(description="双色球历史数据合并（补充数据 → Excel + HTML 同步更新）")
    ap.add_argument("src", nargs="?", default=DEFAULT_SRC, help="补充数据 Excel 路径")
    ap.add_argument("--workdir", default=os.path.dirname(os.path.abspath(__file__)),
                    help="工作目录，默认脚本所在目录")
    ap.add_argument("--xlsx", default=None, help="历史开奖 Excel 路径")
    ap.add_argument("--html", default=None, help="分析工具 HTML 路径")
    args = ap.parse_args()

    workdir = os.path.abspath(args.workdir)
    xlsx_path = os.path.abspath(args.xlsx) if args.xlsx else os.path.join(workdir, XLSX_DEFAULT)
    if args.html:
        html_path = os.path.abspath(args.html)
    else:
        html_path = None
        for name in (HTML_SKILL, HTML_ALT):
            p = os.path.join(workdir, name)
            if os.path.exists(p):
                html_path = p
                break
        if html_path is None:
            html_path = os.path.join(workdir, HTML_SKILL)

    if not os.path.exists(xlsx_path):
        log("未找到现有工作台 Excel：%s" % xlsx_path)
        return 1

    src_rows = load_src(args.src)
    if not src_rows:
        log("未从补充数据中读取到任何合法记录，请检查文件格式。")
        return 1
    log("补充数据：%d 期（%s ~ %s）" %
        (len(src_rows), src_rows[0]["issue"], src_rows[-1]["issue"]))

    exist_rows = load_existing(xlsx_path)
    log("现有数据：%d 期（%s ~ %s）" %
        (len(exist_rows), exist_rows[0]["issue"], exist_rows[-1]["issue"]))

    # 合并：以现有数据为准，补充数据填补缺失期号
    exist_map = {r["issue"]: r for r in exist_rows}
    src_map = {r["issue"]: r for r in src_rows}
    merged = list(exist_rows)
    added = []
    conflicts = []
    for iss in sorted(src_map):
        if iss in exist_map:
            a, b = exist_map[iss], src_map[iss]
            if a["front"] != b["front"] or a["back"] != b["back"]:
                conflicts.append(iss)
        else:
            merged.append(src_map[iss])
            added.append(src_map[iss])
    merged.sort(key=lambda r: r["issue"])

    log("补充新记录：%d 期" % len(added))
    if conflicts:
        log("⚠️ 重叠期号存在号码冲突（以现有工作台数据为准，未采用补充数据）：%d 期" % len(conflicts))
        log("  冲突期号示例：%s" % "、".join(conflicts[:10]))
    else:
        log("重叠期号号码完全一致，无需取舍。")

    # 备份
    bak_dir = os.path.join(workdir, "_backup")
    os.makedirs(bak_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(xlsx_path, os.path.join(bak_dir, "备份_合并_%s.xlsx" % ts))
    if os.path.exists(html_path):
        shutil.copy2(html_path, os.path.join(bak_dir, "备份_合并_%s.html" % ts))

    # 防断档检查
    gaps = check_gaps(merged)
    if gaps:
        log("⚠️ 期号存在断档：%d 处（正常，早期数据可能不全）" % len(gaps))
        for g in gaps[:5]:
            log("  %s -> %s（缺 %d 期）" % (g[0], g[1], g[2]))
    else:
        log("期号连续，无断档。")

    # 写入
    write_xlsx(xlsx_path, merged)
    log("Excel 已更新：共 %d 期（%s ~ %s）" %
        (len(merged), merged[0]["issue"], merged[-1]["issue"]))
    if os.path.exists(html_path) and write_html(html_path, merged):
        log("HTML 内联数据已同步：共 %d 期。" % len(merged))
    log("完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
