# -*- coding: utf-8 -*-
"""
大乐透数据自动补全脚本（技能版，参数化路径）。

从中国体彩官网拉取最新开奖，补全 Excel 表格缺漏记录，并把最新数据固化进
分析工具 HTML 的内联数据块，实现网页数据与表格同步更新。

用法：
    python update_dlt_data.py [--workdir DIR] [--xlsx PATH] [--html PATH]

    --workdir  工作目录，默认取脚本所在目录。xlsx / html 未显式指定时，
               在该目录下寻找默认文件名（见下方 DEFAULTS）。
    --xlsx     历史开奖 Excel 路径，缺省为 <workdir>/大乐透历史开奖结果-2007年至当日更新.xlsx
    --html     分析工具 HTML 路径，缺省为 <workdir>/dlt-analyzer.html（技能 assets 副本）
               或 <workdir>/大乐透智能分析专家.html

依赖：openpyxl（pip install openpyxl）。仅用标准库联网，无需其他第三方包。
"""
import sys, io, os, re, time, json, shutil, urllib.request, argparse
from copy import copy

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

XLSX_DEFAULT = "大乐透历史开奖结果-2007年至当日更新.xlsx"
HTML_ALT = "大乐透智能分析专家.html"
HTML_SKILL = "dlt-analyzer.html"

API = ("https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
       "?gameNo=85&provinceId=0&pageSize=100&isVerify=1&pageNo={page}")


def log(msg):
    print(msg)


def fetch_official(page):
    req = urllib.request.Request(API.format(page=page), headers={
        "Referer": "https://www.lottery.gov.cn/", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize(rec):
    issue = str(rec.get("lotteryDrawNum", ""))
    if not re.fullmatch(r"\d{5}", issue):
        return None
    nums = [int(x) for x in str(rec.get("lotteryDrawResult", "")).split()]
    if len(nums) != 7:
        return None
    front = sorted(nums[:5])
    back = sorted(nums[5:])
    if not all(1 <= x <= 35 for x in front) or not all(1 <= x <= 12 for x in back):
        return None
    return {"issue": issue, "time": str(rec.get("lotteryDrawTime", ""))[:10],
            "front": front, "back": back}


def fetch_new(since_issue):
    """官网按期号降序返回；翻页收集 > since_issue 的全部记录（升序返回）。
    若本地最新期未出现在官网序列中，视为无法确认衔接，拒绝返回（防断档）。"""
    new = []
    seen_since = False
    page = 1
    done = False
    guard = 0
    while not done and guard < 30:
        guard += 1
        j = fetch_official(page)
        if not j.get("value") or not isinstance(j["value"].get("list"), list):
            raise RuntimeError("官网接口返回格式异常")
        lst = j["value"]["list"]
        any_hit = False
        for rec in lst:
            iss = str(rec.get("lotteryDrawNum", ""))
            if iss > since_issue:
                n = normalize(rec)
                if n:
                    new.append(n)
                any_hit = True
            else:
                if iss == since_issue:
                    seen_since = True
                done = True
                break
        if not any_hit or len(lst) < 100:
            break
        page += 1
        time.sleep(0.2)
    new.sort(key=lambda r: r["issue"])
    if new and not seen_since:
        raise RuntimeError("本地最新期 %s 未出现在官网开奖序列中，无法确认衔接，已中止（避免写入断档数据）。"
                           % since_issue)
    return new


def read_xlsx_rows(xlsx_path):
    from openpyxl import load_workbook
    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] is None:
            continue
        rows.append((int(r[0]), [int(x) for x in r[1:8]]))
    wb.close()
    return rows


def read_html_rows(html_path):
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    rows = re.findall(r'"(\d{5},\d{4}-\d{2}-\d{2},[\d,]+)"', html)
    out = []
    for s in rows:
        p = s.split(",")
        out.append({"issue": p[0], "time": p[1],
                    "front": [int(x) for x in p[2:7]], "back": [int(x) for x in p[7:9]]})
    return out, html


def resolve_html_path(workdir, html_arg):
    if html_arg:
        return html_arg
    for name in (HTML_SKILL, HTML_ALT):
        p = os.path.join(workdir, name)
        if os.path.exists(p):
            return p
    return os.path.join(workdir, HTML_SKILL)


def main():
    ap = argparse.ArgumentParser(description="大乐透历史开奖数据自动补全（官网拉取 → Excel + HTML 同步更新）")
    ap.add_argument("--workdir", default=os.path.dirname(os.path.abspath(__file__)),
                    help="工作目录，默认脚本所在目录")
    ap.add_argument("--xlsx", default=None, help="历史开奖 Excel 路径")
    ap.add_argument("--html", default=None, help="分析工具 HTML 路径")
    args = ap.parse_args()

    workdir = os.path.abspath(args.workdir)
    xlsx_path = os.path.abspath(args.xlsx) if args.xlsx else os.path.join(workdir, XLSX_DEFAULT)
    html_path = resolve_html_path(workdir, args.html)

    if not os.path.exists(xlsx_path) or not os.path.exists(html_path):
        log("未找到表格或 HTML。请确认：\n  Excel：%s\n  HTML ：%s\n"
            "可用 --xlsx / --html 显式指定路径。" % (xlsx_path, html_path))
        return 1

    xlsx_rows = read_xlsx_rows(xlsx_path)
    html_rows, html = read_html_rows(html_path)
    xlsx_map = {"%05d" % i: n for i, n in xlsx_rows}

    # 合并 HTML 中浏览器已补全的新记录
    merged = []
    seen = set()
    for r in html_rows:
        merged.append(r)
        seen.add(r["issue"])
    for iss in sorted(xlsx_map):
        if iss not in seen:
            nums = xlsx_map[iss]
            merged.append({"issue": iss, "time": "", "front": nums[:5], "back": nums[5:]})
            seen.add(iss)
    merged.sort(key=lambda r: r["issue"])

    last_issue = merged[-1]["issue"]
    log("当前数据：%d 期，截止第 %s 期" % (len(merged), last_issue))

    log("正在从中国体彩官网拉取最新开奖…")
    try:
        new = fetch_new(last_issue)
    except Exception as e:
        log("拉取失败：%s（请检查网络后重试）" % e)
        return 1

    if not new:
        log("已是最新：官网无新增开奖（大乐透每周一/三/六 21:25 开奖），截止第 %s 期。" % last_issue)
        return 0

    # 备份
    bak_dir = os.path.join(workdir, "_backup")
    os.makedirs(bak_dir, exist_ok=True)
    shutil.copy2(xlsx_path, os.path.join(bak_dir, "备份_%s.xlsx" % time.strftime("%Y%m%d_%H%M%S")))
    shutil.copy2(html_path, os.path.join(bak_dir, "备份_%s.html" % time.strftime("%Y%m%d_%H%M%S")))

    # 1) 追加写入 xlsx（含浏览器已补但表格还没有的记录）
    from openpyxl import load_workbook
    from openpyxl.styles import Font, Alignment, Border, Side
    wb = load_workbook(xlsx_path)
    ws = wb["Sheet1"]
    last_row_idx = ws.max_row
    last_cells = [ws.cell(last_row_idx, c) for c in range(1, 9)]
    tmpl_font = Font(name=last_cells[0].font.name or "宋体", size=last_cells[0].font.size or 11,
                     bold=True)
    tmpl_align = Alignment(horizontal="center", vertical="center")
    tmpl_border = Border(*[Side(style="thin", color="A6A6A6")] * 4)
    xlsx_issues = set("%05d" % i for i, _ in xlsx_rows)
    final_all = sorted(merged + new, key=lambda r: r["issue"])
    append = [r for r in final_all if r["issue"] not in xlsx_issues]
    append.sort(key=lambda r: r["issue"])
    for r in append:
        row = [int(r["issue"])] + r["front"] + r["back"]
        ridx = ws.max_row + 1
        for c, v in enumerate(row, start=1):
            cell = ws.cell(ridx, c)
            cell.value = v
            cell.font = copy(tmpl_font)
            cell.alignment = copy(tmpl_align)
            cell.border = copy(tmpl_border)
    wb.save(xlsx_path)
    log("表格已补全 %d 条记录（%s）" % (len(append), append[0]["issue"] + "~" + append[-1]["issue"]))

    # 2) 重写 HTML 内联数据（全部合并）
    lines = ["const DLT_RAW = ["]
    for r in final_all:
        nums = r["front"] + r["back"]
        lines.append('"%s,%s,%s",' % (r["issue"], r["time"] or "", ",".join(str(n) for n in nums)))
    lines[-1] = lines[-1].rstrip(",")
    lines.append("];")
    new_block = "\n".join(lines)
    html2, n = re.subn(r"const DLT_RAW = \[[\s\S]*?\];", new_block, html, count=1)
    if n != 1:
        log("HTML 内联数据块未找到，跳过 HTML 更新（表格已更新）。")
    else:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html2)
        log("HTML 数据已同步更新：共 %d 期，截止第 %s 期（%s）。" %
            (len(final_all), final_all[-1]["issue"], final_all[-1]["time"]))

    log("完成：新增期号 %s，刷新浏览器打开「%s」即可查看。" %
        ("、".join(r["issue"] for r in new), os.path.basename(html_path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
