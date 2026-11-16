#!/usr/bin/env node
'use strict';
/*
 * 短剧字幕校对工坊 - 无头命令行工具
 *
 * 复用已安装的短剧字幕校对工坊工程（Electron 应用）的 core 模块，
 * 提供命令行接口，输出结构化 JSON，供 WorkBuddy 智能体调用。
 *
 * 用法：
 *   node zimu.js probe "视频路径.mp4"
 *   node zimu.js run "视频路径.mp4" [--script 台词.txt] [--mode ocr|asr|fusion] [--projectDir ...] [--projectName ...]
 *   node zimu.js align --events events.json --script 台词.txt
 *   node zimu.js export-srt --events events.json --out 输出.srt
 *   node zimu.js export-report --events events.json --out 报告.txt
 *   node zimu.js export-csv --events events.json --out 事件表.csv
 *   node zimu.js burn "视频路径.mp4" --events events.json --out 带字幕.mp4 [--maskBottom 0.3] [--noMask]
 *
 * 工程定位：环境变量 ZIMU_HOME 优先，否则使用默认路径。
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

/* ---------- 工程定位 ---------- */
function findProjectRoot() {
  if (process.env.ZIMU_HOME) return path.resolve(process.env.ZIMU_HOME);
  const candidates = [
    'G:/doubaowork/短剧字幕校对工坊',
    path.join(process.env.USERPROFILE || '', '短剧字幕校对工坊'),
    'D:/短剧字幕校对工坊',
    'C:/Program Files (x86)/短剧字幕校对工坊'
  ];
  for (const c of candidates) {
    if (c && fs.existsSync(path.join(c, 'core', 'project.js'))) return c;
  }
  return null;
}

const PROJECT_ROOT = findProjectRoot();
if (!PROJECT_ROOT) {
  console.error(JSON.stringify({
    ok: false,
    error: '未找到短剧字幕校对工坊工程。请设置环境变量 ZIMU_HOME 指向工程根目录（含 core 模块目录）',
    hint: 'export ZIMU_HOME=/path/to/短剧字幕校对工坊'
  }));
  process.exit(2);
}

/* ---------- 加载工程 core 模块 ---------- */
const project = require(path.join(PROJECT_ROOT, 'core', 'project'));
const ffmpeg = require(path.join(PROJECT_ROOT, 'core', 'ffmpeg'));
const ocr = require(path.join(PROJECT_ROOT, 'core', 'ocr'));
const asr = require(path.join(PROJECT_ROOT, 'core', 'asr'));
const fusion = require(path.join(PROJECT_ROOT, 'core', 'fusion'));
const group = require(path.join(PROJECT_ROOT, 'core', 'group'));
const align = require(path.join(PROJECT_ROOT, 'core', 'align'));
const exporter = require(path.join(PROJECT_ROOT, 'core', 'exporter'));
const burn = require(path.join(PROJECT_ROOT, 'core', 'burn'));
const subtitleZone = require(path.join(PROJECT_ROOT, 'core', 'subtitle_zone'));

/* ---------- 工具函数 ---------- */
function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith('--')) {
        args[key] = true;
      } else {
        args[key] = next;
        i++;
      }
    } else {
      args._.push(a);
    }
  }
  return args;
}

function output(obj) {
  console.log(JSON.stringify(obj, null, 2));
}

function fail(msg, hint) {
  output({ ok: false, error: msg, hint: hint });
  process.exit(1);
}

/* ---------- 命令：probe ---------- */
async function cmdProbe(videoPath) {
  if (!videoPath) fail('缺少视频路径参数');
  if (!fs.existsSync(videoPath)) fail('视频文件不存在：' + videoPath);

  try {
    const probe = await ffmpeg.probeVideo(videoPath);
    const isPortrait = probe.width && probe.height && probe.width < probe.height;
    output({
      ok: true,
      duration: probe.duration,
      width: probe.width,
      height: probe.height,
      orientation: isPortrait ? 'portrait' : 'landscape',
      aspectRatio: probe.width + ':' + probe.height
    });
  } catch (e) {
    fail('探测视频失败：' + e.message);
  }
}

/* ---------- 命令：run（识别流水线） ---------- */
async function cmdRun(args) {
  const videoPath = args._[0];
  if (!videoPath) fail('缺少视频路径参数');
  if (!fs.existsSync(videoPath)) fail('视频文件不存在：' + videoPath);

  const mode = (args.mode || 'ocr').toLowerCase();
  if (!['ocr', 'asr', 'fusion'].includes(mode)) {
    fail('无效的识别模式：' + mode + '（支持：ocr/asr/fusion）');
  }

  // 创建项目目录
  let projectDir;
  if (args.projectDir) {
    projectDir = path.resolve(args.projectDir);
  } else {
    const name = args.projectName || path.basename(videoPath, path.extname(videoPath));
    projectDir = project.createProject(videoPath, name);
  }

  const logs = [];
  function log(msg) { logs.push(msg); process.stderr.write(msg + '\n'); }

  try {
    const probe = await ffmpeg.probeVideo(videoPath);
    log('视频信息：时长 ' + probe.duration + 's，' + probe.width + 'x' + probe.height);

    const useOcr = mode !== 'asr';
    const useAsr = mode !== 'ocr';
    let zone = null, strips = [], results = [], asrResult = null, events = null;

    if (useOcr) {
      const memWarn = ocr.checkFreeMemory();
      if (memWarn) log('⚠️ ' + memWarn);
      log('正在抽帧（每秒 1 帧，自动定位字幕区）…');
      const ex = await ffmpeg.extractFrames(videoPath, projectDir, (p) => {
        if (p.ratio !== undefined) log('抽帧进度：' + Math.round(p.ratio * 100) + '%');
      });
      zone = ex.zone || null;
      if (zone) log('字幕区检测：y0=' + zone.y0.toFixed(3) + ', y1=' + zone.y1.toFixed(3));
      strips = fs.readdirSync(path.join(projectDir, 'strips')).filter(f => /\.png$/i.test(f)).sort();
      log('字幕条数量：' + strips.length);
      log('正在识别字幕文字（0/' + strips.length + '）');

      // 在独立子进程中执行 OCR（wasm 内存随子进程退出归还）
      results = await runOcrInChild(
        strips.map(f => path.join(projectDir, 'strips', f)),
        (done, total) => log('正在识别字幕文字（' + done + '/' + total + '）')
      );
    }

    if (useAsr) {
      log('正在提取音频并转写…');
      asrResult = await asr.transcribe(videoPath, projectDir, (p) => {
        log('正在转写音频（' + p.done + '/' + p.total + '）');
      });
      log('ASR转写行数：' + (asrResult ? asrResult.lines.length : 0));
    }

    if (mode === 'asr') {
      events = (asrResult ? asrResult.lines : []).map(l => ({
        start: l.start, end: l.end, frameIndex: null,
        text: l.text, asrText: l.text, frameText: '', source: 'asr'
      }));
    } else if (mode === 'fusion') {
      log('正在融合双通道…');
      events = fusion.build(asrResult, results, (probe && probe.duration) || 0);
    } else {
      events = group.groupEvents(results);
    }

    if (zone) {
      try {
        fs.writeFileSync(path.join(projectDir, 'zone.json'), JSON.stringify(zone), 'utf8');
      } catch (e) {}
    }

    // 保存字幕事件
    const eventsPayload = { events, mode, probe, zone, createdAt: new Date().toISOString() };
    fs.writeFileSync(path.join(projectDir, 'events.json'), JSON.stringify(eventsPayload, null, 2), 'utf8');

    output({
      ok: true,
      projectDir: projectDir,
      mode: mode,
      probe: probe,
      zone: zone,
      stripCount: strips.length,
      frameCount: results.length,
      asrCount: asrResult ? asrResult.lines.length : 0,
      eventCount: events.length,
      events: events,
      logs: logs
    });
  } catch (e) {
    fail('识别流水线失败：' + (e.message || e), '检查视频路径、工程路径和系统内存');
  }
}

/* OCR 子进程执行（复用 main.js 的 runOcrInChild 模式） */
function runOcrInChild(strips, onProgress) {
  const { fork } = require('child_process');
  const child = fork(path.join(PROJECT_ROOT, 'core', 'ocr_worker.js'), [], {
    stdio: 'inherit',
    windowsHide: true,
    env: Object.assign({}, process.env, { ELECTRON_RUN_AS_NODE: '1' })
  });
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (fn, v) => { if (!settled) { settled = true; fn(v); } };
    child.on('message', m => {
      if (!m) return;
      if (m.type === 'progress') onProgress(m.done, m.total);
      else if (m.type === 'done') { finish(resolve, m.results); child.disconnect(); }
      else if (m.type === 'error') { finish(reject, new Error(m.message || 'OCR 子进程错误')); child.disconnect(); }
    });
    child.on('exit', code => {
      finish(code === 0 ? resolve : reject, code === 0 ? undefined : new Error('OCR 子进程异常退出，代码 ' + code));
    });
    child.on('error', e => finish(reject, e));
    child.send({ strips });
  });
}

/* ---------- 命令：align（比对） ---------- */
async function cmdAlign(args) {
  const eventsPath = args.events;
  if (!eventsPath) fail('缺少 --events 参数（字幕事件文件路径）');
  if (!fs.existsSync(eventsPath)) fail('字幕事件文件不存在：' + eventsPath);

  const scriptPath = args.script;
  if (!scriptPath) fail('缺少 --script 参数（台词原文文件路径）');
  if (!fs.existsSync(scriptPath)) fail('台词原文文件不存在：' + scriptPath);

  try {
    // 加载字幕事件
    const raw = fs.readFileSync(eventsPath, 'utf8');
    const payload = JSON.parse(raw);
    const events = payload.events || payload;

    // 解析台词原文
    const scriptData = align.parseScriptFile(scriptPath);

    // 执行比对
    const result = align.align(events, scriptData.items);

    output({
      ok: true,
      totalEvents: result.totalEvents,
      totalScript: result.totalScript,
      rows: result.rows,
      missing: result.missing,
      extra: result.extra
    });
  } catch (e) {
    fail('比对失败：' + (e.message || e));
  }
}

/* ---------- 命令：export-srt ---------- */
async function cmdExportSrt(args) {
  const eventsPath = args.events;
  if (!eventsPath) fail('缺少 --events 参数');
  if (!fs.existsSync(eventsPath)) fail('字幕事件文件不存在：' + eventsPath);
  if (!args.out) fail('缺少 --out 参数（输出文件路径）');

  try {
    const raw = fs.readFileSync(eventsPath, 'utf8');
    const payload = JSON.parse(raw);
    // 如果是比对结果（含 rows），用 rows；否则用 events
    const rows = payload.rows || payload.events || payload;
    const result = exporter.exportSrt(rows, args.out);
    output({ ok: true, count: result.count, outPath: result.outPath });
  } catch (e) {
    fail('导出SRT失败：' + (e.message || e));
  }
}

/* ---------- 命令：export-report ---------- */
async function cmdExportReport(args) {
  const eventsPath = args.events;
  if (!eventsPath) fail('缺少 --events 参数');
  if (!fs.existsSync(eventsPath)) fail('字幕事件文件不存在：' + eventsPath);
  if (!args.out) fail('缺少 --out 参数（输出文件路径）');

  try {
    const raw = fs.readFileSync(eventsPath, 'utf8');
    const payload = JSON.parse(raw);
    const rows = payload.rows || [];
    const missing = payload.missing || [];
    const extra = payload.extra || [];
    const result = exporter.exportReport(rows, missing, extra, args.out);
    output({ ok: true, diffs: result.diffs, missing: result.missing, extra: result.extra, outPath: result.outPath });
  } catch (e) {
    fail('导出报告失败：' + (e.message || e));
  }
}

/* ---------- 命令：export-csv ---------- */
async function cmdExportCsv(args) {
  const eventsPath = args.events;
  if (!eventsPath) fail('缺少 --events 参数');
  if (!fs.existsSync(eventsPath)) fail('字幕事件文件不存在：' + eventsPath);
  if (!args.out) fail('缺少 --out 参数（输出文件路径）');

  try {
    const raw = fs.readFileSync(eventsPath, 'utf8');
    const payload = JSON.parse(raw);
    const rows = payload.rows || payload.events || payload;
    const result = exporter.exportCsv(rows, args.out);
    output({ ok: true, count: result.count, outPath: result.outPath });
  } catch (e) {
    fail('导出CSV失败：' + (e.message || e));
  }
}

/* ---------- 命令：burn（烧录字幕视频） ---------- */
async function cmdBurn(args) {
  const videoPath = args._[0];
  if (!videoPath) fail('缺少视频路径参数');
  if (!fs.existsSync(videoPath)) fail('视频文件不存在：' + videoPath);

  const eventsPath = args.events;
  if (!eventsPath) fail('缺少 --events 参数（字幕事件文件路径）');
  if (!fs.existsSync(eventsPath)) fail('字幕事件文件不存在：' + eventsPath);

  if (!args.out) fail('缺少 --out 参数（输出文件路径）');

  try {
    const raw = fs.readFileSync(eventsPath, 'utf8');
    const payload = JSON.parse(raw);
    const rows = payload.rows || payload.events || payload;

    // 探测视频
    const probe = await ffmpeg.probeVideo(videoPath);

    // 获取字幕区（zone.json 或现场检测）
    let zone = null;
    const projectDir = args.projectDir || path.dirname(eventsPath);
    if (fs.existsSync(path.join(projectDir, 'zone.json'))) {
      try { zone = JSON.parse(fs.readFileSync(path.join(projectDir, 'zone.json'), 'utf8')); } catch (e) {}
    }
    if (!zone) {
      process.stderr.write('未找到 zone.json，现场检测字幕区…\n');
      try { zone = await subtitleZone.detectZone(videoPath); } catch (e) {}
    }

    // 遮罩策略
    let maskBottom = +args.maskBottom || 0;
    if (args.noMask) maskBottom = 0;
    if (!zone && maskBottom > 0 && probe.width && probe.height && probe.width < probe.height) {
      maskBottom = 0.3; // 竖屏无字幕带检测时加大底部遮盖
    }

    // 生成 ASS
    const assPath = path.join(os.tmpdir(), 'zimu_burn_' + Date.now() + '.ass');
    burn.generateAss(rows, probe.width, probe.height, assPath, zone || null);

    // 烧录
    process.stderr.write('正在烧录字幕…\n');
    const opts = { maskBottom: maskBottom };
    if (zone && zone.y0 != null && zone.y1 != null && zone.y1 > zone.y0) opts.zone = zone;

    await burn.burnSubtitles(videoPath, assPath, args.out, probe.duration, opts, (ratio) => {
      process.stderr.write('烧录进度：' + Math.round(ratio * 100) + '%\n');
    });

    try { fs.unlinkSync(assPath); } catch (e) {}

    output({ ok: true, outPath: args.out, duration: probe.duration, zone: zone });
  } catch (e) {
    fail('烧录失败：' + (e.message || e));
  }
}

/* ---------- 主入口 ---------- */
const command = process.argv[2];
const args = parseArgs(process.argv.slice(3));

const commands = {
  probe: cmdProbe,
  run: cmdRun,
  align: cmdAlign,
  'export-srt': cmdExportSrt,
  'export-report': cmdExportReport,
  'export-csv': cmdExportCsv,
  burn: cmdBurn
};

if (!command || !commands[command]) {
  console.error(JSON.stringify({
    ok: false,
    error: '未知命令：' + (command || '(空)'),
    usage: '用法：node zimu.js <命令> [参数]\n' +
      '命令：\n' +
      '  probe <视频路径>                      探测视频信息\n' +
      '  run <视频路径> [--script 台词] [--mode ocr|asr|fusion]  识别字幕流水线\n' +
      '  align --events events.json --script 台词.txt           比对字幕与原文\n' +
      '  export-srt --events events.json --out 输出.srt         导出SRT\n' +
      '  export-report --events events.json --out 报告.txt       导出校对报告\n' +
      '  export-csv --events events.json --out 事件表.csv        导出CSV事件表\n' +
      '  burn <视频路径> --events events.json --out 带字幕.mp4  烧录字幕视频'
  }));
  process.exit(1);
}

commands[command](args).catch(e => fail(e.message || String(e)));
