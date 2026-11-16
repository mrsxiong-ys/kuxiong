#!/usr/bin/env node
'use strict';
/*
 * 漫画工坊 - 无头命令行工具
 *
 * 复用已安装的漫画工坊工程（Electron 应用）的 core 模块，
 * 提供命令行接口，输出结构化 JSON，供 WorkBuddy 智能体调用。
 *
 * 用法：
 *   node mhgf.js resolve "https://mangadex.org/chapter/{id}"
 *   node mhgf.js run "https://mangadex.org/title/{id}" [--chapters 1-5] [--no-pdf] [--no-cbz]
 *   node mhgf.js translate --input 台词.json --baseURL ... --apiKey ... --model ...
 *   node mhgf.js ocr --input page.jpg --lang eng [--langPath ...] [--corePath ...]
 *   node mhgf.js pack --input dir/ --pdf --cbz
 *
 * 工程定位：环境变量 MHGF_HOME 优先，否则使用默认路径。
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

/* ---------- 工程定位 ---------- */
function findProjectRoot() {
  if (process.env.MHGF_HOME) return path.resolve(process.env.MHGF_HOME);
  // 常见默认路径
  const candidates = [
    path.join(process.env.USERPROFILE || '', '漫画工坊'),
    'D:/漫画工坊'
  ];
  for (const c of candidates) {
    if (c && fs.existsSync(path.join(c, 'core', 'pipeline.js'))) return c;
  }
  return null;
}

const PROJECT_ROOT = findProjectRoot();
if (!PROJECT_ROOT) {
  console.error(JSON.stringify({
    ok: false,
    error: '未找到漫画工坊工程。请设置环境变量 MHGF_HOME 指向工程根目录（含核心流水线模块）',
    hint: 'export MHGF_HOME=/path/to/manhua-gongfang'
  }));
  process.exit(2);
}

/* ---------- 加载工程 core 模块 ---------- */
const dl = require(path.join(PROJECT_ROOT, 'core', 'downloader.js'));
const ocrMod = require(path.join(PROJECT_ROOT, 'core', 'ocr.js'));
const translator = require(path.join(PROJECT_ROOT, 'core', 'translator.js'));
const composer = require(path.join(PROJECT_ROOT, 'core', 'composer.js'));
const pipeline = require(path.join(PROJECT_ROOT, 'core', 'pipeline.js'));

/* ---------- 工具函数 ---------- */
function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next !== undefined && !next.startsWith('--')) {
        args[key] = next;
        i++;
      } else {
        args[key] = true;
      }
    } else {
      args._.push(a);
    }
  }
  return args;
}

function out(obj) { console.log(JSON.stringify(obj, null, 2)); }
function err(msg, code = 1) {
  console.error(JSON.stringify({ ok: false, error: msg }));
  process.exit(code);
}

/* ---------- 子命令：resolve ---------- */
async function cmdResolve(args) {
  const url = args._[0] || args.url;
  if (!url) return err('用法：mhgf.js resolve "<url>"');
  try {
    const md = dl.parseMangaDexUrl(url);
    if (md && md.kind === 'manga') {
      const info = await dl.mdMangaInfo(md.id, {});
      const chapters = await dl.mdMangaChapters(md.id, {});
      return out({
        ok: true,
        kind: 'manga',
        id: md.id,
        title: info.title,
        alt: info.alt,
        coverUrl: info.coverUrl,
        chapterCount: chapters.length,
        chapters: chapters.slice(0, 50).map(c => ({
          id: c.id, chapter: c.chapter, title: c.title,
          pages: c.pages, lang: c.lang
        }))
      });
    }
    if (md && md.kind === 'chapter') {
      const info = await dl.mdChapterInfo(md.id, {});
      const pp = await dl.mdChapterPages(md.id, {});
      return out({
        ok: true,
        kind: 'chapter',
        id: md.id,
        title: info.mangaTitle || '漫画章节',
        label: '第' + (info.chapter || '?') + '话' + (info.title ? ' - ' + info.title : ''),
        pages: pp.fileList.length,
        lang: info.lang
      });
    }
    if (md && md.kind === 'unknown') {
      return err('无法识别该 MangaDex 链接（请用章节或作品页面链接）');
    }
    // 通用网页
    return out({ ok: true, kind: 'generic', url, title: new URL(url).hostname.replace(/^www\./, '') });
  } catch (e) {
    return err('解析失败：' + (e.message || e));
  }
}

/* ---------- 子命令：run ---------- */
async function cmdRun(args) {
  const url = args._[0] || args.url;
  if (!url) return err('用法：mhgf.js run "<url>" [--chapters 1-5]');
  const mediaRoot = args.mediaRoot || path.join(process.env.USERPROFILE || '', '漫画工坊');
  fs.mkdirSync(mediaRoot, { recursive: true });

  // 简化任务对象
  const job = {
    id: 'job_' + Date.now().toString(36),
    status: 'working',
    stage: '',
    current: 0, total: 0,
    logs: [],
    steps: [],
    cancelled: false
  };
  const addLog = (m) => { job.logs.push(m); console.log('[log] ' + m); };

  // 解析章节选择
  let chapterIds = [];
  if (args.chapters) {
    chapterIds = String(args.chapters).split(',').map(s => s.trim()).filter(Boolean);
  }

  const settings = {
    editManual: false,
    aiRedraw: args.aiRedraw !== 'false',
    pdf: args.pdf !== 'false',
    cbz: args.cbz !== 'false',
    compress: true,
    translate: true,
    keepOriginal: true
  };

  try {
    addLog('任务已创建：' + url);
    const result = await pipeline.runPipeline(job, {
      url,
      chapterIds,
      mediaRoot,
      settings,
      proxy: args.proxy || '',
      model: {},
      imageModel: {},
      res: {
        langPath: path.join(PROJECT_ROOT, 'data', 'ocr'),
        corePath: '',
        fontPath: path.join(PROJECT_ROOT, 'data', 'fonts', 'LXGWWenKai-Regular.ttf'),
        fontFamily: 'LXGW WenKai, Noto Sans SC, sans-serif',
        ocrCachePath: path.join(mediaRoot, '.ocr-cache')
      }
    });
    out({
      ok: true,
      jobId: job.id,
      status: job.status,
      title: result && result.title,
      outputs: (result && result.outputs) || [],
      logs: job.logs
    });
  } catch (e) {
    out({ ok: false, jobId: job.id, status: 'error', error: e.message || String(e), logs: job.logs });
    process.exit(1);
  }
}

/* ---------- 子命令：translate ---------- */
async function cmdTranslate(args) {
  const inputPath = args.input || args._[1];
  if (!inputPath) return err('用法：mhgf.js translate --input 台词.json --baseURL ... --apiKey ... --model ...');
  const texts = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  if (!Array.isArray(texts)) return err('输入文件必须是 JSON 数组');

  try {
    const result = await translator.translateTexts(texts, {
      baseURL: args.baseURL,
      apiKey: args.apiKey,
      modelName: args.model || args.modelName,
      proxy: args.proxy || ''
    });
    // 保存到输出文件
    const outPath = args.output || path.join(path.dirname(inputPath), 'translated.json');
    fs.writeFileSync(outPath, JSON.stringify(result, null, 2), 'utf8');
    out({ ok: true, count: result.length, output: outPath, translations: result });
  } catch (e) {
    return err('翻译失败：' + (e.message || e));
  }
}

/* ---------- 子命令：ocr ---------- */
async function cmdOcr(args) {
  const inputPath = args.input;
  if (!inputPath) return err('用法：mhgf.js ocr --input page.jpg --lang eng');
  const lang = args.lang || 'eng';
  const buf = fs.readFileSync(inputPath);

  try {
    const boxes = await ocrMod.ocrPage(buf, {
      lang,
      langPath: args.langPath || path.join(PROJECT_ROOT, 'data', 'ocr'),
      corePath: args.corePath || '',
      workDir: path.dirname(inputPath)
    });
    out({ ok: true, lang, count: boxes.length, boxes });
  } catch (e) {
    return err('OCR 失败：' + (e.message || e));
  }
}

/* ---------- 子命令：pack ---------- */
async function cmdPack(args) {
  const inputDir = args.input;
  if (!inputDir) return err('用法：mhgf.js pack --input dir/ --pdf --cbz');
  if (!fs.statSync(inputDir).isDirectory()) return err('输入路径不是目录');

  // 收集图片
  const imgs = fs.readdirSync(inputDir)
    .filter(f => /\.(jpg|jpeg|png|webp)$/i.test(f))
    .sort();
  if (!imgs.length) return err('目录中没有图片文件');

  const paths = imgs.map(f => path.join(inputDir, f));
  const outDir = args.output || inputDir;
  const outputs = {};

  if (args.pdf) {
    const pdfPath = path.join(outDir, path.basename(inputDir) + '.pdf');
    await composer.makePdf(paths, pdfPath);
    outputs.pdf = pdfPath;
  }
  if (args.cbz) {
    const cbzPath = path.join(outDir, path.basename(inputDir) + '.cbz');
    await composer.makeCbz(paths, cbzPath);
    outputs.cbz = cbzPath;
  }
  out({ ok: true, pages: paths.length, outputs });
}

/* ---------- 入口 ---------- */
async function main() {
  const argv = process.argv.slice(2);
  if (!argv.length) {
    return err('漫画工坊无头工具。子命令：resolve | run | translate | ocr | pack');
  }
  const [cmd, ...rest] = argv;
  const args = parseArgs(rest);

  switch (cmd) {
    case 'resolve': return cmdResolve(args);
    case 'run': return cmdRun(args);
    case 'translate': return cmdTranslate(args);
    case 'ocr': return cmdOcr(args);
    case 'pack': return cmdPack(args);
    case '--help':
    case '-h':
      console.log(`漫画工坊无头工具
子命令：
  resolve "<url>"            解析漫画网址
  run "<url>" [--chapters]   启动流水线
  translate --input ...      批量翻译台词
  ocr --input ...            OCR 识别图片文字
  pack --input dir/          合成 PDF/CBZ
环境变量：
  MHGF_HOME                  漫画工坊工程根目录（默认自动查找）`);
      return;
    default:
      return err('未知命令：' + cmd + '。使用 --help 查看帮助');
  }
}

main().catch(e => {
  out({ ok: false, error: e.message || String(e), stack: e.stack });
  process.exit(1);
});
